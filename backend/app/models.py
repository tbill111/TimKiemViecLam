"""15 bảng của CSDL tác nghiệp (xem docs/00_KE_HOACH_KY_THUAT_TH3.md mục 3.1).

Dùng kiểu JSON chung (JSONB trên PostgreSQL) và LargeBinary (BYTEA) để chạy được cả trên SQLite khi test.
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

Json = JSON().with_variant(JSONB(), "postgresql")

ROLES = ("candidate", "recruiter", "admin")
LEVELS = ("intern", "fresher", "junior", "middle", "senior")
JOB_TYPES = ("full_time", "part_time", "internship")
WORK_MODES = ("onsite", "hybrid", "remote")
JOB_STATUSES = ("open", "closed")
APP_STATUSES = ("applied", "screening", "interview", "offer", "hired", "rejected")


def _in(col: str, values: tuple[str, ...]) -> str:
    return f"{col} IN ({', '.join(repr(v) for v in values)})"


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint(_in("role", ROLES), name="ck_users_role"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    region: Mapped[str] = mapped_column(String(50), default="")


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="")
    learning_steps: Mapped[Optional[list[str]]] = mapped_column(Json, nullable=True)


class SkillAlias(Base):
    __tablename__ = "skill_aliases"

    alias: Mapped[str] = mapped_column(String(100), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    industry: Mapped[str] = mapped_column(String(100), default="")
    size_range: Mapped[str] = mapped_column(String(50), default="")
    location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("locations.id"), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("locations.id"), nullable=True)
    years_exp: Mapped[float] = mapped_column(Numeric(3, 1), default=0)
    education_level: Mapped[int] = mapped_column(Integer, default=0)
    major: Mapped[str] = mapped_column(String(255), default="")
    expected_salary_min: Mapped[Optional[float]] = mapped_column(Numeric(6, 1), nullable=True)
    expected_salary_max: Mapped[Optional[float]] = mapped_column(Numeric(6, 1), nullable=True)
    work_mode: Mapped[str] = mapped_column(String(20), default="")
    consent_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime, nullable=True)
    # Phần giàu cấu trúc của StudentProfile: university, year, careerGoal, languages, projects, experience,
    # certificates, githubUrl, linkedinUrl, preferredLocations, preferredWorkTypes
    profile_json: Mapped[dict[str, Any]] = mapped_column(Json, default=dict)
    # Embedding của văn bản hồ sơ (kỹ năng, mục tiêu, dự án), tính khi lưu hồ sơ để chấm điểm không phải mã hoá lúc yêu cầu;
    # khi có CV đang dùng thì dùng embedding của CV.
    embedding: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)

    user: Mapped[User] = relationship()


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), default="")
    file_path: Mapped[str] = mapped_column(String(500), default="")
    raw_text: Mapped[str] = mapped_column(Text, default="")
    parsed_json: Mapped[dict[str, Any]] = mapped_column(Json, default=dict)
    embedding: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    uploaded_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    __table_args__ = (CheckConstraint(_in("source", ("cv", "manual")), name="ck_candidate_skills_source"),)

    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    source: Mapped[str] = mapped_column(String(10), default="manual")
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)


class Recruiter(Base):
    __tablename__ = "recruiters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    position: Mapped[str] = mapped_column(String(100), default="")


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint(_in("level", LEVELS), name="ck_jobs_level"),
        CheckConstraint(_in("job_type", JOB_TYPES), name="ck_jobs_job_type"),
        CheckConstraint(_in("work_mode", WORK_MODES), name="ck_jobs_work_mode"),
        CheckConstraint(_in("status", JOB_STATUSES), name="ck_jobs_status"),
        CheckConstraint("salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max", name="ck_jobs_salary"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    recruiter_id: Mapped[Optional[int]] = mapped_column(ForeignKey("recruiters.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    responsibilities: Mapped[list[str]] = mapped_column(Json, default=list)
    category: Mapped[str] = mapped_column(String(60), default="")
    level: Mapped[str] = mapped_column(String(20), default="fresher")
    job_type: Mapped[str] = mapped_column(String(20), default="full_time")
    work_mode: Mapped[str] = mapped_column(String(20), default="onsite")
    location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("locations.id"), nullable=True)
    salary_min: Mapped[Optional[float]] = mapped_column(Numeric(6, 1), nullable=True)  # triệu VNĐ/tháng
    salary_max: Mapped[Optional[float]] = mapped_column(Numeric(6, 1), nullable=True)
    min_years_exp: Mapped[float] = mapped_column(Numeric(3, 1), default=0)
    min_education: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(10), default="open", index=True)
    posted_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    deadline: Mapped[Optional[dt.datetime]] = mapped_column(DateTime, nullable=True)
    embedding: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)

    company: Mapped[Company] = relationship()
    location: Mapped[Optional[Location]] = relationship()


class JobSkill(Base):
    __tablename__ = "job_skills"

    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True, index=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("candidate_id", "job_id", name="uq_applications_candidate_job"),
        CheckConstraint(_in("status", APP_STATUSES), name="ck_applications_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id: Mapped[Optional[int]] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)
    match_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(15), default="applied")
    applied_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)

    candidate: Mapped[Candidate] = relationship()
    job: Mapped[Job] = relationship()


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    to_status: Mapped[str] = mapped_column(String(15), nullable=False)
    changed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    changed_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
    note: Mapped[str] = mapped_column(Text, default="")


class MatchResult(Base):
    __tablename__ = "match_results"

    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    model_version: Mapped[str] = mapped_column(String(60), primary_key=True)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False)
    skill_req_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    skill_pref_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    semantic_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    exp_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    edu_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    location_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    matched_skills: Mapped[list[str]] = mapped_column(Json, default=list)
    missing_skills: Mapped[list[str]] = mapped_column(Json, default=list)
    computed_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)


class SavedJob(Base):
    __tablename__ = "saved_jobs"

    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    saved_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow)
