"""Hiện thực AIRepository bằng SQLAlchemy (hợp đồng ở app/ai/repository.py)."""
from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.embedder import embed_text, from_bytes
from app.ai.repository import ApplicantRow
from app.ai.types import CandidateInput, JobInput
from app.models import (
    Application,
    Candidate,
    CandidateSkill,
    Job,
    JobSkill,
    MatchResult,
    Resume,
    Skill,
    SkillAlias,
)
from app.services.jobs import job_input, job_skill_map
from app.services.skills import SkillResolver


def _f(x: Any) -> Optional[float]:
    return None if x is None else float(x)


def profile_text(cand: Candidate, skills: list[str]) -> str:
    p = cand.profile_json or {}
    parts = [p.get("careerGoal", ""), " ".join(skills)]
    parts += [f"{x.get('name', '')} {x.get('description', '')}" for x in p.get("projects", [])]
    parts += [f"{x.get('position', '')} {x.get('description', '')}" for x in p.get("experience", [])]
    return " ".join(x for x in parts if x).strip() or cand.major or " "


def refresh_candidate_embedding(db: Session, cand: Candidate) -> None:
    """Tính và lưu embedding hồ sơ (gọi khi hồ sơ hoặc kỹ năng đổi) để điểm khớp không phải mã hoá lúc yêu cầu."""
    from app.ai.embedder import to_bytes

    names = list(
        db.scalars(
            select(Skill.name)
            .join(CandidateSkill, CandidateSkill.skill_id == Skill.id)
            .where(CandidateSkill.candidate_id == cand.id, CandidateSkill.confirmed.is_(True))
            .order_by(Skill.id)
        )
    )
    try:
        cand.embedding = to_bytes(embed_text(profile_text(cand, names)))
    except Exception:  # tầng AI chưa sẵn sàng: API vẫn chạy, lần chấm đầu sẽ tự mã hoá
        cand.embedding = None


class SqlAIRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- ứng viên ---------------------------------------------------------
    def _candidate_input(self, cand: Candidate) -> CandidateInput:
        skills = list(
            self.db.scalars(
                select(Skill.name)
                .join(CandidateSkill, CandidateSkill.skill_id == Skill.id)
                .where(CandidateSkill.candidate_id == cand.id, CandidateSkill.confirmed.is_(True))
                .order_by(Skill.id)
            )
        )
        resume = self.db.scalar(
            select(Resume).where(Resume.candidate_id == cand.id, Resume.is_active.is_(True)).order_by(Resume.id.desc())
        )
        if resume is not None and resume.embedding:
            text = (resume.parsed_json or {}).get("model_text") or profile_text(cand, skills)
            emb = from_bytes(resume.embedding)
        else:
            text = profile_text(cand, skills)
            emb = from_bytes(cand.embedding) if cand.embedding else embed_text(text)  # embed_text chỉ là phương án cuối
        p = cand.profile_json or {}
        return CandidateInput(
            id=cand.id,
            skills=skills,
            years_exp=float(cand.years_exp or 0),
            edu=int(cand.education_level or 0),
            locations=list(p.get("preferredLocations", [])),
            work_types=list(p.get("preferredWorkTypes", [])),
            sal_min=_f(cand.expected_salary_min),
            sal_max=_f(cand.expected_salary_max),
            text=text,
            embedding=emb,
        )

    def candidate_input_for_user(self, user_id: int) -> Optional[CandidateInput]:
        cand = self.db.scalar(select(Candidate).where(Candidate.user_id == user_id))
        return self._candidate_input(cand) if cand else None

    def candidate_input(self, candidate_id: int) -> Optional[CandidateInput]:
        cand = self.db.get(Candidate, candidate_id)
        return self._candidate_input(cand) if cand else None

    # --- tin --------------------------------------------------------------
    def job_input(self, job_id: int) -> Optional[JobInput]:
        job = self.db.get(Job, job_id)
        if job is None:
            return None
        req, pref = job_skill_map(self.db, [job.id])[job.id]
        return job_input(job, req, pref)

    def open_jobs(self) -> list[JobInput]:
        jobs = self.db.scalars(select(Job).where(Job.status == "open").order_by(Job.id)).all()
        skills = job_skill_map(self.db, [j.id for j in jobs])
        return [job_input(j, *skills[j.id]) for j in jobs]

    def job_company_id(self, job_id: int) -> Optional[int]:
        return self.db.scalar(select(Job.company_id).where(Job.id == job_id))

    def applicants_for_job(self, job_id: int) -> list[ApplicantRow]:
        rows = self.db.execute(
            select(Application, Candidate).join(Candidate, Candidate.id == Application.candidate_id).where(Application.job_id == job_id)
        ).all()
        return [
            ApplicantRow(self._candidate_input(c), c.full_name, a.id, a.status, a.applied_at.isoformat())
            for a, c in rows
        ]

    # --- danh mục ---------------------------------------------------------
    def skill_index_rows(self) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
        skills = [(s.name, s.category) for s in self.db.scalars(select(Skill).order_by(Skill.id))]
        aliases = [
            (a, n)
            for a, n in self.db.execute(select(SkillAlias.alias, Skill.name).join(Skill, Skill.id == SkillAlias.skill_id)).all()
        ]
        return skills, aliases

    def open_jobs_requiring(self, skill: str) -> int:
        s = SkillResolver(self.db).resolve(skill)
        if s is None:
            return 0
        return int(
            self.db.scalar(
                select(func.count(func.distinct(JobSkill.job_id)))
                .join(Job, Job.id == JobSkill.job_id)
                .where(JobSkill.skill_id == s.id, Job.status == "open")
            )
            or 0
        )

    def learning_steps(self, skill: str) -> list[str]:
        s = SkillResolver(self.db).resolve(skill)
        return list(s.learning_steps or []) if s else []

    # --- ghi --------------------------------------------------------------
    def save_resume(self, user_id: int, filename: str, parsed: dict[str, Any], consent: bool) -> int:
        cand = self.db.scalar(select(Candidate).where(Candidate.user_id == user_id))
        if cand is None:
            raise LookupError("candidate_profile_not_found")
        for old in self.db.scalars(select(Resume).where(Resume.candidate_id == cand.id, Resume.is_active.is_(True))):
            old.is_active = False
        stored = {k: v for k, v in parsed.items() if k != "embedding"}
        resume = Resume(
            candidate_id=cand.id,
            filename=filename,
            raw_text=parsed.get("text", ""),
            parsed_json=stored,
            embedding=parsed.get("embedding"),
            is_active=True,
        )
        self.db.add(resume)
        if consent and cand.consent_at is None:
            cand.consent_at = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
        cand.years_exp = parsed.get("years_exp", cand.years_exp)
        if parsed.get("education_level"):
            cand.education_level = parsed["education_level"]
        resolver = SkillResolver(self.db)
        existing = {cs.skill_id: cs for cs in self.db.scalars(select(CandidateSkill).where(CandidateSkill.candidate_id == cand.id))}
        for hit in parsed.get("skills", []):
            skill = resolver.resolve(hit["name"])
            if skill is None or skill.id in existing:
                continue  # không hạ cấp kỹ năng đã xác nhận
            self.db.add(CandidateSkill(candidate_id=cand.id, skill_id=skill.id, source="cv", confirmed=False))
        self.db.commit()
        return resume.id

    def save_match(self, candidate_id: int, job_id: int, match: dict[str, Any]) -> None:
        c = match["components"]
        row = self.db.get(MatchResult, (candidate_id, job_id, match["model_version"]))
        if row is None:
            row = MatchResult(candidate_id=candidate_id, job_id=job_id, model_version=match["model_version"], total_score=0)
            self.db.add(row)
        row.total_score = match["total_score"]
        row.skill_req_score, row.skill_pref_score = c.get("skill_req"), c.get("skill_pref")
        row.semantic_score, row.exp_score, row.edu_score = c.get("semantic"), c.get("exp"), c.get("edu")
        row.location_score = c.get("pref")
        row.matched_skills = match["matched_required"] + match["matched_preferred"]
        row.missing_skills = match["missing_required"] + match["missing_preferred"]
        row.computed_at = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
        self.db.commit()
