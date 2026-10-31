"""BI: số liệu cho thẻ KPI, phương án dự phòng Recharts và guest token nhúng Superset.

Các số liệu tính cùng định nghĩa với 3 view trong bi/views.sql (v_skill_supply_demand, v_salary, v_funnel):
phễu đếm "từng đạt" từ application_status_history, không đếm theo trạng thái hiện tại.
"""
from __future__ import annotations

import statistics
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.deps import CurrentUser, get_current_user, get_db, require_role
from app.models import Application, ApplicationStatusHistory, Candidate, CandidateSkill, Job, JobSkill, Skill

router = APIRouter(prefix="/bi", tags=["bi"])

STAGES = ["applied", "screening", "interview", "offer", "hired"]
STAGE_REACHED_BY = {  # trạng thái nào trong lịch sử chứng tỏ hồ sơ từng đạt bước này
    "applied": set(STAGES) | {"rejected"},
    "screening": {"screening", "interview", "offer", "hired"},
    "interview": {"interview", "offer", "hired"},
    "offer": {"offer", "hired"},
    "hired": {"hired"},
}
BANDS = [(0, 40, "0–40"), (40, 60, "40–60"), (60, 80, "60–80"), (80, 101, "80–100")]


@router.get("/summary")
def summary(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    applications = db.scalar(select(func.count(Application.id))) or 0
    hired = db.scalar(select(func.count(Application.id)).where(Application.status == "hired")) or 0
    return {
        "candidates": db.scalar(select(func.count(Candidate.id))) or 0,
        "open_jobs": db.scalar(select(func.count(Job.id)).where(Job.status == "open")) or 0,
        "applications": applications,
        "hire_rate": round(hired / applications, 4) if applications else 0.0,
    }


@router.get("/skills")
def skills(user: CurrentUser = Depends(require_role("recruiter", "admin")), db: Session = Depends(get_db)):
    """Cung (ứng viên đã xác nhận) và cầu (tin đang mở) theo kỹ năng; thiếu hụt = cầu / cung, > 1 là thiếu người."""
    supply = dict(db.execute(
        select(CandidateSkill.skill_id, func.count(func.distinct(CandidateSkill.candidate_id)))
        .where(CandidateSkill.confirmed.is_(True)).group_by(CandidateSkill.skill_id)
    ).all())
    demand = dict(db.execute(
        select(JobSkill.skill_id, func.count(func.distinct(JobSkill.job_id)))
        .join(Job, Job.id == JobSkill.job_id).where(Job.status == "open").group_by(JobSkill.skill_id)
    ).all())
    items = []
    for s in db.scalars(select(Skill).order_by(Skill.id)):
        n_cand, n_jobs = int(supply.get(s.id, 0)), int(demand.get(s.id, 0))
        items.append({"skill": s.name, "category": s.category, "so_ung_vien": n_cand, "so_tin_yeu_cau": n_jobs,
                      "shortage": round(n_jobs / n_cand, 3) if n_cand else None})
    items.sort(key=lambda it: (-it["so_ung_vien"], it["skill"]))
    return {"items": items}


@router.get("/salary")
def salary(user: CurrentUser = Depends(require_role("recruiter", "admin")), db: Session = Depends(get_db)):
    """Trung vị lương tin (triệu VNĐ/tháng) theo tháng đăng và cấp bậc; bỏ tin thoả thuận (lương NULL)."""
    rows = db.execute(select(Job.posted_at, Job.level, Job.salary_min, Job.salary_max).where(Job.salary_min.is_not(None), Job.salary_max.is_not(None))).all()
    groups: dict[tuple[str, str], list[float]] = {}
    overall: dict[str, list[float]] = {}
    for posted, level, lo, hi in rows:
        month, mid = posted.strftime("%Y-%m"), (float(lo) + float(hi)) / 2
        groups.setdefault((month, level), []).append(mid)
        overall.setdefault(month, []).append(mid)
    return {
        "items": [{"month": m, "level": lv, "median_salary": round(statistics.median(v), 2), "n": len(v)} for (m, lv), v in sorted(groups.items())],
        "overall": [{"month": m, "median_salary": round(statistics.median(v), 2), "n": len(v)} for m, v in sorted(overall.items())],
    }


def funnel_data(db: Session, company_id: Optional[int]) -> dict[str, Any]:
    stmt = select(Application.id, Application.match_score, Application.applied_at, Application.status)
    if company_id is not None:
        stmt = stmt.join(Job, Job.id == Application.job_id).where(Job.company_id == company_id)
    apps = db.execute(stmt).all()
    ids = [a[0] for a in apps]
    reached: dict[int, set[str]] = {i: set() for i in ids}
    hired_at: dict[int, Any] = {}
    if ids:
        for app_id, to_status, changed_at in db.execute(
            select(ApplicationStatusHistory.application_id, ApplicationStatusHistory.to_status, ApplicationStatusHistory.changed_at)
            .where(ApplicationStatusHistory.application_id.in_(ids))
        ):
            reached[app_id].add(to_status)
            if to_status == "hired":
                hired_at[app_id] = changed_at
    counts = {st: sum(1 for i in ids if reached[i] & STAGE_REACHED_BY[st]) for st in STAGES}
    stages = []
    for k, st in enumerate(STAGES):
        prev = counts[STAGES[k - 1]] if k else None
        stages.append({"stage": st, "count": counts[st], "conversion_from_prev": round(counts[st] / prev, 4) if prev else None})
    days = [(hired_at[a[0]] - a[2]).total_seconds() / 86400 for a in apps if a[0] in hired_at]
    bands = []
    for lo, hi, label in BANDS:
        in_band = [a for a in apps if a[1] is not None and lo <= a[1] < hi]
        hired = sum(1 for a in in_band if "hired" in reached[a[0]])
        bands.append({"band": label, "applications": len(in_band), "hired": hired, "hire_rate": round(hired / len(in_band), 4) if in_band else None})
    total = counts["applied"]
    return {
        "stages": stages,
        "total_conversion": round(counts["hired"] / total, 4) if total else None,
        "median_time_to_hire_days": round(statistics.median(days), 1) if days else None,
        "by_score_band": bands,
    }


@router.get("/funnel")
def funnel(company_id: Optional[int] = Query(None), user: CurrentUser = Depends(require_role("recruiter", "admin")), db: Session = Depends(get_db)):
    """Phễu tuyển dụng. Nhà tuyển dụng chỉ thấy công ty mình; quản trị xem toàn thị trường hoặc lọc `company_id`."""
    scope = user.company_id if user.role == "recruiter" else company_id
    return funnel_data(db, scope)


def request_guest_token(user: CurrentUser) -> dict[str, Any]:
    s = get_settings()
    if not s.superset_url or not s.superset_dashboard_id:
        raise HTTPException(503, detail="superset_not_configured")
    rls: list[dict[str, Any]] = []
    if user.role == "recruiter":
        if not s.superset_funnel_dataset_id:
            raise HTTPException(503, detail="superset_not_configured")
        rls = [{"dataset": s.superset_funnel_dataset_id, "clause": f"company_id = {int(user.company_id or 0)}"}]
    try:
        with httpx.Client(base_url=s.superset_url, timeout=10) as c:
            login = c.post("/api/v1/security/login", json={"username": s.superset_admin_user, "password": s.superset_admin_password, "provider": "db", "refresh": True})
            login.raise_for_status()
            headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
            resp = c.post(
                "/api/v1/security/guest_token/",
                headers=headers,
                json={
                    "user": {"username": f"user-{user.id}", "first_name": user.full_name or "User", "last_name": user.role},
                    "resources": [{"type": "dashboard", "id": s.superset_dashboard_id}],
                    "rls": rls,
                },
            )
            resp.raise_for_status()
            token = resp.json()["token"]
    except (httpx.HTTPError, KeyError, ValueError):
        raise HTTPException(502, detail="superset_unavailable")
    return {"token": token, "dashboard_id": s.superset_dashboard_id, "superset_domain": s.superset_public_url}


@router.get("/guest-token")
def guest_token(user: CurrentUser = Depends(require_role("recruiter", "admin"))):
    """Token nhúng Superset; recruiter bị RLS `company_id = <công ty mình>` trên dataset v_funnel."""
    return request_guest_token(user)
