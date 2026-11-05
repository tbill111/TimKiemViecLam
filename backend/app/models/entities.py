"""The 15-table relational model used by the API, seed loader and BI views."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")
PK = BigInteger().with_variant(Integer, "sqlite")


class Location(Base):
    __tablename__ = "locations"
    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    region: Mapped[str | None] = mapped_column(String(120))


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(240), unique=True, nullable=False)
    industry: Mapped[str] = mapped_column(String(160), default="Công nghệ", nullable=False)
    size_range: Mapped[str] = mapped_column(String(80), default="10–50 nhân viên", nullable=False)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    __table_args__ = (CheckConstraint("role IN ('admin','recruiter','candidate')", name="ck_users_role"),)


class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(80), default="Khác", nullable=False)
    learning_steps: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class SkillAlias(Base):
    __tablename__ = "skill_aliases"
    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    alias: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)


class Candidate(Base):
    __tablename__ = "candidates"
    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(80), unique=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    university: Mapped[str] = mapped_column(String(240), default="", nullable=False)
    major: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    years_exp: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    education_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id", ondelete="SET NULL"))
    expected_salary_min: Mapped[float | None] = mapped_column(Numeric(10, 2))
    expected_salary_max: Mapped[float | None] = mapped_column(Numeric(10, 2))
    profile_json: Mapped[dict] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary)
    consent_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    __table_args__ = (
        CheckConstraint("education_level BETWEEN 0 AND 4", name="ck_candidates_education_level"),
        CheckConstraint("expected_salary_min IS NULL OR expected_salary_max IS NULL OR expected_salary_min <= expected_salary_max", name="ck_candidates_salary_range"),
    )


class Resume(Base):
    __tablename__ = "resumes"
    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    parsed_json: Mapped[dict] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    model_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary)
    consent_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="profile", nullable=False)
    confirmed: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    __table_args__ = (UniqueConstraint("candidate_id", "skill_id", name="uq_candidate_skills"), CheckConstraint("source IN ('profile','cv','manual')", name="ck_candidate_skills_source"))


class Recruiter(Base):
    __tablename__ = "recruiters"
    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(120), default="Recruiter", nullable=False)


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(80), unique=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    recruiter_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    category: Mapped[str] = mapped_column(String(80), default="Software Engineering", nullable=False)
    level: Mapped[str] = mapped_column(String(20), default="fresher", nullable=False)
    job_type: Mapped[str] = mapped_column(String(20), default="full_time", nullable=False)
    work_mode: Mapped[str] = mapped_column(String(20), default="onsite", nullable=False)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id", ondelete="SET NULL"))
    salary_min: Mapped[float | None] = mapped_column(Numeric(10, 2))
    salary_max: Mapped[float | None] = mapped_column(Numeric(10, 2))
    min_years_exp: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    min_education: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    posted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    deadline: Mapped[datetime | None] = mapped_column(DateTime)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    responsibilities: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    __table_args__ = (
        CheckConstraint("status IN ('open','closed')", name="ck_jobs_status"),
        CheckConstraint("level IN ('intern','fresher','junior','middle','senior')", name="ck_jobs_level"),
        CheckConstraint("job_type IN ('full_time','part_time','internship')", name="ck_jobs_type"),
        CheckConstraint("work_mode IN ('onsite','hybrid','remote')", name="ck_jobs_work_mode"),
        CheckConstraint("salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max", name="ck_jobs_salary_range"),
        CheckConstraint("min_education BETWEEN 0 AND 4", name="ck_jobs_education"),
        Index("ix_jobs_status_posted", "status", "posted_at"),
    )


class JobSkill(Base):
    __tablename__ = "job_skills"
    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    __table_args__ = (UniqueConstraint("job_id", "skill_id", name="uq_job_skills"), CheckConstraint("priority IN ('required','preferred')", name="ck_job_skills_priority"))


class Application(Base):
    __tablename__ = "applications"
    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(20), default="applied", nullable=False)
    match_score: Mapped[int | None] = mapped_column(Integer)
    applied_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint("candidate_id", "job_id", name="uq_applications_candidate_job"),
        CheckConstraint("status IN ('applied','screening','interview','offer','hired','rejected')", name="ck_applications_status"),
        CheckConstraint("match_score IS NULL OR match_score BETWEEN 0 AND 100", name="ck_applications_match_score"),
    )


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"
    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    note: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    __table_args__ = (
        CheckConstraint("from_status IS NULL OR from_status IN ('applied','screening','interview','offer','hired','rejected')", name="ck_application_history_from"),
        CheckConstraint("to_status IN ('applied','screening','interview','offer','hired','rejected')", name="ck_application_history_to"),
    )


class MatchResult(Base):
    __tablename__ = "match_results"
    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    model: Mapped[str] = mapped_column(String(10), nullable=False)
    model_version: Mapped[str] = mapped_column(String(80), nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False)
    result_json: Mapped[dict] = mapped_column(JSON_TYPE, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint("candidate_id", "job_id", "model_version", name="uq_match_results_version"),
        CheckConstraint("total_score BETWEEN 0 AND 100", name="ck_match_results_score"),
        CheckConstraint("model IN ('m0','m1','m2','m3','m4')", name="ck_match_results_model"),
    )


class LabelingTask(Base):
    __tablename__ = "labeling_tasks"
    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    matching_score: Mapped[int | None] = mapped_column(Integer)
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str | None] = mapped_column(String(20))
    model: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    __table_args__ = (
        UniqueConstraint("resume_id", "job_id", name="uq_labeling_tasks_resume_job"),
        CheckConstraint("matching_score IS NULL OR matching_score BETWEEN 0 AND 100", name="ck_labeling_tasks_matching_score"),
        CheckConstraint("status IN ('pending','completed','failed')", name="ck_labeling_tasks_status"),
    )


class SavedJob(Base):
    __tablename__ = "saved_jobs"
    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    saved_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    __table_args__ = (UniqueConstraint("candidate_id", "job_id", name="uq_saved_jobs_candidate_job"),)
