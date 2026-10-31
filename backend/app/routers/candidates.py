from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.deps import CurrentUser, get_db, require_role
from app.models import (
    Application,
    ApplicationStatusHistory,
    Candidate,
    CandidateSkill,
    Location,
    MatchResult,
    Resume,
    SavedJob,
    Skill,
    User,
)
from app.services.ai_repo import refresh_candidate_embedding
from app.services.skills import SkillResolver

router = APIRouter(prefix="/candidates/me", tags=["candidates"])


class ProfileIn(BaseModel):
    """Đúng tên trường (camelCase) của StudentProfile ở frontend, cộng `consent`."""

    model_config = ConfigDict(extra="ignore")

    fullName: Optional[str] = Field(default=None, max_length=255)
    university: Optional[str] = None
    major: Optional[str] = None
    year: Optional[str] = None
    phone: Optional[str] = None
    githubUrl: Optional[str] = None
    linkedinUrl: Optional[str] = None
    careerGoal: Optional[str] = None
    skills: Optional[list[str]] = None
    preferredLocations: Optional[list[str]] = None
    preferredWorkTypes: Optional[list[str]] = None
    languages: Optional[list[str]] = None
    projects: Optional[list[dict[str, Any]]] = None
    experience: Optional[list[dict[str, Any]]] = None
    certificates: Optional[list[dict[str, Any]]] = None
    consent: Optional[bool] = None


class SkillsIn(BaseModel):
    skills: list[str]


_PROFILE_KEYS = ("university", "year", "githubUrl", "linkedinUrl", "careerGoal", "preferredLocations", "preferredWorkTypes",
                 "languages", "projects", "experience", "certificates")


def get_candidate(db: Session, user: CurrentUser) -> Candidate:
    cand = db.scalar(select(Candidate).where(Candidate.user_id == user.id))
    if cand is None:
        raise HTTPException(404, detail="candidate_profile_not_found")
    return cand


def confirmed_skill_names(db: Session, cand: Candidate) -> list[str]:
    return list(
        db.scalars(
            select(Skill.name)
            .join(CandidateSkill, CandidateSkill.skill_id == Skill.id)
            .where(CandidateSkill.candidate_id == cand.id, CandidateSkill.confirmed.is_(True))
            .order_by(Skill.id)
        )
    )


def completion(p: dict[str, Any]) -> int:
    """Cùng 12 tiêu chí với calculateProfileCompletion ở frontend."""
    checks = [
        bool(p.get("fullName", "").strip()), bool(p.get("university", "").strip()), bool(p.get("major", "").strip()),
        bool(p.get("year", "").strip()), bool(p.get("email", "").strip()), bool(p.get("careerGoal", "").strip()),
        len(p.get("skills", [])) >= 3, len(p.get("languages", [])) >= 1, len(p.get("projects", [])) >= 1,
        len(p.get("experience", [])) >= 1, len(p.get("certificates", [])) >= 1, bool((p.get("phone") or "").strip()),
    ]
    return round(sum(checks) / len(checks) * 100)


def profile_out(db: Session, cand: Candidate) -> dict[str, Any]:
    stored = cand.profile_json or {}
    out: dict[str, Any] = {
        "fullName": cand.full_name,
        "university": stored.get("university", ""),
        "major": cand.major,
        "year": stored.get("year", ""),
        "email": cand.user.email,
        "phone": cand.phone,
        "githubUrl": stored.get("githubUrl", ""),
        "linkedinUrl": stored.get("linkedinUrl", ""),
        "careerGoal": stored.get("careerGoal", ""),
        "skills": confirmed_skill_names(db, cand),
        "preferredLocations": stored.get("preferredLocations", []),
        "preferredWorkTypes": stored.get("preferredWorkTypes", []),
        "languages": stored.get("languages", []),
        "projects": stored.get("projects", []),
        "experience": stored.get("experience", []),
        "certificates": stored.get("certificates", []),
    }
    out["profileCompletion"] = completion(out)
    out["consent"] = cand.consent_at is not None
    return out


def _set_skills(db: Session, cand: Candidate, names: list[str]) -> list[str]:
    """Thay toàn bộ kỹ năng bằng danh sách đã xác nhận. Trả về các tên không có trong danh mục."""
    resolver = SkillResolver(db)
    wanted = {s.id: s for s in resolver.resolve_many(names)}
    unresolved = [n for n in names if resolver.resolve(n) is None]
    existing = {cs.skill_id: cs for cs in db.scalars(select(CandidateSkill).where(CandidateSkill.candidate_id == cand.id))}
    for sid, row in existing.items():
        if sid not in wanted:
            db.delete(row)
    for sid in wanted:
        if sid in existing:
            existing[sid].confirmed = True
        else:
            db.add(CandidateSkill(candidate_id=cand.id, skill_id=sid, source="manual", confirmed=True))
    return unresolved


@router.get("")
def get_profile(user: CurrentUser = Depends(require_role("candidate")), db: Session = Depends(get_db)):
    return profile_out(db, get_candidate(db, user))


@router.put("")
def put_profile(body: ProfileIn, user: CurrentUser = Depends(require_role("candidate")), db: Session = Depends(get_db)):
    cand = get_candidate(db, user)
    data = body.model_dump(exclude_none=True)
    if "fullName" in data:
        cand.full_name = data["fullName"]
        cand.user.full_name = data["fullName"]
    if "major" in data:
        cand.major = data["major"]
    if "phone" in data:
        cand.phone = data["phone"]
    stored = dict(cand.profile_json or {})
    for key in _PROFILE_KEYS:
        if key in data:
            stored[key] = data[key]
    cand.profile_json = stored
    if data.get("preferredLocations"):
        name = data["preferredLocations"][0]
        loc = db.scalar(select(Location).where(Location.name == name)) or Location(name=name, region="")
        db.add(loc)
        db.flush()
        cand.location_id = loc.id
    if data.get("consent") and cand.consent_at is None:
        cand.consent_at = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    if "skills" in data:
        _set_skills(db, cand, data["skills"])
    db.flush()
    refresh_candidate_embedding(db, cand)
    db.commit()
    db.refresh(cand)
    return profile_out(db, cand)


@router.get("/skills")
def get_skills(user: CurrentUser = Depends(require_role("candidate")), db: Session = Depends(get_db)):
    cand = get_candidate(db, user)
    rows = db.execute(
        select(Skill.name, CandidateSkill.source, CandidateSkill.confirmed)
        .join(CandidateSkill, CandidateSkill.skill_id == Skill.id)
        .where(CandidateSkill.candidate_id == cand.id)
        .order_by(Skill.id)
    ).all()
    return {"skills": [{"name": n, "source": s, "confirmed": c} for n, s, c in rows]}


@router.put("/skills")
def put_skills(body: SkillsIn, user: CurrentUser = Depends(require_role("candidate")), db: Session = Depends(get_db)):
    """Xác nhận/sửa kỹ năng: danh sách gửi lên là toàn bộ kỹ năng đã xác nhận."""
    cand = get_candidate(db, user)
    unresolved = _set_skills(db, cand, body.skills)
    db.flush()
    refresh_candidate_embedding(db, cand)
    db.commit()
    return {"skills": confirmed_skill_names(db, cand), "unresolved": unresolved}


@router.delete("", status_code=204)
def delete_profile(user: CurrentUser = Depends(require_role("candidate")), db: Session = Depends(get_db)):
    """Xoá hồ sơ và mọi dữ liệu liên quan (quyền xoá dữ liệu cá nhân)."""
    cand = get_candidate(db, user)
    app_ids = list(db.scalars(select(Application.id).where(Application.candidate_id == cand.id)))
    if app_ids:
        db.execute(delete(ApplicationStatusHistory).where(ApplicationStatusHistory.application_id.in_(app_ids)))
    for model in (Application, SavedJob, MatchResult, Resume, CandidateSkill):
        db.execute(delete(model).where(model.candidate_id == cand.id))
    db.delete(cand)
    db.flush()
    db.delete(db.get(User, user.id))
    db.commit()
