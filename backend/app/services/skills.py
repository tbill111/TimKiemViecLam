"""Tra kỹ năng theo tên/alias trong DB (không phân biệt hoa thường, bỏ hậu tố 'cơ bản')."""
from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.skills import normalize_skill, strip_level
from app.models import Skill, SkillAlias


class SkillResolver:
    def __init__(self, db: Session):
        self.by_key: dict[str, Skill] = {}
        skills = db.scalars(select(Skill)).all()
        by_id = {s.id: s for s in skills}
        for s in skills:
            key = normalize_skill(s.name)
            self.by_key.setdefault(key, s)
            self.by_key.setdefault(strip_level(key), s)
        for a in db.scalars(select(SkillAlias)).all():
            if a.skill_id in by_id:
                self.by_key.setdefault(normalize_skill(a.alias), by_id[a.skill_id])

    def resolve(self, name: str) -> Optional[Skill]:
        key = normalize_skill(name)
        return self.by_key.get(key) or self.by_key.get(strip_level(key))

    def resolve_many(self, names: Iterable[str]) -> list[Skill]:
        seen: set[int] = set()
        out: list[Skill] = []
        for n in names:
            s = self.resolve(n)
            if s and s.id not in seen:
                seen.add(s.id)
                out.append(s)
        return out
