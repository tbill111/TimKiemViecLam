from __future__ import annotations

import datetime as dt
import os
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ai.scorers import score_pair
from app.ai.types import ModelNotAvailable
from app.deps import CurrentUser, get_db, get_optional_user, require_role
from app.models import APP_STATUSES, JOB_TYPES, LEVELS, WORK_MODES, Job, JobSkill, Location, Skill
from app.services.ai_repo import SqlAIRepository
from app.services.jobs import job_dto, job_input, job_skill_map, refresh_embedding
from app.services.skills import SkillResolver

router = APIRouter(tags=["jobs"])

CATEGORIES = (
    "Frontend Development", "Backend Development", "Data Science & Analytics", "Business Analysis", "QA & Testing",
    "UI/UX Design", "IT Support", "Digital Marketing", "Software Engineering", "Business Operations",
)
# Nhãn kinh nghiệm của frontend → khoảng min_years_exp [lo, hi)
EXPERIENCE_RANGES = {
    "Chưa có kinh nghiệm": (0, 0.0001),
    "Dưới 1 năm": (0.0001, 1),
    "1-2 năm": (1, 2),
    "2-3 năm": (2, 3),
    "3+ năm": (3, 99),
}
WORK_TYPE_FILTER = {"Toàn thời gian": "full_time", "Bán thời gian": "part_time", "Thực tập": "internship"}


class JobIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    responsibilities: list[str] = []
    category: Literal[CATEGORIES] = "Software Engineering"  # type: ignore[valid-type]
    level: Literal[LEVELS] = "fresher"  # type: ignore[valid-type]
    job_type: Literal[JOB_TYPES] = "full_time"  # type: ignore[valid-type]
    work_mode: Literal[WORK_MODES] = "onsite"  # type: ignore[valid-type]
    location: str = Field(min_length=1, max_length=100)
    salary_min: Optional[float] = Field(default=None, ge=0)
    salary_max: Optional[float] = Field(default=None, ge=0)
    min_years_exp: float = Field(default=0, ge=0, le=30)
    min_education: int = Field(default=0, ge=0, le=4)
    deadline: Optional[dt.datetime] = None
    required_skills: list[str] = []
    preferred_skills: list[str] = []


def _default_model() -> str:
    return os.getenv("DEFAULT_MODEL", "m3")


def _match_for(db: Session, user: CurrentUser, jobs: list[Job], model: str) -> dict[int, dict[str, Any]]:
    """Điểm khớp của ứng viên đang đăng nhập với danh sách tin; rỗng nếu chưa có hồ sơ."""
    repo = SqlAIRepository(db)
    cand = repo.candidate_input_for_user(user.id)
    if cand is None:
        return {}
    skills = job_skill_map(db, [j.id for j in jobs])
    out: dict[int, dict[str, Any]] = {}
    for j in jobs:
        try:
            out[j.id] = score_pair(model, cand, job_input(j, *skills[j.id]))
        except ModelNotAvailable:
            out[j.id] = score_pair("m3", cand, job_input(j, *skills[j.id]))
    return out


def _location(db: Session, name: str) -> Location:
    loc = db.scalar(select(Location).where(Location.name == name))
    if loc is None:
        loc = Location(name=name, region="")
        db.add(loc)
        db.flush()
    return loc


def _apply_skills(db: Session, job: Job, required: list[str], preferred: list[str]) -> tuple[list[str], list[str]]:
    resolver = SkillResolver(db)
    unknown = [n for n in required + preferred if resolver.resolve(n) is None]
    if unknown:
        raise HTTPException(422, detail={"detail": "unknown_skills", "skills": unknown})
    req = resolver.resolve_many(required)
    req_ids = {s.id for s in req}
    pref = [s for s in resolver.resolve_many(preferred) if s.id not in req_ids]
    db.execute(delete(JobSkill).where(JobSkill.job_id == job.id))
    db.add_all([JobSkill(job_id=job.id, skill_id=s.id, is_required=True) for s in req])
    db.add_all([JobSkill(job_id=job.id, skill_id=s.id, is_required=False) for s in pref])
    return [s.name for s in req], [s.name for s in pref]


def _fill(job: Job, body: JobIn, db: Session) -> None:
    if body.salary_min is not None and body.salary_max is not None and body.salary_min > body.salary_max:
        raise HTTPException(422, detail="salary_min_greater_than_max")
    job.title, job.description, job.responsibilities = body.title.strip(), body.description, body.responsibilities
    job.category, job.level, job.job_type, job.work_mode = body.category, body.level, body.job_type, body.work_mode
    job.location_id = _location(db, body.location.strip()).id
    job.salary_min, job.salary_max = body.salary_min, body.salary_max
    job.min_years_exp, job.min_education, job.deadline = body.min_years_exp, body.min_education, body.deadline


@router.get("/jobs")
def list_jobs(
    q: str = "",
    location: str = "",
    work_type: str = "",
    experience: str = "",
    category: str = "",
    sort: Literal["relevance", "newest"] = "relevance",
    model: Optional[str] = None,
    mine: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    user: Optional[CurrentUser] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    stmt = select(Job).order_by(Job.posted_at.desc(), Job.id.desc())
    if mine:
        if user is None or user.role not in ("recruiter", "admin"):
            raise HTTPException(403, detail="forbidden")
        if user.role == "recruiter":
            stmt = stmt.where(Job.company_id == user.company_id)
    else:
        stmt = stmt.where(Job.status == "open")
    if category:
        stmt = stmt.where(Job.category == category)
    if location and location != "Tất cả":
        stmt = stmt.join(Location, Location.id == Job.location_id).where(Location.name == location)
    if work_type == "Remote":
        stmt = stmt.where(Job.work_mode == "remote")
    elif work_type in WORK_TYPE_FILTER:
        stmt = stmt.where(Job.job_type == WORK_TYPE_FILTER[work_type], Job.work_mode != "remote")
    if experience in EXPERIENCE_RANGES:
        lo, hi = EXPERIENCE_RANGES[experience]
        stmt = stmt.where(Job.min_years_exp >= lo, Job.min_years_exp < hi)
    jobs = list(db.scalars(stmt).unique())
    skills = job_skill_map(db, [j.id for j in jobs])
    if q.strip():
        needle = q.lower().strip()
        jobs = [
            j for j in jobs
            if needle in " ".join([j.title, j.company.name, j.location.name if j.location else "", j.category, *skills[j.id][0], *skills[j.id][1]]).lower()
        ]
    matches = _match_for(db, user, jobs, (model or _default_model()).lower()) if user and user.role == "candidate" else {}
    if sort == "relevance" and matches:
        jobs.sort(key=lambda j: matches[j.id]["total_score"], reverse=True)
    total = len(jobs)
    page_jobs = jobs[(page - 1) * page_size : page * page_size]
    items = []
    for j in page_jobs:
        dto = job_dto(j, *skills[j.id])
        if j.id in matches:
            dto["match"] = matches[j.id]
        items.append(dto)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/jobs/{job_id}")
def get_job(job_id: int, user: Optional[CurrentUser] = Depends(get_optional_user), db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, detail="job_not_found")
    dto = job_dto(job, *job_skill_map(db, [job.id])[job.id])
    if user and user.role == "candidate":
        m = _match_for(db, user, [job], _default_model())
        if job.id in m:
            dto["match"] = m[job.id]
    return dto


def _own_job(db: Session, user: CurrentUser, job_id: int) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, detail="job_not_found")
    if user.role != "admin" and job.company_id != user.company_id:
        raise HTTPException(403, detail="not_your_job")
    return job


@router.post("/jobs", status_code=201)
def create_job(body: JobIn, user: CurrentUser = Depends(require_role("recruiter")), db: Session = Depends(get_db)):
    from app.models import Recruiter

    recruiter_id = db.scalar(select(Recruiter.id).where(Recruiter.user_id == user.id))
    job = Job(company_id=user.company_id, recruiter_id=recruiter_id, status="open", posted_at=dt.datetime.now(dt.timezone.utc).replace(tzinfo=None))
    _fill(job, body, db)
    db.add(job)
    db.flush()
    req, pref = _apply_skills(db, job, body.required_skills, body.preferred_skills)
    refresh_embedding(job, req, pref)
    db.commit()
    db.refresh(job)
    return job_dto(job, req, pref)


@router.put("/jobs/{job_id}")
def update_job(job_id: int, body: JobIn, user: CurrentUser = Depends(require_role("recruiter", "admin")), db: Session = Depends(get_db)):
    job = _own_job(db, user, job_id)
    _fill(job, body, db)
    req, pref = _apply_skills(db, job, body.required_skills, body.preferred_skills)
    refresh_embedding(job, req, pref)
    db.commit()
    db.refresh(job)
    return job_dto(job, req, pref)


@router.delete("/jobs/{job_id}", status_code=204)
def close_job(job_id: int, user: CurrentUser = Depends(require_role("recruiter", "admin")), db: Session = Depends(get_db)):
    """Đóng tin (không xoá để giữ lịch sử ứng tuyển và số liệu BI)."""
    _own_job(db, user, job_id).status = "closed"
    db.commit()


@router.get("/locations")
def list_locations(db: Session = Depends(get_db)):
    return {"items": [{"id": loc.id, "name": loc.name, "region": loc.region} for loc in db.scalars(select(Location).order_by(Location.name))]}


@router.get("/skills")
def list_skills(db: Session = Depends(get_db)):
    return {"items": [{"id": s.id, "name": s.name, "category": s.category} for s in db.scalars(select(Skill).order_by(Skill.category, Skill.name))]}


__all__ = ["router", "APP_STATUSES"]
