"""Idempotently load reference data, 300 candidates and ~1,200 simulated applications."""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from datetime import date, datetime
from pathlib import Path

import bcrypt
from sqlalchemy import select, text
from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(BACKEND_ROOT))

from app.ai.embedder import get_embedder
from app.models import (
    ApplicationStatusHistory, Candidate, CandidateSkill, Company, Job, JobSkill, Location,
    Recruiter, Resume, SavedJob, Skill, SkillAlias, User,
)
from app.db import SessionLocal
from seed.gen_applications import generate_applications
from seed.gen_candidates import export_csv, generate_profiles

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
LOCK_ID = 4815162342
DEMO_PASSWORD = "Demo@12345"
DEMO_EMAIL = "thanhtung.demo@smartcareer.vn"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Required seed CSV not found: {path}")
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def _split(value: str | None) -> list[str]:
    return [item.strip() for item in (value or "").split("|") if item.strip()]


def _date(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def _ensure(db: Session, model, condition, **values):
    row = db.scalar(select(model).where(condition))
    if row is None:
        row = model(**values)
        db.add(row)
        db.flush()
    return row


def _load_skill_aliases(
    db: Session,
    alias_rows: list[dict[str, str]],
    skill_by_name: dict[str, Skill],
) -> int:
    loaded = 0
    for row in alias_rows:
        alias = row.get("alias", "").strip()
        skill_name = row.get("skill_name", "").strip()
        if not alias or not skill_name:
            raise RuntimeError(f"Invalid skill alias row: {row}")
        skill = skill_by_name.get(skill_name.casefold())
        if skill is None:
            raise RuntimeError(f"Alias references unknown skill: {skill_name}")
        existing = db.scalar(select(SkillAlias).where(SkillAlias.alias == alias))
        if existing is None:
            db.add(SkillAlias(alias=alias, skill_id=skill.id))
            db.flush()
        elif existing.skill_id != skill.id:
            raise RuntimeError(
                f"Alias {alias!r} is already linked to a different skill."
            )
        loaded += 1
    return loaded


def _ensure_profile_resume(db: Session, candidate: Candidate, profile: dict) -> Resume:
    resume = db.scalar(
        select(Resume)
        .where(Resume.candidate_id == candidate.id, Resume.is_active.is_(True))
        .order_by(Resume.created_at.desc(), Resume.id.desc())
        .limit(1)
    )
    if resume is not None:
        return resume

    now = datetime.utcnow()
    candidate.consent_at = candidate.consent_at or now
    parsed_json = {
        "source": "synthetic_seed_profile",
        "skills": profile["skills"],
        "years_exp": profile["years_exp"],
        "education_level": profile["education_level"],
    }
    resume = Resume(
        candidate_id=candidate.id,
        filename=f"synthetic-{candidate.external_id}.txt",
        parsed_json=parsed_json,
        model_text=profile["text"],
        consent_at=candidate.consent_at,
        is_active=True,
    )
    db.add(resume)
    db.flush()
    return resume


def _drop_views(db: Session) -> None:
    for view in ("v_funnel_stages", "v_funnel", "v_salary", "v_skill_supply_demand"):
        db.execute(text(f"DROP VIEW IF EXISTS {view}"))


def _create_views(db: Session) -> None:
    path = ROOT.parent.parent / "bi" / "views.sql"
    sql = "\n".join(line for line in path.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("--"))
    for statement in sql.split(";"):
        if statement.strip():
            db.execute(text(statement.strip()))
    for view in ("v_skill_supply_demand", "v_salary", "v_funnel", "v_funnel_stages"):
        db.execute(text(f"GRANT SELECT ON {view} TO bi_reader"))


def _reset(db: Session) -> None:
    _drop_views(db)
    db.execute(text("TRUNCATE TABLE labeling_tasks, application_status_history, match_results, saved_jobs, applications, job_skills, jobs, candidate_skills, resumes, candidates, recruiters, skill_aliases, skills, users, companies, locations RESTART IDENTITY CASCADE"))


def _load(db: Session, reset: bool) -> tuple[int, int, int, list[dict]]:
    if reset:
        _reset(db)
    locations: dict[str, Location] = {}
    for name in ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Remote"] + [r.get("location", "") for r in read_csv(DATA / "companies.csv")] + [r.get("location", "") for r in read_csv(DATA / "jobs_seed.csv")]:
        name = name.strip()
        if name:
            locations[name] = _ensure(db, Location, Location.name == name, name=name, region="Remote" if name == "Remote" else None)

    skill_rows = read_csv(DATA / "skills.csv")
    if len(skill_rows) < 80:
        raise RuntimeError(f"skills.csv contains only {len(skill_rows)} rows; run python -m seed.generate_reference_data first")
    steps_by_name = {r["skill_name"].strip().casefold(): _split(r.get("steps")) for r in read_csv(DATA / "skill_learning_steps.csv")}
    skill_by_name: dict[str, Skill] = {}
    for row in skill_rows:
        name = row["name"].strip()
        skill = _ensure(db, Skill, Skill.name == name, name=name, category=row.get("category") or "Khác", learning_steps=steps_by_name.get(name.casefold(), []))
        skill.category = row.get("category") or skill.category
        if name.casefold() in steps_by_name:
            skill.learning_steps = steps_by_name[name.casefold()]
        skill_by_name[name.casefold()] = skill

    companies: dict[str, Company] = {}
    company_rows = read_csv(DATA / "companies.csv")
    if len(company_rows) < 30:
        raise RuntimeError(f"companies.csv contains only {len(company_rows)} rows; run python -m seed.generate_reference_data first")
    for row in company_rows:
        name = row["name"].strip()
        location_id = locations.get(row.get("location", ""), locations["Hà Nội"]).id
        company = _ensure(db, Company, Company.name == name, name=name, industry=row.get("industry") or "Công nghệ", size_range=row.get("size_range") or "10–50 nhân viên", location_id=location_id)
        company.industry, company.size_range, company.location_id = row.get("industry") or company.industry, row.get("size_range") or company.size_range, location_id
        companies[name] = company

    alias_rows = read_csv(DATA / "skill_aliases.csv")
    if len(alias_rows) < 150:
        raise RuntimeError(f"skill_aliases.csv contains only {len(alias_rows)} rows; run python -m seed.generate_reference_data first")
    _load_skill_aliases(db, alias_rows, skill_by_name)

    digest = bcrypt.hashpw(DEMO_PASSWORD.encode(), bcrypt.gensalt()).decode()
    admin = _ensure(db, User, User.email == "admin@smartcareer.vn", email="admin@smartcareer.vn", password_hash=digest, role="admin", full_name="Quản trị SmartCareer")
    admin.password_hash, admin.role = digest, "admin"
    recruiters_by_company = {}
    for index, company in enumerate(companies.values(), start=1):
        email = f"hr{index}@smartcareer.vn"
        user = _ensure(db, User, User.email == email, email=email, password_hash=digest, role="recruiter", full_name=f"Nhân sự {company.name}", company_id=company.id)
        user.password_hash, user.company_id = digest, company.id
        rec = _ensure(db, Recruiter, Recruiter.user_id == user.id, user_id=user.id, company_id=company.id)
        rec.company_id = company.id
        recruiters_by_company[company.id] = user.id

    profiles = generate_profiles(300)
    demo_user = _ensure(db, User, User.email == DEMO_EMAIL, email=DEMO_EMAIL, password_hash=digest, role="candidate", full_name="Giang Thanh Tùng")
    demo_user.password_hash, demo_user.full_name = digest, "Giang Thanh Tùng"

    jobs_by_external: dict[str, Job] = {}
    job_rows = read_csv(DATA / "jobs_seed.csv")
    if len(job_rows) < 150:
        raise RuntimeError(f"jobs_seed.csv contains only {len(job_rows)} rows; run python -m seed.generate_reference_data first")
    for row in job_rows:
        external_id = row["external_id"].strip()
        company = companies.get(row["company_name"].strip())
        if company is None:
            raise RuntimeError(f"Job references unknown company {row['company_name']}")
        loc = locations.get(row["location"].strip()) or _ensure(db, Location, Location.name == row["location"].strip(), name=row["location"].strip())
        posted_at = _date(row.get("posted_at")) or datetime.utcnow()
        job = _ensure(db, Job, Job.external_id == external_id, external_id=external_id, company_id=company.id, recruiter_id=recruiters_by_company[company.id], title=row["title"], category=row["category"], level=row["level"], job_type=row["job_type"], work_mode=row["work_mode"], location_id=loc.id)
        job.company_id, job.recruiter_id, job.title, job.category = company.id, recruiters_by_company[company.id], row["title"], row["category"]
        job.level, job.job_type, job.work_mode, job.location_id = row["level"], row["job_type"], row["work_mode"], loc.id
        job.salary_min = float(row["salary_min"]) if row.get("salary_min") else None
        job.salary_max = float(row["salary_max"]) if row.get("salary_max") else None
        job.min_years_exp = float(row.get("min_years_exp") or 0)
        job.min_education = int(row.get("min_education") or 0)
        job.posted_at, job.deadline = posted_at, _date(row.get("deadline"))
        job.description = row.get("description") or ""
        job.responsibilities = _split(row.get("responsibilities"))
        job.status = "open"
        db.flush()
        db.execute(JobSkill.__table__.delete().where(JobSkill.job_id == job.id))
        for priority, column in (("required", "required_skills"), ("preferred", "preferred_skills")):
            for skill_name in _split(row.get(column)):
                skill = skill_by_name.get(skill_name.casefold())
                if skill is None:
                    raise RuntimeError(f"Job {external_id} has unknown skill {skill_name}")
                db.add(JobSkill(job_id=job.id, skill_id=skill.id, priority=priority))
        jobs_by_external[external_id] = job

    # Embeddings are computed in batches before any match scoring is performed.
    candidates_by_external: dict[str, Candidate] = {}
    candidate_texts: list[str] = []
    candidate_rows: list[Candidate] = []
    for profile_index, profile in enumerate(profiles):
        profile_json = profile["profile_json"]
        is_demo = profile["candidate_id"] == "cand-demo-001"
        candidate = _ensure(db, Candidate, Candidate.external_id == profile["candidate_id"], external_id=profile["candidate_id"], user_id=demo_user.id if is_demo else None, full_name=profile_json["fullName"])
        candidate.user_id = demo_user.id if is_demo else None
        candidate.full_name = profile_json["fullName"]
        candidate.university, candidate.major = profile_json["university"], profile_json["major"]
        candidate.years_exp, candidate.education_level = float(profile["years_exp"]), int(profile["education_level"])
        candidate.location_id = locations[profile["locations"][0]].id
        candidate.expected_salary_min, candidate.expected_salary_max = profile["expected_salary_min"], profile["expected_salary_max"]
        profile_json["cvFile"] = profile.get("cv_file")
        candidate.profile_json = profile_json
        if profile.get("cv_file"):
            cv_path = ROOT / str(profile["cv_file"])
            if not cv_path.is_file():
                cv_path = ROOT / "cv_files" / str(profile["cv_file"])
            if cv_path.is_file() and candidate.consent_at is None:
                from app.ai.parser import parse_cv
                from app.ai.skills import SkillIndex
                skill_rows = [(skill.name, skill.category) for skill in skill_by_name.values()]
                skill_by_id = {skill.id: skill for skill in skill_by_name.values()}
                alias_pairs = [(row.alias, skill_by_id[row.skill_id].name) for row in db.scalars(select(SkillAlias)) if row.skill_id in skill_by_id]
                parsed = parse_cv(cv_path.read_bytes(), cv_path.name, SkillIndex.from_rows(skill_rows, alias_pairs))
                now = datetime.utcnow()
                candidate.consent_at = now
                db.add(Resume(candidate_id=candidate.id, filename=cv_path.name, parsed_json={k: v for k, v in parsed.items() if k != "embedding"}, model_text=parsed["model_text"], embedding=parsed["embedding"], consent_at=now))
                candidate.years_exp = parsed["years_exp"]
                candidate.education_level = parsed["education_level"]
                profile_skill_ids = {row.skill_id for row in db.scalars(select(CandidateSkill).where(CandidateSkill.candidate_id == candidate.id))}
                for hit in parsed["skills"]:
                    skill = skill_by_name.get(hit["name"].casefold())
                    if skill and skill.id not in profile_skill_ids:
                        db.add(CandidateSkill(candidate_id=candidate.id, skill_id=skill.id, source="cv", confirmed=False))
        db.flush()
        existing = {row.skill_id: row for row in db.scalars(select(CandidateSkill).where(CandidateSkill.candidate_id == candidate.id))}
        for row in existing.values():
            db.delete(row)
        seen_skill_ids: set[int] = set()
        for name in profile["skills"]:
            # Tên có đuôi " cơ bản" là tên chuẩn của một số kỹ năng: ưu tiên khớp nguyên tên rồi mới cắt đuôi.
            skill = skill_by_name.get(name.casefold()) or skill_by_name.get(name.removesuffix(" cơ bản").casefold())
            if skill and skill.id not in seen_skill_ids:
                seen_skill_ids.add(skill.id)
                db.add(CandidateSkill(candidate_id=candidate.id, skill_id=skill.id, source="profile", confirmed=True))
        candidates_by_external[profile["candidate_id"]] = candidate
        candidate_rows.append(candidate)
        latest = db.scalar(select(Resume).where(Resume.candidate_id == candidate.id, Resume.is_active.is_(True)).order_by(Resume.created_at.desc()).limit(1))
        if profile_index < 50 and latest is None:
            latest = _ensure_profile_resume(db, candidate, profile)
        candidate_texts.append(latest.model_text if latest and latest.model_text else profile["text"] + "\n" + " ".join(profile["skills"]))

    db.flush()
    embedder = get_embedder()
    job_list = list(jobs_by_external.values())
    job_texts = []
    for job in job_list:
        skills = db.execute(select(Skill.name).join(JobSkill, JobSkill.skill_id == Skill.id).where(JobSkill.job_id == job.id)).scalars().all()
        job_texts.append(" ".join([job.title, job.description, " ".join(job.responsibilities or []), *skills]))
    job_vectors = embedder.encode(job_texts)
    candidate_vectors = embedder.encode(candidate_texts)
    for row, vector in zip(job_list, job_vectors):
        row.embedding = vector.astype("float32").tobytes()
    for row, vector in zip(candidate_rows, candidate_vectors):
        row.embedding = vector.astype("float32").tobytes()

    db.flush()
    generated_apps = generate_applications(db, 1200, 42)
    if reset:
        _create_views(db)
    return len(skill_rows), len(alias_rows), len(profiles), generated_apps, profiles


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="drop BI views and replace all seeded rows in one transaction")
    args = parser.parse_args()
    result = None
    with SessionLocal() as db:
        try:
            with db.begin():
                db.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": LOCK_ID})
                result = _load(db, args.reset)
        except Exception:
            db.rollback()
            raise
    # Do not leave a generated export if the transaction failed.
    if result is not None:
        export_csv(result[4])
        print(f"Seed ready: skills={result[0]}, aliases={result[1]}, candidates={result[2]}, new_applications={result[3]}; outputs are simulated demo data.")


if __name__ == "__main__":
    main()
