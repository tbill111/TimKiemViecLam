"""BI summary endpoints and Superset embedded guest-token exchange."""
from __future__ import annotations

import re
from typing import Any

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.deps import CurrentUser, get_current_user, get_db, require_role
from app.models import Application, Candidate, Job

router = APIRouter(prefix="/bi", tags=["bi"])


def _company_clause(user: CurrentUser) -> tuple[str, dict[str, int]]:
    if user.role == "admin":
        return "", {}
    if user.company_id is None:
        raise HTTPException(403, detail="recruiter_company_required")
    return "WHERE company_id = :company_id", {"company_id": user.company_id}


def _rows(db: Session, view: str, user: CurrentUser | None = None):
    if view not in {"v_skill_supply_demand", "v_salary", "v_funnel", "v_funnel_stages"}:
        raise ValueError("Unknown BI view")
    clause = ""
    params: dict[str, Any] = {}
    if view in {"v_funnel", "v_funnel_stages"} and user is not None and user.role != "admin":
        clause, params = _company_clause(user)
    result = db.execute(text(f"SELECT * FROM {view} {clause}"), params)
    return [dict(row._mapping) for row in result]


@router.get("/summary")
def summary(db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    if user.role != "recruiter":
        candidates = int(db.scalar(select(func.count(Candidate.id))) or 0)
        open_jobs = int(db.scalar(select(func.count(Job.id)).where(Job.status == "open")) or 0)
        applications = int(db.scalar(select(func.count(Application.id))) or 0)
        hired = int(db.scalar(select(func.count(Application.id)).where(Application.status == "hired")) or 0)
    else:
        candidates = int(db.scalar(select(func.count(func.distinct(Application.candidate_id))).join(Job, Job.id == Application.job_id).where(Job.company_id == user.company_id)) or 0)
        open_jobs = int(db.scalar(select(func.count(Job.id)).where(Job.status == "open", Job.company_id == user.company_id)) or 0)
        applications = int(db.scalar(select(func.count(Application.id)).join(Job, Job.id == Application.job_id).where(Job.company_id == user.company_id)) or 0)
        hired = int(db.scalar(select(func.count(Application.id)).join(Job, Job.id == Application.job_id).where(Job.company_id == user.company_id, Application.status == "hired")) or 0)
    return {"candidates": candidates, "open_jobs": open_jobs, "applications": applications,
            "hire_rate": round(100 * hired / applications, 2) if applications else 0.0}


@router.get("/skills")
def skills(db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("recruiter", "admin"))):
    return {"items": _rows(db, "v_skill_supply_demand")}


@router.get("/salary")
def salary(db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("recruiter", "admin"))):
    return {"items": _rows(db, "v_salary")}


@router.get("/funnel")
def funnel(db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("recruiter", "admin"))):
    return {"items": _rows(db, "v_funnel", user), "stages": _rows(db, "v_funnel_stages", user)}


def _superset_guest_token(user: CurrentUser) -> dict[str, str]:
    if not settings.dashboard_id:
        raise HTTPException(503, detail="superset_not_configured")
    rls = []
    if user.role != "admin":
        if not settings.funnel_dataset_id or not settings.funnel_stages_dataset_id:
            raise HTTPException(503, detail="superset_not_configured")
        if not settings.guest_token_secret or not settings.superset_password:
            raise HTTPException(503, detail="superset_not_configured")
        if not re.fullmatch(r"[1-9][0-9]*", str(user.company_id or "")):
            raise HTTPException(403, detail="recruiter_company_required")
        clause = f"company_id = {user.company_id}"
        rls = [
            {"dataset": int(settings.funnel_dataset_id), "clause": clause},
            {"dataset": int(settings.funnel_stages_dataset_id), "clause": clause},
        ]
    elif not settings.guest_token_secret or not settings.superset_password:
        raise HTTPException(503, detail="superset_not_configured")
    session = requests.Session()
    base = settings.superset_url.rstrip("/")
    try:
        # Superset 4.1 keeps a session cookie for write endpoints, in addition to its Bearer token.
        login_page = session.get(f"{base}/login/", timeout=10)
        login_page.raise_for_status()
        csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', login_page.text)
        form_data = {
            "username": settings.superset_username,
            "password": settings.superset_password,
            "provider": "db",
            "refresh": "true",
        }
        if csrf_match:
            form_data["csrf_token"] = csrf_match.group(1)
        form_login = session.post(f"{base}/login/", data=form_data, allow_redirects=True, timeout=10)
        form_login.raise_for_status()
        login = session.post(f"{base}/api/v1/security/login", json={
            "username": settings.superset_username, "password": settings.superset_password,
            "provider": "db", "refresh": True,
        }, timeout=10)
        login.raise_for_status()
        access = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {access}", "Content-Type": "application/json", "Referer": f"{base}/"}
        csrf_response = session.get(f"{base}/api/v1/security/csrf_token/", headers=headers, timeout=10)
        csrf_response.raise_for_status()
        csrf = csrf_response.json().get("result")
        if csrf:
            headers.update({"X-CSRFToken": csrf, "Referer": f"{base}/"})
        response = session.post(f"{base}/api/v1/security/guest_token/", headers=headers, json={
            "user": {"username": f"smartcareer-{user.id}", "first_name": user.full_name, "last_name": ""},
            "resources": [{"type": "dashboard", "id": settings.dashboard_id}],
            "rls": rls,
        }, timeout=10)
        response.raise_for_status()
        payload = response.json()
        return {"token": payload["token"], "dashboard_id": settings.dashboard_id, "superset_domain": settings.superset_public_url.rstrip("/")}
    except (requests.RequestException, KeyError, ValueError) as exc:
        raise HTTPException(503, detail={"detail": "superset_unavailable", "reason": str(exc)[:240]}) from exc


@router.get("/guest-token")
def guest_token(user: CurrentUser = Depends(require_role("recruiter", "admin"))):
    return _superset_guest_token(user)
