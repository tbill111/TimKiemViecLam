"""Applications and legal status transition endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai.repository import get_ai_repo
from app.deps import CurrentUser, get_db, require_role
from app.models import Application, ApplicationStatusHistory, Candidate, Company, Job, Resume, User
from app.services.ai_repo import SqlAIRepository

router = APIRouter(tags=["applications"])
NEXT = {"applied": "screening", "screening": "interview", "interview": "offer", "offer": "hired"}
FINAL = {"hired", "rejected"}


def _candidate(db: Session, user_id: int) -> Candidate:
    row = db.scalar(select(Candidate).where(Candidate.user_id == user_id))
    if row is None:
        raise HTTPException(404, detail="candidate_profile_not_found")
    return row


def _history(db: Session, application_id: int):
    rows = db.scalars(select(ApplicationStatusHistory).where(ApplicationStatusHistory.application_id == application_id).order_by(ApplicationStatusHistory.changed_at, ApplicationStatusHistory.id))
    return [{"from_status": row.from_status, "to_status": row.to_status, "note": row.note, "changed_at": row.changed_at.isoformat() + "Z"} for row in rows]


def _application_dto(db: Session, app: Application):
    job = db.get(Job, app.job_id)
    company = db.get(Company, job.company_id) if job else None
    return {"id": str(app.id), "job_id": str(app.job_id), "job_title": job.title if job else "", "company": company.name if company else "",
            "applied_at": app.applied_at.isoformat() + "Z", "status": app.status, "match_score": app.match_score,
            "history": _history(db, app.id)}


@router.post("/applications", status_code=201)
def apply(body: dict[str, Any], db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("candidate"))):
    job_id = body.get("job_id")
    if isinstance(job_id, str) and job_id.isdigit():
        job_id = int(job_id)  # GET /jobs trả id dạng chuỗi
    if not isinstance(job_id, int) or isinstance(job_id, bool):
        raise HTTPException(422, detail="job_id_required")
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, detail="job_not_found")
    if job.status != "open":
        raise HTTPException(409, detail="job_closed")
    candidate = _candidate(db, user.id)
    if db.scalar(select(Application.id).where(Application.candidate_id == candidate.id, Application.job_id == job.id)):
        raise HTTPException(409, detail="already_applied")
    resume_id = body.get("resume_id")
    if resume_id is not None:
        try:
            resume_id = int(resume_id)
        except (TypeError, ValueError):
            raise HTTPException(422, detail="invalid_resume")
        resume = db.get(Resume, resume_id)
        if resume is None or resume.candidate_id != candidate.id:
            raise HTTPException(422, detail="invalid_resume")
    score = None
    try:
        from app.ai.scorers import score_pair
        repo = SqlAIRepository(db)
        ci, ji = repo.candidate_input(candidate.id), repo.job_input(job.id)
        if ci and ji:
            score = score_pair("m3", ci, ji)["total_score"]
    except Exception:
        score = None
    app = Application(candidate_id=candidate.id, job_id=job.id, resume_id=resume_id, status="applied", match_score=score)
    db.add(app)
    try:
        db.flush()
        db.add(ApplicationStatusHistory(application_id=app.id, from_status=None, to_status="applied", changed_by=user.id, note="Nộp hồ sơ"))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, detail="already_applied")
    db.refresh(app)
    return _application_dto(db, app)


@router.get("/applications/me")
def my_applications(db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("candidate"))):
    candidate = _candidate(db, user.id)
    rows = db.scalars(select(Application).where(Application.candidate_id == candidate.id).order_by(Application.applied_at.desc()))
    return {"items": [_application_dto(db, row) for row in rows]}


def _owned_job(db: Session, job_id: int, user: CurrentUser) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, detail="job_not_found")
    if job.company_id != user.company_id:
        raise HTTPException(403, detail="not_your_job")
    return job


@router.get("/jobs/{job_id}/applications")
def job_applications(job_id: int, db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("recruiter"))):
    _owned_job(db, job_id, user)
    rows = db.execute(select(Application, Candidate, User).join(Candidate, Candidate.id == Application.candidate_id).outerjoin(User, User.id == Candidate.user_id).where(Application.job_id == job_id).order_by(Application.applied_at.desc())).all()
    return {"items": [{**_application_dto(db, app), "candidate": {"id": cand.id, "full_name": user.full_name if user else cand.full_name,
             "major": cand.major, "university": cand.university, "years_exp": cand.years_exp, "education_level": cand.education_level}} for app, cand, user in rows]}


@router.patch("/applications/{application_id}/status")
def change_status(application_id: int, body: dict[str, Any], db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("recruiter"))):
    app = db.get(Application, application_id)
    if app is None:
        raise HTTPException(404, detail="application_not_found")
    _owned_job(db, app.job_id, user)
    target = body.get("status")
    if target not in {"applied", "screening", "interview", "offer", "hired", "rejected"}:
        raise HTTPException(422, detail="invalid_status")
    if app.status in FINAL or (target != "rejected" and target != NEXT.get(app.status)):
        raise HTTPException(409, detail={"detail": "invalid_transition", "from": app.status, "to": target})
    previous = app.status
    app.status = target
    db.add(ApplicationStatusHistory(application_id=app.id, from_status=previous, to_status=target, changed_by=user.id, note=body.get("note")))
    db.commit()
    db.refresh(app)
    return _application_dto(db, app)
