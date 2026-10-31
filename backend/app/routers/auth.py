from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import CurrentUser, get_current_user, get_db
from app.models import Candidate, Company, Recruiter, User
from app.security import create_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role: Literal["candidate", "recruiter"]
    full_name: str = Field(min_length=1, max_length=255)
    company_name: Optional[str] = Field(default=None, max_length=255)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


def user_payload(u: CurrentUser | User, company_id: Optional[int] = None) -> dict:
    return {
        "id": u.id,
        "email": u.email,
        "role": u.role,
        "full_name": u.full_name,
        "company_id": getattr(u, "company_id", None) if isinstance(u, CurrentUser) else company_id,
    }


@router.post("/register", status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User.id).where(User.email == body.email.lower())):
        raise HTTPException(409, detail="email_taken")
    if body.role == "recruiter" and not (body.company_name or "").strip():
        raise HTTPException(422, detail="company_name_required")
    user = User(email=body.email.lower(), password_hash=hash_password(body.password), role=body.role, full_name=body.full_name.strip())
    db.add(user)
    db.flush()
    company_id: Optional[int] = None
    if body.role == "candidate":
        db.add(Candidate(user_id=user.id, full_name=user.full_name, profile_json={}))
    else:
        name = body.company_name.strip()  # type: ignore[union-attr]
        company = db.scalar(select(Company).where(Company.name == name)) or Company(name=name, verified=False)
        db.add(company)
        db.flush()
        company_id = company.id
        db.add(Recruiter(user_id=user.id, company_id=company.id, position="HR"))
    db.commit()
    return {"access_token": create_token(user.id, user.role), "token_type": "bearer", "user": user_payload(user, company_id)}


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, detail="invalid_credentials")
    company_id = db.scalar(select(Recruiter.company_id).where(Recruiter.user_id == user.id)) if user.role == "recruiter" else None
    return {"access_token": create_token(user.id, user.role), "token_type": "bearer", "user": user_payload(user, company_id)}


@router.get("/me")
def me(user: CurrentUser = Depends(get_current_user)):
    return user_payload(user)
