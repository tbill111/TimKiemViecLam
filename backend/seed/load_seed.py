"""Nạp toàn bộ dữ liệu seed vào CSDL (chạy lặp lại không nhân đôi dữ liệu).

    cd backend && python -m seed.load_seed [--reset] [--no-applications]

Tài khoản demo (mật khẩu chung `Demo@12345`, đổi bằng biến SEED_PASSWORD):
    admin@smartcareer.vn            quản trị
    hr01@smartcareer.vn … hr30@…    mỗi công ty một nhà tuyển dụng (hr01 = Sao Mai Software)
    tung.demo@smartcareer.vn        ứng viên demo (hồ sơ của Giang Thanh Tùng như frontend)
    cand0001@example.edu.vn …         300 ứng viên sinh tự động
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import random
from pathlib import Path
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app import db as dbmod
from app.ai.embedder import get_embedder, to_bytes
from app.ai.parser import parse_cv
from app.ai.skills import SkillIndex
from app.models import (
    Base, Candidate, CandidateSkill, Company, Job, JobSkill, Location, Recruiter, Resume, Skill, SkillAlias, User,
)
from app.security import hash_password
from app.services.jobs import job_text
from app.services.skills import SkillResolver

from .catalog import LOCATIONS

DATA = Path(__file__).resolve().parent / "data"
CV_DIR = Path(__file__).resolve().parent / "cv_files"
SEED_NOW = dt.datetime(2026, 10, 31, 12, 0, 0)  # "hôm nay" của dữ liệu demo (cùng DEMO_NOW của frontend, cộng 9 ngày)
PASSWORD = os.getenv("SEED_PASSWORD", "Demo@12345")


def rows(name: str) -> list[dict[str, str]]:
    with open(DATA / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def split(value: str) -> list[str]:
    return [x for x in (value or "").split("|") if x]


def num(value: str) -> float | None:
    return float(value) if (value or "").strip() else None


def is_seeded(db: Session) -> bool:
    return db.scalar(select(Job.id).limit(1)) is not None


def reset(db: Session) -> None:
    from app.bi_sql import apply_views, drop_views

    engine = db.get_bind()
    db.close()
    with engine.begin() as conn:
        drop_views(conn)  # PostgreSQL: view phụ thuộc bảng nên phải xoá trước
        Base.metadata.drop_all(conn)
        Base.metadata.create_all(conn)
        apply_views(conn)


def get_location(db: Session, cache: dict[str, Location], name: str) -> Location:
    if name not in cache:
        cache[name] = Location(name=name, region="")
        db.add(cache[name])
        db.flush()
    return cache[name]


def load_catalog(db: Session) -> dict[str, Skill]:
    skills: dict[str, Skill] = {}
    steps = {r["skill_name"]: split(r["steps"]) for r in rows("skill_learning_steps.csv")}
    for r in rows("skills.csv"):
        skills[r["name"]] = Skill(name=r["name"], category=r["category"], learning_steps=steps.get(r["name"]))
    db.add_all(skills.values())
    db.flush()
    db.add_all([SkillAlias(alias=r["alias"].lower(), skill_id=skills[r["skill_name"]].id) for r in rows("skill_aliases.csv")])
    db.flush()
    return skills


def load_companies_and_jobs(db: Session, skills: dict[str, Skill], locs: dict[str, Location], pw_hash: str) -> dict[str, Recruiter]:
    companies: dict[str, Company] = {}
    recruiters: dict[str, Recruiter] = {}
    for i, r in enumerate(rows("companies.csv"), start=1):
        c = Company(name=r["name"], industry=r["industry"], size_range=r["size_range"], location_id=get_location(db, locs, r["location"]).id, verified=True)
        db.add(c)
        db.flush()
        companies[c.name] = c
        user = User(email=f"hr{i:02d}@smartcareer.vn", password_hash=pw_hash, role="recruiter", full_name=f"HR {c.name}")
        db.add(user)
        db.flush()
        rec = Recruiter(user_id=user.id, company_id=c.id, position="Trưởng bộ phận tuyển dụng")
        db.add(rec)
        db.flush()
        recruiters[c.name] = rec

    job_rows = rows("jobs.csv")
    jobs: list[tuple[Job, list[str], list[str]]] = []
    for r in job_rows:
        c = companies[r["company_name"]]
        job = Job(
            external_id=r["external_id"], company_id=c.id, recruiter_id=recruiters[c.name].id, title=r["title"], description=r["description"],
            responsibilities=split(r["responsibilities"]), category=r["category"], level=r["level"], job_type=r["job_type"], work_mode=r["work_mode"],
            location_id=get_location(db, locs, r["location"]).id, salary_min=num(r["salary_min"]), salary_max=num(r["salary_max"]),
            min_years_exp=num(r["min_years_exp"]) or 0, min_education=int(num(r["min_education"]) or 0), status="open",
            posted_at=dt.datetime.fromisoformat(r["posted_at"]), deadline=dt.datetime.fromisoformat(r["deadline"]),
        )
        db.add(job)
        jobs.append((job, split(r["required_skills"]), split(r["preferred_skills"])))
    db.flush()
    for job, req, pref in jobs:
        db.add_all([JobSkill(job_id=job.id, skill_id=skills[s].id, is_required=True) for s in req])
        db.add_all([JobSkill(job_id=job.id, skill_id=skills[s].id, is_required=False) for s in pref if s not in req])
    embs = get_embedder().encode([job_text(j, req, pref) for j, req, pref in jobs])
    for (job, _, _), vec in zip(jobs, embs):
        job.embedding = to_bytes(vec)
    db.flush()
    return recruiters


def add_candidate(db: Session, skills: dict[str, Skill], locs: dict[str, Location], user: User, *, external_id: str | None, full_name: str,
                  phone: str, years: float, edu: int, major: str, sal: tuple[float | None, float | None], profile: dict[str, Any],
                  skill_names: list[str]) -> Candidate:
    cand = Candidate(
        user_id=user.id, external_id=external_id, full_name=full_name, phone=phone, years_exp=years, education_level=edu, major=major,
        expected_salary_min=sal[0], expected_salary_max=sal[1], consent_at=SEED_NOW, profile_json=profile,
        location_id=get_location(db, locs, profile["preferredLocations"][0]).id if profile.get("preferredLocations") else None,
    )
    db.add(cand)
    db.flush()
    resolver = SkillResolver(db)
    for s in resolver.resolve_many(skill_names):
        db.add(CandidateSkill(candidate_id=cand.id, skill_id=s.id, source="manual", confirmed=True))
    return cand


def load_candidates(db: Session, skills: dict[str, Skill], locs: dict[str, Location], pw_hash: str, with_cv: bool = True) -> int:
    legacy = json.loads((DATA / "legacy_jobs.json").read_text(encoding="utf-8"))
    demo = legacy["demoProfile"]
    user = User(email="tung.demo@smartcareer.vn", password_hash=pw_hash, role="candidate", full_name=demo["fullName"])
    db.add(user)
    db.flush()
    profile = {k: demo.get(k) for k in ("university", "year", "githubUrl", "linkedinUrl", "careerGoal", "preferredLocations", "preferredWorkTypes",
                                        "languages", "projects", "experience", "certificates")}
    add_candidate(db, skills, locs, user, external_id="cand-demo", full_name=demo["fullName"], phone=demo.get("phone", ""), years=0.5, edu=3,
                  major=demo["major"], sal=(None, None), profile=profile, skill_names=demo["skills"])

    index = SkillIndex.from_rows([(s.name, s.category) for s in skills.values()],
                                 [(a.alias, next(n for n, s in skills.items() if s.id == a.skill_id)) for a in db.scalars(select(SkillAlias))])
    manifest = {r["candidate_id"]: r["cv_file"] for r in rows("cv_manifest.csv")} if with_cv and (DATA / "cv_manifest.csv").exists() else {}
    count = 0
    for i, r in enumerate(rows("candidates_generated.csv"), start=1):
        u = User(email=f"cand{i:04d}@example.edu.vn", password_hash=pw_hash, role="candidate", full_name=r["full_name"])
        db.add(u)
        db.flush()
        profile = {
            "university": r["university"], "year": r["year"], "careerGoal": r["career_goal"], "githubUrl": "", "linkedinUrl": "",
            "preferredLocations": split(r["locations"]), "preferredWorkTypes": split(r["work_types"]), "languages": ["Tiếng Việt", "Tiếng Anh"],
            "projects": [], "experience": [], "certificates": [],
        }
        cand = add_candidate(db, skills, locs, u, external_id=r["candidate_id"], full_name=r["full_name"], phone=r["phone"], years=float(r["years_exp"]),
                             edu=int(r["education_level"]), major=r["major"], sal=(num(r["expected_salary_min"]), num(r["expected_salary_max"])),
                             profile=profile, skill_names=split(r["skills"]))
        cv_file = manifest.get(r["candidate_id"])
        if cv_file and (CV_DIR / cv_file).exists():
            parsed = parse_cv((CV_DIR / cv_file).read_bytes(), cv_file, index=index)
            db.add(Resume(candidate_id=cand.id, filename=cv_file, file_path=f"seed/cv_files/{cv_file}", raw_text=parsed["text"],
                          parsed_json={k: v for k, v in parsed.items() if k != "embedding"}, embedding=parsed["embedding"], is_active=True))
        count += 1
    db.flush()
    _embed_candidates(db)
    return count


def _embed_candidates(db: Session) -> None:
    """Embedding hồ sơ tính theo lô một lần (như khi người dùng lưu hồ sơ)."""
    from app.services.ai_repo import profile_text

    cands = list(db.scalars(select(Candidate)))
    names: dict[int, list[str]] = {c.id: [] for c in cands}
    for cid, name in db.execute(select(CandidateSkill.candidate_id, Skill.name).join(Skill, Skill.id == CandidateSkill.skill_id).order_by(Skill.id)):
        names[cid].append(name)
    vecs = get_embedder().encode([profile_text(c, names[c.id]) for c in cands])
    for c, v in zip(cands, vecs):
        c.embedding = to_bytes(v)


def seed(db: Session, applications: bool = True, with_cv: bool = True, rng_seed: int = 42) -> dict[str, int]:
    """Nạp toàn bộ dữ liệu trong MỘT giao dịch: lỗi giữa chừng thì không để lại dữ liệu nửa vời
    (nếu để lại, lần khởi động sau sẽ thấy "đã có dữ liệu" và không bao giờ sinh đơn ứng tuyển)."""
    pw_hash = hash_password(PASSWORD)  # băm một lần dùng chung cho mọi tài khoản demo
    locs = {loc.name: loc for loc in [Location(name=n, region=r) for n, r in LOCATIONS]}
    db.add_all(locs.values())
    db.add(User(email="admin@smartcareer.vn", password_hash=pw_hash, role="admin", full_name="Quản trị SmartCareer"))
    db.flush()
    skills = load_catalog(db)
    load_companies_and_jobs(db, skills, locs, pw_hash)
    n_cand = load_candidates(db, skills, locs, pw_hash, with_cv)
    stats = {"skills": len(skills), "candidates": n_cand + 1, "jobs": len(rows("jobs.csv"))}
    if applications:
        from .gen_applications import generate_applications

        stats["applications"] = generate_applications(db, random.Random(rng_seed))  # commit ở cuối
    else:
        db.commit()
    return stats


LOCK_ID = 727274


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="xoá toàn bộ bảng rồi nạp lại")
    ap.add_argument("--no-applications", action="store_true")
    args = ap.parse_args()
    engine = dbmod.get_engine()
    Base.metadata.create_all(engine)
    # PostgreSQL: một kết nối riêng giữ khoá cố vấn để hai tiến trình nạp (entrypoint và lệnh chạy tay) không chạy cùng lúc
    lock = engine.connect() if engine.dialect.name == "postgresql" else None
    try:
        if lock is not None:
            lock.execute(text("SELECT pg_advisory_lock(:id)"), {"id": LOCK_ID})
        db = dbmod.new_session()
        if args.reset:
            reset(db)
            db = dbmod.new_session()
        try:
            if is_seeded(db):
                print("CSDL đã có dữ liệu; dùng --reset để nạp lại.")
                return
            print("Đã nạp:", seed(db, applications=not args.no_applications))
        finally:
            db.close()
    finally:
        if lock is not None:
            lock.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": LOCK_ID})
            lock.close()


if __name__ == "__main__":
    main()
