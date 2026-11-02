"""FastAPI database and authentication dependencies."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.models import Recruiter, User

bearer = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    id: int
    email: str
    role: str
    full_name: str
    company_id: int | None = None


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, detail="not_authenticated", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise HTTPException(401, detail="invalid_token", headers={"WWW-Authenticate": "Bearer"})
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(401, detail="not_authenticated", headers={"WWW-Authenticate": "Bearer"})
    company_id = user.company_id
    if user.role == "recruiter" and company_id is None:
        company_id = db.scalar(select(Recruiter.company_id).where(Recruiter.user_id == user.id))
    return CurrentUser(user.id, user.email, user.role, user.full_name, company_id)


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> CurrentUser | None:
    if credentials is None:
        return None
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        return None
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        return None
    company_id = user.company_id
    if user.role == "recruiter" and company_id is None:
        company_id = db.scalar(select(Recruiter.company_id).where(Recruiter.user_id == user.id))
    return CurrentUser(user.id, user.email, user.role, user.full_name, company_id)


def require_role(*roles: str):
    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(403, detail="forbidden")
        return user

    return dependency
