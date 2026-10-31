"""Dựng JobInput/JobDTO từ bản ghi DB và tính embedding khi lưu tin."""
from __future__ import annotations

from typing import Any, Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.embedder import embed_text, from_bytes, to_bytes
from app.ai.types import JobInput
from app.models import Job, JobSkill, Skill

WORK_TYPE_LABEL = {"full_time": "Toàn thời gian", "part_time": "Bán thời gian", "internship": "Thực tập"}


def work_type_label(job_type: str, work_mode: str) -> str:
    """Quy tắc giống adapter frontend: làm việc từ xa → 'Remote', còn lại theo loại hình."""
    return "Remote" if work_mode == "remote" else WORK_TYPE_LABEL.get(job_type, "")


def job_skill_map(db: Session, job_ids: Iterable[int]) -> dict[int, tuple[list[str], list[str]]]:
    ids = list(job_ids)
    out: dict[int, tuple[list[str], list[str]]] = {i: ([], []) for i in ids}
    if not ids:
        return out
    rows = db.execute(
        select(JobSkill.job_id, Skill.name, JobSkill.is_required)
        .join(Skill, Skill.id == JobSkill.skill_id)
        .where(JobSkill.job_id.in_(ids))
        .order_by(JobSkill.job_id, Skill.id)
    ).all()
    for job_id, name, required in rows:
        out[job_id][0 if required else 1].append(name)
    return out


def job_text(job: Job, required: list[str], preferred: list[str]) -> str:
    return " ".join([job.title, job.description or "", " ".join(job.responsibilities or []), " ".join(required + preferred)])


def _f(x: Any) -> Optional[float]:
    return None if x is None else float(x)


def job_input(job: Job, required: list[str], preferred: list[str]) -> JobInput:
    text = job_text(job, required, preferred)
    emb = from_bytes(job.embedding) if job.embedding else embed_text(text)
    return JobInput(
        id=job.id,
        required=required,
        preferred=preferred,
        min_years=float(job.min_years_exp or 0),
        min_edu=int(job.min_education or 0),
        location=job.location.name if job.location else "",
        work_type_label=work_type_label(job.job_type, job.work_mode),
        salary_min=_f(job.salary_min),
        salary_max=_f(job.salary_max),
        text=text,
        embedding=emb,
    )


def job_dto(job: Job, required: list[str], preferred: list[str]) -> dict[str, Any]:
    c = job.company
    return {
        "id": job.id,
        "external_id": job.external_id,
        "title": job.title,
        "company": {"id": c.id, "name": c.name, "size_range": c.size_range, "industry": c.industry},
        "location": job.location.name if job.location else "",
        "category": job.category,
        "level": job.level,
        "job_type": job.job_type,
        "work_mode": job.work_mode,
        "salary_min": _f(job.salary_min),
        "salary_max": _f(job.salary_max),
        "min_years_exp": float(job.min_years_exp or 0),
        "min_education": int(job.min_education or 0),
        "description": job.description,
        "responsibilities": job.responsibilities or [],
        "required_skills": required,
        "preferred_skills": preferred,
        "status": job.status,
        "posted_at": job.posted_at.isoformat() if job.posted_at else None,
        "deadline": job.deadline.isoformat() if job.deadline else None,
    }


def refresh_embedding(job: Job, required: list[str], preferred: list[str]) -> None:
    """Tính lại embedding tin (gọi khi tạo/sửa tin)."""
    try:
        job.embedding = to_bytes(embed_text(job_text(job, required, preferred)))
    except Exception:  # API vẫn chạy khi tầng AI chưa sẵn sàng
        job.embedding = None
