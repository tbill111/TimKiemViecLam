"""Skill catalogue administration endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.deps import CurrentUser, get_db, require_role
from app.models import Skill, SkillAlias

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/skills")
def list_skills(db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("admin"))):
    return {"items": [{"id": s.id, "name": s.name, "category": s.category, "learning_steps": s.learning_steps or []} for s in db.scalars(select(Skill).where(Skill.is_active.is_(True)).order_by(Skill.name))]}


@router.post("/skills", status_code=201)
def create_skill(body: dict, db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("admin"))):
    name = str(body.get("name", "")).strip()
    if not name:
        raise HTTPException(422, detail="name_required")
    if db.scalar(select(Skill.id).where(func.lower(Skill.name) == name.lower())):
        raise HTTPException(409, detail="skill_exists")
    row = Skill(name=name, category=str(body.get("category") or "Khác"), learning_steps=body.get("learning_steps") or [])
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "name": row.name, "category": row.category, "learning_steps": row.learning_steps}


@router.put("/skills/{skill_id}")
def update_skill(skill_id: int, body: dict, db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("admin"))):
    row = db.get(Skill, skill_id)
    if row is None:
        raise HTTPException(404, detail="skill_not_found")
    if "category" in body:
        row.category = str(body["category"])
    if "learning_steps" in body:
        row.learning_steps = [str(v) for v in body["learning_steps"]]
    db.commit()
    return {"id": row.id, "name": row.name, "category": row.category, "learning_steps": row.learning_steps}


@router.get("/skill-aliases")
def list_aliases(db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("admin"))):
    rows = db.execute(select(SkillAlias, Skill).join(Skill, Skill.id == SkillAlias.skill_id).order_by(SkillAlias.alias))
    return {"items": [{"alias": alias.alias, "skill_id": skill.id, "skill_name": skill.name} for alias, skill in rows]}


@router.post("/skill-aliases", status_code=201)
def create_alias(body: dict, db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("admin"))):
    alias = str(body.get("alias", "")).strip()
    name = str(body.get("skill_name", "")).strip()
    if not alias or not name:
        raise HTTPException(422, detail="alias_and_skill_name_required")
    if db.scalar(select(SkillAlias.id).where(func.lower(SkillAlias.alias) == alias.lower())):
        raise HTTPException(409, detail="alias_exists")
    skill = db.scalar(select(Skill).where(func.lower(Skill.name) == name.lower()))
    if skill is None:
        raise HTTPException(404, detail="skill_not_found")
    row = SkillAlias(alias=alias, skill_id=skill.id)
    db.add(row)
    db.commit()
    return {"alias": row.alias, "skill_name": skill.name}


@router.delete("/skill-aliases/{alias}", status_code=204)
def delete_alias(alias: str, db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("admin"))):
    row = db.scalar(select(SkillAlias).where(func.lower(SkillAlias.alias) == alias.lower()))
    if row:
        db.delete(row)
        db.commit()
