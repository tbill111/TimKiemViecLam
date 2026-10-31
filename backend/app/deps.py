"""Dependency của FastAPI: phiên DB, người dùng hiện tại, kiểm tra vai trò.

Hợp đồng với router AI: `get_current_user()` trả đối tượng có `.id`, `.role`, `.company_id`;
`require_role(*roles)` trả dependency kiểm tra vai trò (403) và trả lại user.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import new_session
from .models import Candidate, Recruiter, User
from .security import decode_token

_bearer = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    id: int
    email: str
    role: str
    full_name: str
    company_id: Optional[int] = None
    candidate_id: Optional[int] = None


def get_db() -> Iterator[Session]:
    db = new_session()
    try:
        yield db
    finally:
        db.close()


def _load_user(db: Session, creds: Optional[HTTPAuthorizationCredentials]) -> Optional[CurrentUser]:
    if creds is None:
        return None
    uid = decode_token(creds.credentials)
    user = db.get(User, uid) if uid else None
    if user is None:
        return None
    company_id = candidate_id = None
    if user.role == "recruiter":
        company_id = db.scalar(select(Recruiter.company_id).where(Recruiter.user_id == user.id))
    elif user.role == "candidate":
        candidate_id = db.scalar(select(Candidate.id).where(Candidate.user_id == user.id))
    return CurrentUser(user.id, user.email, user.role, user.full_name, company_id, candidate_id)


def get_optional_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer), db: Session = Depends(get_db)
) -> Optional[CurrentUser]:
    return _load_user(db, creds)


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer), db: Session = Depends(get_db)
) -> CurrentUser:
    user = _load_user(db, creds)
    if user is None:
        raise HTTPException(401, detail="not_authenticated")
    return user


def require_role(*roles: str):
    def dep(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(403, detail="forbidden")
        return user

    return dep
