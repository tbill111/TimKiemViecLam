"""Candidate saved-job endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import CurrentUser, get_db, require_role
from app.models import Candidate, Job, SavedJob

router = APIRouter(prefix="/saved-jobs", tags=["saved-jobs"])


def _candidate(db: Session, user_id: int) -> Candidate:
    row = db.scalar(select(Candidate).where(Candidate.user_id == user_id))
    if row is None:
        raise HTTPException(404, detail="candidate_profile_not_found")
    return row


def _save(db: Session, candidate: Candidate, job_id: int):
    if db.get(Job, job_id) is None:
        raise HTTPException(404, detail="job_not_found")
    row = db.scalar(select(SavedJob).where(SavedJob.candidate_id == candidate.id, SavedJob.job_id == job_id))
    if row is None:
        row = SavedJob(candidate_id=candidate.id, job_id=job_id)
        db.add(row)
        db.commit()
    return {"job_id": str(row.job_id), "saved_at": row.saved_at.isoformat() + "Z" if row.saved_at else None}


@router.post("")
def save_body(body: dict, db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("candidate"))):
    try:
        job_id = int(body["job_id"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(422, detail="job_id_required")
    return _save(db, _candidate(db, user.id), job_id)


@router.post("/{job_id}")
def save(job_id: int, db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("candidate"))):
    return _save(db, _candidate(db, user.id), job_id)


@router.delete("")
def remove_body(body: dict | None = None, job_id: int | None = None, db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("candidate"))):
    target = job_id or (body or {}).get("job_id")
    if target is None:
        raise HTTPException(422, detail="job_id_required")
    return _remove(db, _candidate(db, user.id), int(target))


@router.delete("/{job_id}", status_code=204)
def remove(job_id: int, db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("candidate"))):
    _remove(db, _candidate(db, user.id), job_id)


def _remove(db: Session, candidate: Candidate, job_id: int):
    row = db.scalar(select(SavedJob).where(SavedJob.candidate_id == candidate.id, SavedJob.job_id == job_id))
    if row:
        db.delete(row)
        db.commit()
    return None


@router.get("")
def list_saved(db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("candidate"))):
    candidate = _candidate(db, user.id)
    rows = db.scalars(select(SavedJob).where(SavedJob.candidate_id == candidate.id).order_by(SavedJob.saved_at.desc()))
    return {"items": [{"job_id": str(row.job_id), "saved_at": row.saved_at.isoformat() + "Z"} for row in rows]}
