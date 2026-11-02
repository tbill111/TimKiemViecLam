"""Candidate profile and confirmed-skill endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.deps import CurrentUser, get_db, require_role
from app.models import Candidate, CandidateSkill, Location, Resume, Skill, SkillAlias, User

router = APIRouter(prefix="/candidates", tags=["candidates"])


def _candidate(db: Session, user_id: int) -> Candidate:
    row = db.scalar(select(Candidate).where(Candidate.user_id == user_id))
    if row is None:
        raise HTTPException(404, detail="candidate_profile_not_found")
    return row


def _embed_candidate(candidate: Candidate, skills: list[str] | None = None):
    try:
        from app.ai.embedder import embed_text, to_bytes

        profile = candidate.profile_json or {}
        detail_text = " ".join(
            [str(item.get("description", "")) for key in ("projects", "experience", "certificates")
             for item in profile.get(key, []) if isinstance(item, dict)]
        )
        text = " ".join([str(profile.get("careerGoal") or ""), " ".join(skills or []), str(profile.get("major") or ""), detail_text])
        candidate.embedding = to_bytes(embed_text(text[:3000]))
    except Exception:
        candidate.embedding = None


def _replace_skills(db: Session, candidate: Candidate, names: list[str]):
    skills = {s.name.casefold(): s for s in db.scalars(select(Skill).where(Skill.is_active.is_(True)))}
    aliases = {a.alias.casefold(): a.skill_id for a in db.scalars(select(SkillAlias))}
    resolved: dict[int, str] = {}
    unresolved = []
    for name in names:
        item = skills.get(name.strip().casefold())
        skill_id = item.id if item else aliases.get(name.strip().casefold())
        if skill_id:
            resolved[skill_id] = name
        else:
            unresolved.append(name)
    existing = {s.skill_id: s for s in db.scalars(select(CandidateSkill).where(CandidateSkill.candidate_id == candidate.id))}
    for skill_id, row in existing.items():
        if skill_id not in resolved:
            db.delete(row)
    for skill_id in resolved:
        if skill_id in existing:
            existing[skill_id].confirmed = True
        else:
            db.add(CandidateSkill(candidate_id=candidate.id, skill_id=skill_id, source="manual", confirmed=True))
    canonical = list(db.scalars(select(Skill.name).where(Skill.id.in_(resolved)))) if resolved else []
    _embed_candidate(candidate, canonical)
    return canonical, unresolved


@router.get("/me")
def get_me(db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("candidate"))):
    row = _candidate(db, user.id)
    return {**(row.profile_json or {}), "fullName": row.full_name, "major": row.major, "university": row.university,
            "skills": list(db.scalars(select(Skill.name).join(CandidateSkill, CandidateSkill.skill_id == Skill.id).where(CandidateSkill.candidate_id == row.id, CandidateSkill.confirmed.is_(True)))),
            "consent": row.consent_at is not None, "years_exp": row.years_exp, "education_level": row.education_level}


@router.put("/me")
def update_me(body: dict[str, Any], db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("candidate"))):
    row = _candidate(db, user.id)
    consent = bool(body.pop("consent", False))
    if consent:
        row.consent_at = row.consent_at or datetime.utcnow()
    profile = {k: v for k, v in body.items() if k not in {"years_exp", "education_level", "location_id", "expected_salary_min", "expected_salary_max"}}
    row.profile_json = profile
    row.full_name = str(body.get("fullName") or row.full_name)
    row.university = str(body.get("university") or "")
    row.major = str(body.get("major") or "")
    if body.get("years_exp") is not None:
        row.years_exp = max(0, float(body["years_exp"]))
    elif isinstance(body.get("experience"), list) and body["experience"]:
        try:
            from app.ai.parser import extract_years_exp
            history = "\n".join(str(item.get("duration", "")) for item in body["experience"] if isinstance(item, dict))
            row.years_exp = extract_years_exp(history, {"experience": history})
        except Exception:
            pass
    if body.get("education_level") is not None:
        row.education_level = min(4, max(0, int(body["education_level"])))
    elif body.get("university"):
        row.education_level = 3
    if body.get("location_id") is not None:
        row.location_id = int(body["location_id"])
    elif isinstance(body.get("preferredLocations"), list) and body["preferredLocations"]:
        selected = str(body["preferredLocations"][0])
        location = db.scalar(select(Location).where(func.lower(Location.name) == selected.lower()))
        if location is None:
            location = Location(name=selected, region="Remote" if selected.lower() == "remote" else None)
            db.add(location)
            db.flush()
        row.location_id = location.id
    for col in ("expected_salary_min", "expected_salary_max"):
        if col in body:
            setattr(row, col, body[col])
    if row.expected_salary_min is not None and row.expected_salary_max is not None and row.expected_salary_min > row.expected_salary_max:
        raise HTTPException(422, detail="invalid_salary_range")
    unresolved = []
    if isinstance(body.get("skills"), list):
        _, unresolved = _replace_skills(db, row, body["skills"])
    else:
        confirmed = list(db.scalars(select(Skill.name).join(CandidateSkill, CandidateSkill.skill_id == Skill.id).where(CandidateSkill.candidate_id == row.id, CandidateSkill.confirmed.is_(True))))
        _embed_candidate(row, confirmed)
    db.commit()
    return {**profile, "consent": row.consent_at is not None, "unresolved": unresolved}


@router.get("/me/skills")
def get_skills(db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("candidate"))):
    row = _candidate(db, user.id)
    items = db.execute(select(Skill.name, CandidateSkill.source, CandidateSkill.confirmed)
        .join(CandidateSkill, CandidateSkill.skill_id == Skill.id).where(CandidateSkill.candidate_id == row.id).order_by(Skill.name)).all()
    return {"skills": [{"name": n, "source": source, "confirmed": confirmed} for n, source, confirmed in items]}


@router.put("/me/skills")
def set_skills(body: dict[str, list[str]], db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("candidate"))):
    names = body.get("skills")
    if not isinstance(names, list) or any(not isinstance(name, str) for name in names):
        raise HTTPException(422, detail="skills_must_be_string_array")
    candidate = _candidate(db, user.id)
    canonical_names, unresolved = _replace_skills(db, candidate, names)
    db.commit()
    return {"skills": canonical_names, "unresolved": unresolved}


@router.delete("/me", status_code=204)
def delete_me(db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("candidate"))):
    account = db.get(User, user.id)
    if account is not None:
        db.delete(account)
    db.commit()
    return None
