"""SQLAlchemy implementation of the AIRepository contract."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.repository import ApplicantRow
from app.ai.types import CandidateInput, JobInput
from app.models import (
    Application, Candidate, CandidateSkill, Company, Job, JobSkill, Location, Recruiter,
    Resume, Skill, SkillAlias, User,
)


def _unpack(data: bytes | None):
    if not data:
        return None
    import numpy as np

    return np.frombuffer(data, dtype=np.float32)


class SqlAIRepository:
    def __init__(self, db: Session):
        self.db = db

    def candidate_input_for_user(self, user_id: int) -> CandidateInput | None:
        candidate = self.db.scalar(select(Candidate).where(Candidate.user_id == user_id))
        return self.candidate_input(candidate.id) if candidate else None

    def candidate_input(self, candidate_id: int) -> CandidateInput | None:
        candidate = self.db.get(Candidate, candidate_id)
        if candidate is None:
            return None
        skills = list(self.db.scalars(
            select(Skill.name).join(CandidateSkill, CandidateSkill.skill_id == Skill.id)
            .where(CandidateSkill.candidate_id == candidate.id, CandidateSkill.confirmed.is_(True))
            .order_by(Skill.name)
        ))
        resume = self.db.scalar(
            select(Resume).where(Resume.candidate_id == candidate.id, Resume.is_active.is_(True))
            .order_by(Resume.created_at.desc()).limit(1)
        )
        profile = candidate.profile_json or {}
        return CandidateInput(
            id=candidate.id,
            skills=skills,
            years_exp=float(candidate.years_exp or 0),
            edu=int(candidate.education_level or 0),
            locations=list(profile.get("preferredLocations") or ([self._location_name(candidate.location_id)] if candidate.location_id else [])),
            work_types=list(profile.get("preferredWorkTypes") or []),
            sal_min=float(candidate.expected_salary_min) if candidate.expected_salary_min is not None else None,
            sal_max=float(candidate.expected_salary_max) if candidate.expected_salary_max is not None else None,
            text=(resume.model_text if resume else "") or str(profile.get("careerGoal") or ""),
            embedding=_unpack((resume.embedding if resume else None) or candidate.embedding),
        )

    def _location_name(self, location_id: int | None) -> str:
        if location_id is None:
            return ""
        return self.db.scalar(select(Location.name).where(Location.id == location_id)) or ""

    def job_input(self, job_id: int) -> JobInput | None:
        job = self.db.get(Job, job_id)
        if job is None:
            return None
        skills = list(self.db.execute(
            select(Skill.name, JobSkill.priority).join(JobSkill, JobSkill.skill_id == Skill.id)
            .where(JobSkill.job_id == job.id)
        ))
        company = self.db.get(Company, job.company_id)
        location = self._location_name(job.location_id)
        required = [name for name, priority in skills if priority == "required"]
        preferred = [name for name, priority in skills if priority == "preferred"]
        type_label = "Remote" if job.work_mode == "remote" else {
            "full_time": "Toàn thời gian", "part_time": "Bán thời gian", "internship": "Thực tập"
        }.get(job.job_type, "Toàn thời gian")
        text = " ".join([job.title, job.description, " ".join(job.responsibilities or []), *required, *preferred])
        return JobInput(
            id=job.id, required=required, preferred=preferred, min_years=float(job.min_years_exp or 0),
            min_edu=job.min_education, location=location, work_type_label=type_label,
            salary_min=float(job.salary_min) if job.salary_min is not None else None,
            salary_max=float(job.salary_max) if job.salary_max is not None else None,
            text=text, embedding=_unpack(job.embedding),
        )

    def open_jobs(self) -> list[JobInput]:
        from app.services.ai_index import fit_open_job_corpus
        fit_open_job_corpus(self.db)
        jobs = self.db.scalars(select(Job).where(Job.status == "open").order_by(Job.id)).all()
        return [item for job in jobs if (item := self.job_input(job.id)) is not None]

    def job_company_id(self, job_id: int) -> int | None:
        return self.db.scalar(select(Job.company_id).where(Job.id == job_id))

    def applicants_for_job(self, job_id: int) -> list[ApplicantRow]:
        rows = self.db.execute(
            select(Application, Candidate, User)
            .join(Candidate, Candidate.id == Application.candidate_id)
            .outerjoin(User, User.id == Candidate.user_id)
            .where(Application.job_id == job_id)
        ).all()
        result = []
        for app, cand, user in rows:
            value = self.candidate_input(cand.id)
            if value is not None:
                result.append(ApplicantRow(value, user.full_name if user else cand.full_name, app.id, app.status, app.applied_at.isoformat()))
        return result

    def skill_index_rows(self) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
        skills = list(self.db.execute(select(Skill.name, Skill.category).where(Skill.is_active.is_(True))))
        aliases = list(self.db.execute(
            select(SkillAlias.alias, Skill.name).join(Skill, Skill.id == SkillAlias.skill_id)
            .where(Skill.is_active.is_(True))
        ))
        return [(a, b or "") for a, b in skills], [(a, b) for a, b in aliases]

    def open_jobs_requiring(self, skill: str) -> int:
        return int(self.db.scalar(
            select(func.count(func.distinct(JobSkill.job_id)))
            .join(Job, Job.id == JobSkill.job_id).join(Skill, Skill.id == JobSkill.skill_id)
            .where(Job.status == "open", func.lower(Skill.name) == skill.lower())
        ) or 0)

    def learning_steps(self, skill: str) -> list[str]:
        value = self.db.scalar(select(Skill.learning_steps).where(func.lower(Skill.name) == skill.lower()))
        return value or []

    def save_resume(self, user_id: int, filename: str, parsed: dict[str, Any], consent: bool) -> int:
        if not consent:
            raise ValueError("consent_required")
        candidate = self.db.scalar(select(Candidate).where(Candidate.user_id == user_id))
        if candidate is None:
            raise ValueError("candidate_profile_not_found")
        now = datetime.utcnow()
        candidate.consent_at = now
        candidate.embedding = parsed.get("embedding")
        for old in self.db.scalars(select(Resume).where(Resume.candidate_id == candidate.id, Resume.is_active.is_(True))):
            old.is_active = False
        resume = Resume(
            candidate_id=candidate.id,
            filename=filename[:255],
            parsed_json={k: v for k, v in parsed.items() if k not in {"embedding"}},
            model_text=parsed.get("model_text", ""),
            embedding=parsed.get("embedding"),
            consent_at=now,
        )
        self.db.add(resume)
        candidate.years_exp = float(parsed.get("years_exp") or 0)
        candidate.education_level = int(parsed.get("education_level") or 0)
        existing_ids = set(self.db.scalars(select(CandidateSkill.skill_id).where(CandidateSkill.candidate_id == candidate.id)))
        skills = {s.name.casefold(): s for s in self.db.scalars(select(Skill).where(Skill.is_active.is_(True)))}
        aliases = {a.alias.casefold(): a.skill_id for a in self.db.scalars(select(SkillAlias))}
        for hit in parsed.get("skills", []):
            name = hit.get("name", "") if isinstance(hit, dict) else str(hit)
            skill = skills.get(name.casefold())
            skill_id = skill.id if skill else aliases.get(name.casefold())
            if skill_id and skill_id not in existing_ids:
                self.db.add(CandidateSkill(candidate_id=candidate.id, skill_id=skill_id, source="cv", confirmed=False))
                existing_ids.add(skill_id)
        self.db.flush()
        self.db.commit()
        return resume.id

    def save_match(self, candidate_id: int, job_id: int, match: dict[str, Any]) -> None:
        from app.models import MatchResult

        row = self.db.scalar(select(MatchResult).where(
            MatchResult.candidate_id == candidate_id,
            MatchResult.job_id == job_id,
            MatchResult.model_version == match["model_version"],
        ))
        if row is None:
            row = MatchResult(candidate_id=candidate_id, job_id=job_id, model=match["model"], model_version=match["model_version"], total_score=match["total_score"], result_json=match)
            self.db.add(row)
        else:
            row.model = match["model"]
            row.total_score = match["total_score"]
            row.result_json = match
            row.created_at = datetime.utcnow()
        self.db.commit()
