"""Registration, login and current-account endpoints."""
from __future__ import annotations

from datetime import datetime, timedelta
import re

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.deps import CurrentUser, get_current_user, get_db
from app.models import Candidate, Company, Location, Recruiter, User

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str
    full_name: str = Field(min_length=2, max_length=200)
    company_name: str | None = Field(default=None, max_length=240)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


def _safe_email(email: str) -> str:
    value = email.strip().lower()
    domain = value.rsplit("@", 1)[-1]
    if domain.endswith((".test", ".example")):
        raise HTTPException(422, detail="invalid_email_domain")
    return value


def _token(user: User) -> str:
    expiry = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": str(user.id), "exp": expiry}, settings.jwt_secret, algorithm="HS256")


def _payload(user: User, company_id: int | None = None) -> dict:
    return {"id": user.id, "email": user.email, "role": user.role, "full_name": user.full_name, "company_id": company_id if company_id is not None else user.company_id}


@router.post("/register", status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = _safe_email(str(body.email))
    if len(body.password.encode("utf-8")) > 72:
        raise HTTPException(422, detail="password_too_long")
    if body.role not in {"candidate", "recruiter"}:
        raise HTTPException(422, detail="invalid_role")
    if body.role == "recruiter" and not body.company_name:
        raise HTTPException(422, detail="company_name_required")
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(409, detail="email_already_registered")
    company_id = None
    if body.role == "recruiter":
        loc = db.scalar(select(Location).where(Location.name == "Hà Nội"))
        if loc is None:
            loc = Location(name="Hà Nội", region="Miền Bắc")
            db.add(loc)
            db.flush()
        company = db.scalar(select(Company).where(Company.name == body.company_name.strip()))
        if company is None:
            company = Company(name=body.company_name.strip(), location_id=loc.id)
            db.add(company)
            db.flush()
        company_id = company.id
    user = User(email=email, password_hash=bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode(), role=body.role, full_name=body.full_name.strip(), company_id=company_id)
    db.add(user)
    db.flush()
    if body.role == "candidate":
        db.add(Candidate(user_id=user.id, full_name=user.full_name, profile_json={}))
    else:
        db.add(Recruiter(user_id=user.id, company_id=company_id))
    db.commit()
    db.refresh(user)
    return {"access_token": _token(user), "token_type": "bearer", "user": _payload(user, company_id)}


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    email = str(body.email).strip().lower()
    user = db.scalar(select(User).where(User.email == email, User.is_active.is_(True)))
    try:
        valid = user is not None and bcrypt.checkpw(body.password.encode(), user.password_hash.encode())
    except (ValueError, TypeError):
        valid = False
    if not valid or user is None:
        raise HTTPException(401, detail="invalid_credentials")
    return {"access_token": _token(user), "token_type": "bearer", "user": _payload(user)}


@router.get("/me")
def me(user: CurrentUser = Depends(get_current_user)):
    return _payload(User(id=user.id, email=user.email, role=user.role, full_name=user.full_name), user.company_id)
