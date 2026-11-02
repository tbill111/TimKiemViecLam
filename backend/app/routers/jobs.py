"""Job search and recruiter job management endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.ai.types import CandidateInput
from app.deps import CurrentUser, get_db, get_optional_user, require_role
from app.models import Company, Job, JobSkill, Location, Skill
from app.services.ai_repo import SqlAIRepository

router = APIRouter(tags=["jobs"])


def _skillsets(db: Session, job_id: int):
    rows = db.execute(select(Skill.name, JobSkill.priority).join(JobSkill, JobSkill.skill_id == Skill.id).where(JobSkill.job_id == job_id)).all()
    return [name for name, p in rows if p == "required"], [name for name, p in rows if p == "preferred"]


def _dto(db: Session, job: Job, match=None):
    company = db.get(Company, job.company_id)
    loc = db.get(Location, job.location_id) if job.location_id else None
    required, preferred = _skillsets(db, job.id)
    value = {
        "id": str(job.id), "title": job.title, "company": {"id": company.id, "name": company.name, "size": company.size_range, "industry": company.industry} if company else None,
        "location": loc.name if loc else "", "job_type": job.job_type, "work_mode": job.work_mode,
        "min_years_exp": job.min_years_exp, "salary_min": float(job.salary_min) if job.salary_min is not None else None,
        "salary_max": float(job.salary_max) if job.salary_max is not None else None, "category": job.category,
        "responsibilities": job.responsibilities or [], "description": job.description,
        "required_skills": required, "preferred_skills": preferred, "level": job.level, "status": job.status,
        "posted_at": job.posted_at.isoformat() + ("Z" if job.posted_at.tzinfo is None else ""),
        "deadline": job.deadline.isoformat() if job.deadline else None,
    }
    if match is not None:
        value["match"] = match
    return value


def _candidate_match(db: Session, user: CurrentUser | None):
    if user is None or user.role != "candidate":
        return None
    repo = SqlAIRepository(db)
    return repo.candidate_input_for_user(user.id)


def _add_skills(db: Session, job: Job, required_names: list[str], preferred_names: list[str]):
    # Composite legacy labels are split into two preferred skills by contract.
    normalized_preferred = list(preferred_names)
    normalized_required = []
    for name in required_names:
        if " hoặc " in name.lower():
            normalized_preferred.extend(part.strip() for part in name.split(" hoặc ") if part.strip())
        else:
            normalized_required.append(name)
    skills = {s.name.casefold(): s for s in db.scalars(select(Skill).where(Skill.is_active.is_(True)))}
    for name, priority in [(n, "required") for n in normalized_required] + [(n, "preferred") for n in normalized_preferred]:
        skill = skills.get(name.strip().casefold())
        if skill is None:
            raise HTTPException(422, detail={"unknown_skill": name})
        db.add(JobSkill(job_id=job.id, skill_id=skill.id, priority=priority))


def _embedding(job: Job, body: dict[str, Any] | None = None):
    body = body or {}
    text = " ".join([job.title, job.description, " ".join(job.responsibilities or []), " ".join(body.get("required_skills", [])), " ".join(body.get("preferred_skills", []))])
    try:
        from app.ai.embedder import embed_text, to_bytes
        job.embedding = to_bytes(embed_text(text[:3000]))
    except Exception:
        job.embedding = None


def _location_id(db: Session, name: str) -> int:
    loc = db.scalar(select(Location).where(func.lower(Location.name) == name.strip().lower()))
    if loc is None:
        loc = Location(name=name.strip(), region="Remote" if name.strip().lower() == "remote" else None)
        db.add(loc)
        db.flush()
    return loc.id


def _validate_job_body(body: dict[str, Any]):
    required = ["title", "category", "level", "job_type", "work_mode", "location"]
    missing = [k for k in required if not body.get(k)]
    if missing:
        raise HTTPException(422, detail={"missing_fields": missing})
    if body.get("salary_min") is not None and body.get("salary_max") is not None and float(body["salary_min"]) > float(body["salary_max"]):
        raise HTTPException(422, detail="invalid_salary_range")
    if body["level"] not in {"intern", "fresher", "junior", "middle", "senior"}:
        raise HTTPException(422, detail="invalid_level")
    if body["job_type"] not in {"full_time", "part_time", "internship"} or body["work_mode"] not in {"onsite", "hybrid", "remote"}:
        raise HTTPException(422, detail="invalid_work_type")


def _write_job(db: Session, job: Job, body: dict[str, Any]):
    _validate_job_body(body)
    for col in ("title", "category", "level", "job_type", "work_mode", "description"):
        setattr(job, col, str(body.get(col) or ""))
    job.location_id = _location_id(db, str(body["location"]))
    job.responsibilities = body.get("responsibilities") or []
    job.min_years_exp = float(body.get("min_years_exp", 0))
    job.min_education = int(body.get("min_education", 0))
    job.salary_min = body.get("salary_min")
    job.salary_max = body.get("salary_max")
    if body.get("deadline"):
        job.deadline = datetime.fromisoformat(str(body["deadline"]).replace("Z", "+00:00")).replace(tzinfo=None)
    if "status" in body and body["status"] not in {"open", "closed"}:
        raise HTTPException(422, detail="invalid_status")
    if body.get("status"):
        job.status = body["status"]
    _embedding(job, body)


@router.get("/jobs")
def list_jobs(q: str | None = None, location: str | None = None, work_type: str | None = None,
              experience: str | None = None, category: str | None = None, sort: str = "newest",
              mine: bool = False, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
              db: Session = Depends(get_db), user: CurrentUser | None = Depends(get_optional_user)):
    if mine and (user is None or user.role != "recruiter"):
        raise HTTPException(403, detail="recruiter_only")
    if sort not in {"relevance", "newest"}:
        raise HTTPException(422, detail="invalid_sort")
    query = select(Job)
    if not mine:
        query = query.where(Job.status == "open")
    if mine and user is not None:
        query = query.where(Job.company_id == user.company_id)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.join(Company, Company.id == Job.company_id).where(or_(Job.title.ilike(pattern), Job.description.ilike(pattern), Company.name.ilike(pattern)))
    if location:
        query = query.join(Location, Location.id == Job.location_id).where(Location.name.ilike(f"%{location.strip()}%"))
    if category:
        query = query.where(Job.category == category)
    if work_type:
        if work_type.lower() == "remote":
            query = query.where(Job.work_mode == "remote")
        else:
            type_map = {"toàn thời gian": "full_time", "bán thời gian": "part_time", "thực tập": "internship"}
            query = query.where(Job.job_type == type_map.get(work_type.lower(), work_type))
    exp_map = {"Chưa có kinh nghiệm": (0, 0.01), "Dưới 1 năm": (0, 1), "1-2 năm": (1, 2), "2-3 năm": (2, 3), "3+ năm": (3, None)}
    if experience in exp_map:
        low, high = exp_map[experience]
        query = query.where(Job.min_years_exp >= low)
        if high is not None:
            query = query.where(Job.min_years_exp < high)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    candidate = _candidate_match(db, user)
    repo = SqlAIRepository(db)
    ordered = query.order_by(Job.posted_at.desc(), Job.id.desc())
    if sort == "relevance" and candidate is not None:
        jobs = list(db.scalars(ordered))
    else:
        jobs = list(db.scalars(ordered.offset((page - 1) * page_size).limit(page_size)))
    items = []
    for row in jobs:
        match = None
        if candidate is not None:
            job_input = repo.job_input(row.id)
            if job_input is not None:
                try:
                    from app.ai.scorers import score_pair
                    match = score_pair("m3", candidate, job_input)
                except Exception:
                    match = None
        items.append(_dto(db, row, match))
    if sort == "relevance" and candidate is not None:
        items.sort(key=lambda item: (-(item["match"] or {}).get("total_score", -1), item["id"]))
        items = items[(page - 1) * page_size:page * page_size]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, detail="job_not_found")
    return _dto(db, job)


@router.post("/jobs", status_code=201)
def create_job(body: dict[str, Any], db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("recruiter"))):
    if user.company_id is None:
        raise HTTPException(403, detail="recruiter_company_required")
    job = Job(company_id=user.company_id, recruiter_id=user.id, external_id=None)
    _write_job(db, job, body)
    db.add(job)
    db.flush()
    _add_skills(db, job, body.get("required_skills", []), body.get("preferred_skills", []))
    db.commit()
    db.refresh(job)
    from app.services.ai_index import fit_open_job_corpus
    fit_open_job_corpus(db, force=True)
    return _dto(db, job)


@router.put("/jobs")
def update_job(body: dict[str, Any], db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("recruiter"))):
    if not body.get("id"):
        raise HTTPException(422, detail="id_required")
    return _update_job(int(body["id"]), body, db, user)


@router.put("/jobs/{job_id}")
def update_job_path(job_id: int, body: dict[str, Any], db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("recruiter"))):
    return _update_job(job_id, body, db, user)


def _update_job(job_id: int, body: dict[str, Any], db: Session, user: CurrentUser):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, detail="job_not_found")
    if job.company_id != user.company_id:
        raise HTTPException(403, detail="not_your_job")
    _write_job(db, job, body)
    db.execute(JobSkill.__table__.delete().where(JobSkill.job_id == job.id))
    _add_skills(db, job, body.get("required_skills", []), body.get("preferred_skills", []))
    db.commit()
    db.refresh(job)
    from app.services.ai_index import fit_open_job_corpus
    fit_open_job_corpus(db, force=True)
    return _dto(db, job)


@router.delete("/jobs/{job_id}", status_code=204)
def close_job(job_id: int, db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("recruiter"))):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, detail="job_not_found")
    if job.company_id != user.company_id:
        raise HTTPException(403, detail="not_your_job")
    job.status = "closed"
    db.commit()
    from app.services.ai_index import fit_open_job_corpus
    fit_open_job_corpus(db, force=True)


@router.delete("/jobs", status_code=204)
def close_job_query(job_id: int, db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("recruiter"))):
    close_job(job_id, db, user)


@router.get("/locations")
def locations(db: Session = Depends(get_db)):
    return {"items": [{"id": row.id, "name": row.name, "region": row.region} for row in db.scalars(select(Location).order_by(Location.name))]}


@router.get("/skills")
def skills(db: Session = Depends(get_db)):
    return {"items": [{"id": row.id, "name": row.name, "category": row.category} for row in db.scalars(select(Skill).where(Skill.is_active.is_(True)).order_by(Skill.name))]}
