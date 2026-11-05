from __future__ import annotations

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db import Base
from app.models import Candidate, Resume, Skill, SkillAlias
from seed.load_seed import _ensure_profile_resume, _load_skill_aliases


def _session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'seed-data.db'}")
    Base.metadata.create_all(
        engine,
        tables=[
            Skill.__table__,
            Candidate.__table__,
            SkillAlias.__table__,
            Resume.__table__,
        ],
    )
    return engine


def test_aliases_are_imported_with_skill_foreign_keys_and_idempotently(tmp_path):
    engine = _session(tmp_path)
    with Session(engine) as db:
        python = Skill(name="Python", category="Programming")
        db.add(python)
        db.flush()
        skill_map = {"python": python}
        rows = [
            {"alias": "py", "skill_name": "Python"},
            {"alias": "python3", "skill_name": " Python "},
        ]

        assert _load_skill_aliases(db, rows, skill_map) == 2
        assert _load_skill_aliases(db, rows, skill_map) == 2
        assert db.scalar(select(func.count()).select_from(SkillAlias)) == 2
        assert set(db.scalars(select(SkillAlias.skill_id))) == {python.id}


def test_synthetic_profile_resume_is_linked_and_idempotent(tmp_path):
    engine = _session(tmp_path)
    with Session(engine) as db:
        candidate = Candidate(external_id="cand-seed-001", full_name="Demo Candidate")
        db.add(candidate)
        db.flush()
        profile = {
            "skills": ["Python", "SQL"],
            "years_exp": 1.5,
            "education_level": 3,
            "text": "Kỹ năng\nPython, SQL\nKinh nghiệm\n1.5 năm",
        }

        resume = _ensure_profile_resume(db, candidate, profile)
        same_resume = _ensure_profile_resume(db, candidate, profile)

        assert resume.id == same_resume.id
        assert resume.candidate_id == candidate.id
        assert resume.model_text == profile["text"]
        assert resume.parsed_json["source"] == "synthetic_seed_profile"
        assert resume.consent_at is not None
        assert db.scalar(select(func.count()).select_from(Resume)) == 1
