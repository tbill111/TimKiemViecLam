"""Create about 1,200 simulated applications with funnel history.

Status probabilities are independent of match_score; this dataset demonstrates
BI calculations and is not evidence of model quality.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from sqlalchemy import select

from app.ai.scorers import score_pair
from app.models import Application, ApplicationStatusHistory, Candidate, Job, Recruiter
from app.services.ai_repo import SqlAIRepository

STATUS_STEPS = ["applied", "screening", "interview", "offer", "hired"]


def generate_applications(db, target: int = 1200, seed: int = 42) -> int:
    rng = random.Random(seed)
    candidates = list(db.scalars(select(Candidate).order_by(Candidate.id)))
    jobs = list(db.scalars(select(Job).where(Job.status == "open").order_by(Job.id)))
    if not candidates or not jobs:
        return 0
    existing = {(row.candidate_id, row.job_id) for row in db.scalars(select(Application))}
    pairs = [(c.id, j.id) for c in candidates for j in jobs if (c.id, j.id) not in existing]
    rng.shuffle(pairs)
    pairs = pairs[:max(0, min(target - len(existing), len(pairs)))]
    repo = SqlAIRepository(db)
    candidate_inputs = {c.id: repo.candidate_input(c.id) for c in candidates}
    job_inputs = {j.id: repo.job_input(j.id) for j in jobs}
    recruiters = {row.company_id: row.user_id for row in db.scalars(select(Recruiter))}
    now = datetime.utcnow()
    for index, (candidate_id, job_id) in enumerate(pairs):
        candidate = next(c for c in candidates if c.id == candidate_id)
        job = next(j for j in jobs if j.id == job_id)
        cand_input, job_input = candidate_inputs[candidate_id], job_inputs[job_id]
        score = score_pair("m3", cand_input, job_input)["total_score"] if cand_input and job_input else None
        status = "applied"
        reached = ["applied"]
        # Funnel-stage outcomes are generated independently of model scores.
        if rng.random() < 0.62:
            reached.append("screening")
            if rng.random() < 0.58:
                reached.append("interview")
                if rng.random() < 0.42:
                    reached.append("offer")
                    if rng.random() < 0.38:
                        reached.append("hired")
        if reached[-1] != "hired" and rng.random() < 0.22:
            reached.append("rejected")
        status = reached[-1]
        applied_at = now - timedelta(days=rng.randint(0, 365), hours=rng.randint(0, 23))
        app = Application(candidate_id=candidate_id, job_id=job_id, status=status, match_score=score, applied_at=applied_at)
        db.add(app)
        db.flush()
        previous = None
        changed_at = applied_at
        for step_index, step in enumerate(reached):
            if step_index:
                changed_at += timedelta(days=rng.randint(1, 7))
            db.add(ApplicationStatusHistory(
                application_id=app.id, from_status=previous, to_status=step,
                changed_by=recruiters.get(job.company_id) if step_index else candidate.user_id,
                note="Dữ liệu mô phỏng" if step_index == 0 else None,
                changed_at=changed_at,
            ))
            previous = step
    return len(pairs)
