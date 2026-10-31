from __future__ import annotations

import datetime as dt
import os
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.scorers import score_pair
from app.ai.types import ModelNotAvailable
from app.deps import CurrentUser, get_db, require_role
from app.models import Application, ApplicationStatusHistory, Candidate, Job, Resume
from app.services.ai_repo import SqlAIRepository

router = APIRouter(tags=["applications"])

# Luồng phễu: applied → screening → interview → offer → hired; rejected từ bất kỳ bước chưa kết thúc
NEXT_STATUS = {"applied": "screening", "screening": "interview", "interview": "offer", "offer": "hired"}
FINAL = {"hired", "rejected"}
Status = Literal["applied", "screening", "interview", "offer", "hired", "rejected"]


class ApplyIn(BaseModel):
    job_id: int
    resume_id: Optional[int] = None


class StatusIn(BaseModel):
    status: Status
    note: str = ""


def can_transition(current: str, new: str) -> bool:
    if current in FINAL:
        return False
    return new == "rejected" or NEXT_STATUS.get(current) == new


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


def application_dto(app: Application, history: list[ApplicationStatusHistory], job: Optional[Job] = None) -> dict[str, Any]:
    dto: dict[str, Any] = {
        "id": app.id,
        "job_id": app.job_id,
        "candidate_id": app.candidate_id,
        "status": app.status,
        "match_score": app.match_score,
        "applied_at": app.applied_at.isoformat(),
        "updated_at": app.updated_at.isoformat(),
        "history": [
            {"from_status": h.from_status, "to_status": h.to_status, "changed_at": h.changed_at.isoformat(), "note": h.note}
            for h in history
        ],
    }
    if job is not None:
        dto["job"] = {"title": job.title, "company_name": job.company.name}
    return dto


def _history(db: Session, app_ids: list[int]) -> dict[int, list[ApplicationStatusHistory]]:
    out: dict[int, list[ApplicationStatusHistory]] = {i: [] for i in app_ids}
    if app_ids:
        for h in db.scalars(select(ApplicationStatusHistory).where(ApplicationStatusHistory.application_id.in_(app_ids)).order_by(ApplicationStatusHistory.changed_at, ApplicationStatusHistory.id)):
            out[h.application_id].append(h)
    return out


def _score_at_apply(db: Session, user_id: int, job_id: int) -> Optional[int]:
    repo = SqlAIRepository(db)
    cand, job = repo.candidate_input_for_user(user_id), repo.job_input(job_id)
    if cand is None or job is None:
        return None
    model = os.getenv("DEFAULT_MODEL", "m3")
    try:
        return score_pair(model, cand, job)["total_score"]
    except ModelNotAvailable:
        return score_pair("m3", cand, job)["total_score"]


@router.post("/applications", status_code=201)
def apply(body: ApplyIn, user: CurrentUser = Depends(require_role("candidate")), db: Session = Depends(get_db)):
    cand = db.scalar(select(Candidate).where(Candidate.user_id == user.id))
    if cand is None:
        raise HTTPException(404, detail="candidate_profile_not_found")
    job = db.get(Job, body.job_id)
    if job is None:
        raise HTTPException(404, detail="job_not_found")
    if job.status != "open":
        raise HTTPException(409, detail="job_closed")
    if db.scalar(select(Application.id).where(Application.candidate_id == cand.id, Application.job_id == job.id)):
        raise HTTPException(409, detail="already_applied")
    resume_id = body.resume_id
    if resume_id is not None and db.scalar(select(Resume.id).where(Resume.id == resume_id, Resume.candidate_id == cand.id)) is None:
        raise HTTPException(404, detail="resume_not_found")
    now = _now()
    app = Application(candidate_id=cand.id, job_id=job.id, resume_id=resume_id, status="applied", applied_at=now, updated_at=now,
                      match_score=_score_at_apply(db, user.id, job.id))
    db.add(app)
    db.flush()
    db.add(ApplicationStatusHistory(application_id=app.id, from_status=None, to_status="applied", changed_by=user.id, changed_at=now))
    db.commit()
    return application_dto(app, _history(db, [app.id])[app.id], job)


@router.get("/applications/me")
def my_applications(user: CurrentUser = Depends(require_role("candidate")), db: Session = Depends(get_db)):
    cand = db.scalar(select(Candidate).where(Candidate.user_id == user.id))
    if cand is None:
        return {"items": []}
    apps = list(db.scalars(select(Application).where(Application.candidate_id == cand.id).order_by(Application.applied_at.desc())))
    hist = _history(db, [a.id for a in apps])
    return {"items": [application_dto(a, hist[a.id], a.job) for a in apps]}


def _owned_job(db: Session, user: CurrentUser, job_id: int) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, detail="job_not_found")
    if user.role != "admin" and job.company_id != user.company_id:
        raise HTTPException(403, detail="not_your_job")
    return job


@router.get("/jobs/{job_id}/applications")
def job_applications(job_id: int, user: CurrentUser = Depends(require_role("recruiter", "admin")), db: Session = Depends(get_db)):
    _owned_job(db, user, job_id)
    apps = list(db.scalars(select(Application).where(Application.job_id == job_id).order_by(Application.match_score.desc().nulls_last(), Application.id)))
    hist = _history(db, [a.id for a in apps])
    items = []
    for a in apps:
        dto = application_dto(a, hist[a.id])
        dto["candidate_name"] = a.candidate.full_name
        items.append(dto)
    return {"job_id": job_id, "items": items}


@router.patch("/applications/{application_id}/status")
def change_status(application_id: int, body: StatusIn, user: CurrentUser = Depends(require_role("recruiter", "admin")), db: Session = Depends(get_db)):
    app = db.get(Application, application_id)
    if app is None:
        raise HTTPException(404, detail="application_not_found")
    _owned_job(db, user, app.job_id)
    if not can_transition(app.status, body.status):
        raise HTTPException(409, detail={"detail": "invalid_transition", "from": app.status, "to": body.status})
    now = _now()
    db.add(ApplicationStatusHistory(application_id=app.id, from_status=app.status, to_status=body.status, changed_by=user.id, changed_at=now, note=body.note))
    app.status, app.updated_at = body.status, now
    db.commit()
    return application_dto(app, _history(db, [app.id])[app.id], app.job)
