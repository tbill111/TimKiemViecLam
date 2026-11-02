"""Maintain the in-memory TF-IDF corpus for open jobs."""
from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.ai.scorers import fit_tfidf
from app.models import Job, JobSkill, Skill

_open_job_count: int | None = None


def fit_open_job_corpus(db: Session, force: bool = False) -> None:
    global _open_job_count
    count = int(db.scalar(select(func.count(Job.id)).where(Job.status == "open")) or 0)
    if not force and _open_job_count == count:
        return
    jobs = db.scalars(select(Job).where(Job.status == "open").order_by(Job.id)).all()
    corpus = []
    for job in jobs:
        skills = db.scalars(select(Skill.name).join(JobSkill, JobSkill.skill_id == Skill.id).where(JobSkill.job_id == job.id)).all()
        corpus.append(" ".join([job.title, job.description, " ".join(job.responsibilities or []), *skills]))
    if corpus:
        fit_tfidf(corpus)
    _open_job_count = count
