"""Mô phỏng ~1.200 đơn ứng tuyển kèm lịch sử trạng thái theo phễu (dùng cho dashboard BI).

Quan trọng về trung thực: xác suất đi tiếp mỗi bước KHÔNG phụ thuộc vào `match_score`. Vì vậy biểu đồ "tỷ lệ tuyển theo
nhóm điểm khớp" trên dữ liệu seed chỉ minh hoạ cách tính, không chứng minh mô hình AI tốt. Hiệu quả mô hình chỉ được kết luận
từ tập 300 cặp gán nhãn (notebooks/03_ranking_eval.ipynb).
"""
from __future__ import annotations

import datetime as dt
import os
import random

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.scorers import score_pair
from app.models import Application, ApplicationStatusHistory, Candidate, Job
from app.services.ai_repo import SqlAIRepository
from app.services.jobs import job_input, job_skill_map

NOW = dt.datetime(2026, 10, 31, 12, 0, 0)
N_TARGET = 1200
# Xác suất vượt từng bước; thất bại thì 70% bị loại (rejected), 30% còn đang chờ ở bước đó
PASS = {"applied": 0.62, "screening": 0.55, "interview": 0.42, "offer": 0.78}
NEXT = {"applied": "screening", "screening": "interview", "interview": "offer", "offer": "hired"}


def generate_applications(db: Session, rng: random.Random, target: int = N_TARGET) -> int:
    repo = SqlAIRepository(db)
    jobs = list(db.scalars(select(Job).where(Job.status == "open").order_by(Job.id)))
    skills = job_skill_map(db, [j.id for j in jobs])
    job_inputs = {j.id: job_input(j, *skills[j.id]) for j in jobs}
    by_cat: dict[str, list[Job]] = {}
    for j in jobs:
        by_cat.setdefault(j.category, []).append(j)
    candidates = list(db.scalars(select(Candidate).where(Candidate.external_id != "cand-demo").order_by(Candidate.id)))
    per_candidate = target / max(1, len(candidates))
    model = os.getenv("DEFAULT_MODEL", "m3")
    created = 0
    for cand in candidates:
        cand_in = repo._candidate_input(cand)
        # 70% đơn vào tin của nhóm nghề khớp kỹ năng nhất, 30% vào tin ngẫu nhiên
        best_cat = max(by_cat, key=lambda c: sum(1 for j in by_cat[c] for s in job_inputs[j.id].required if s in cand_in.skills))
        k = max(1, min(10, round(rng.gauss(per_candidate, 1.8))))
        chosen: dict[int, Job] = {}
        while len(chosen) < min(k, len(jobs)):
            pool = by_cat[best_cat] if rng.random() < 0.7 else jobs
            j = rng.choice(pool)
            chosen[j.id] = j
        for job in chosen.values():
            applied = job.posted_at + dt.timedelta(days=rng.randint(0, 25), hours=rng.randint(8, 18))
            if applied > NOW - dt.timedelta(days=1):
                applied = NOW - dt.timedelta(days=rng.randint(1, 10))
            status, when, history = "applied", applied, [(None, "applied", applied)]
            while status in NEXT:
                if rng.random() < PASS[status]:
                    when = when + dt.timedelta(days=rng.randint(1, 7), hours=rng.randint(0, 6))
                    if when > NOW:
                        break  # chưa kịp tới bước này vào thời điểm "hôm nay" của dữ liệu demo
                    history.append((status, NEXT[status], when))
                    status = NEXT[status]
                else:
                    if rng.random() < 0.7:
                        when = when + dt.timedelta(days=rng.randint(1, 7))
                        if when <= NOW:
                            history.append((status, "rejected", when))
                            status = "rejected"
                    break
            score = score_pair(model, cand_in, job_inputs[job.id])["total_score"]
            app = Application(candidate_id=cand.id, job_id=job.id, match_score=score, status=status, applied_at=applied, updated_at=history[-1][2])
            db.add(app)
            db.flush()
            db.add_all([ApplicationStatusHistory(application_id=app.id, from_status=f, to_status=t, changed_at=w) for f, t, w in history])
            created += 1
    db.commit()
    return created
