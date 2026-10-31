"""Việc đã lưu (ứng viên) và quản trị danh mục kỹ năng (admin)."""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import CurrentUser, get_db, require_role
from app.models import Candidate, Job, SavedJob, Skill, SkillAlias
from app.services.jobs import job_dto, job_skill_map

saved_router = APIRouter(tags=["saved-jobs"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])


def _cand_id(db: Session, user: CurrentUser) -> int:
    cid = db.scalar(select(Candidate.id).where(Candidate.user_id == user.id))
    if cid is None:
        raise HTTPException(404, detail="candidate_profile_not_found")
    return cid


@saved_router.get("/saved-jobs")
def list_saved(user: CurrentUser = Depends(require_role("candidate")), db: Session = Depends(get_db)):
    cid = _cand_id(db, user)
    rows = db.execute(select(SavedJob, Job).join(Job, Job.id == SavedJob.job_id).where(SavedJob.candidate_id == cid).order_by(SavedJob.saved_at.desc())).all()
    skills = job_skill_map(db, [j.id for _, j in rows])
    return {"items": [{"job_id": s.job_id, "saved_at": s.saved_at.isoformat(), "job": job_dto(j, *skills[j.id])} for s, j in rows]}


@saved_router.post("/saved-jobs/{job_id}", status_code=201)
def save_job(job_id: int, user: CurrentUser = Depends(require_role("candidate")), db: Session = Depends(get_db)):
    cid = _cand_id(db, user)
    if db.get(Job, job_id) is None:
        raise HTTPException(404, detail="job_not_found")
    existing = db.get(SavedJob, (cid, job_id))
    if existing is None:
        existing = SavedJob(candidate_id=cid, job_id=job_id, saved_at=dt.datetime.now(dt.timezone.utc).replace(tzinfo=None))
        db.add(existing)
        db.commit()
    return {"job_id": job_id, "saved_at": existing.saved_at.isoformat()}


@saved_router.delete("/saved-jobs/{job_id}", status_code=204)
def unsave_job(job_id: int, user: CurrentUser = Depends(require_role("candidate")), db: Session = Depends(get_db)):
    row = db.get(SavedJob, (_cand_id(db, user), job_id))
    if row is not None:
        db.delete(row)
        db.commit()


class SkillIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: str = ""
    learning_steps: list[str] | None = None


class SkillUpdate(BaseModel):
    category: str | None = None
    learning_steps: list[str] | None = None


class AliasIn(BaseModel):
    alias: str = Field(min_length=1, max_length=100)
    skill_name: str


@admin_router.get("/skills")
def admin_skills(user: CurrentUser = Depends(require_role("admin")), db: Session = Depends(get_db)):
    return {"items": [{"id": s.id, "name": s.name, "category": s.category, "learning_steps": s.learning_steps or []} for s in db.scalars(select(Skill).order_by(Skill.id))]}


@admin_router.post("/skills", status_code=201)
def admin_add_skill(body: SkillIn, user: CurrentUser = Depends(require_role("admin")), db: Session = Depends(get_db)):
    if db.scalar(select(Skill.id).where(Skill.name == body.name.strip())):
        raise HTTPException(409, detail="skill_exists")
    skill = Skill(name=body.name.strip(), category=body.category, learning_steps=body.learning_steps)
    db.add(skill)
    db.commit()
    return {"id": skill.id, "name": skill.name, "category": skill.category}


@admin_router.put("/skills/{skill_id}")
def admin_update_skill(skill_id: int, body: SkillUpdate, user: CurrentUser = Depends(require_role("admin")), db: Session = Depends(get_db)):
    """Sửa nhóm và lộ trình học của kỹ năng (tên chuẩn không đổi để không làm lệch dữ liệu đã gắn)."""
    skill = db.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(404, detail="skill_not_found")
    if body.category is not None:
        skill.category = body.category
    if body.learning_steps is not None:
        skill.learning_steps = [x.strip() for x in body.learning_steps if x.strip()] or None
    db.commit()
    return {"id": skill.id, "name": skill.name, "category": skill.category, "learning_steps": skill.learning_steps or []}


@admin_router.delete("/skill-aliases/{alias}", status_code=204)
def admin_delete_alias(alias: str, user: CurrentUser = Depends(require_role("admin")), db: Session = Depends(get_db)):
    row = db.get(SkillAlias, alias.strip().lower())
    if row is None:
        raise HTTPException(404, detail="alias_not_found")
    db.delete(row)
    db.commit()


@admin_router.get("/skill-aliases")
def admin_aliases(user: CurrentUser = Depends(require_role("admin")), db: Session = Depends(get_db)):
    rows = db.execute(select(SkillAlias.alias, Skill.name).join(Skill, Skill.id == SkillAlias.skill_id).order_by(SkillAlias.alias)).all()
    return {"items": [{"alias": a, "skill_name": n} for a, n in rows]}


@admin_router.post("/skill-aliases", status_code=201)
def admin_add_alias(body: AliasIn, user: CurrentUser = Depends(require_role("admin")), db: Session = Depends(get_db)):
    skill = db.scalar(select(Skill).where(Skill.name == body.skill_name))
    if skill is None:
        raise HTTPException(404, detail="skill_not_found")
    alias = body.alias.strip().lower()
    if db.get(SkillAlias, alias) is not None:
        raise HTTPException(409, detail="alias_exists")
    db.add(SkillAlias(alias=alias, skill_id=skill.id))
    db.commit()
    return {"alias": alias, "skill_name": skill.name}
