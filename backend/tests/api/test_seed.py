"""Dữ liệu seed: số lượng đúng yêu cầu, nhất quán và parser đọc đúng 50 CV tổng hợp."""
import csv
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app import db as dbmod
from app.models import (
    Application, ApplicationStatusHistory, Base, Candidate, CandidateSkill, Company, Job, JobSkill, Resume, Skill, SkillAlias,
)
from seed import load_seed

DATA = Path(__file__).resolve().parents[2] / "seed" / "data"
CV_DIR = Path(__file__).resolve().parents[2] / "seed" / "cv_files"


@pytest.fixture(scope="module")
def seeded():
    engine = dbmod.make_engine("sqlite://")
    Base.metadata.create_all(engine)
    dbmod.configure(engine)
    db = dbmod.new_session()
    stats = load_seed.seed(db)
    yield db, stats
    db.close()


def read(name):
    with open(DATA / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_counts_meet_requirements(seeded):
    db, stats = seeded
    count = lambda m: db.scalar(select(func.count()).select_from(m))  # noqa: E731
    assert count(Skill) >= 80 and count(SkillAlias) >= 150
    assert count(Company) == 30 and count(Job) == 150
    assert count(Candidate) == 301  # 300 sinh tự động + hồ sơ demo
    assert 1000 <= count(Application) <= 1400 and stats["applications"] == count(Application)
    assert count(Resume) == 50


def test_csv_quality_rules():
    skills = {r["name"] for r in read("skills.csv")}
    companies = {r["name"] for r in read("companies.csv")}
    jobs = read("jobs.csv")
    for r in jobs:
        used = [s for s in (r["required_skills"] + "|" + r["preferred_skills"]).split("|") if s]
        assert set(used) <= skills, r["external_id"]
        assert " hoặc " not in r["required_skills"]
        assert r["company_name"] in companies
        if r["salary_min"] and r["salary_max"]:
            assert float(r["salary_min"]) <= float(r["salary_max"])
    assert len({(r["title"], r["company_name"]) for r in jobs}) == len(jobs)  # không trùng tin
    assert {r["category"] for r in jobs} == {r["occupation"] for r in read("occupation_templates.csv")}
    assert {r["level"] for r in jobs} == {"intern", "fresher", "junior", "middle", "senior"}
    assert len({r["posted_at"][:7] for r in jobs}) >= 12  # tin rải đều 12 tháng


def test_every_job_has_required_skills_and_embedding(seeded):
    db, _ = seeded
    assert db.scalar(select(func.count()).select_from(Job).where(Job.embedding.is_(None))) == 0
    with_req = db.scalar(select(func.count(func.distinct(JobSkill.job_id))).where(JobSkill.is_required.is_(True)))
    assert with_req == 150


def test_candidates_have_confirmed_skills_and_consent(seeded):
    db, _ = seeded
    assert db.scalar(select(func.count()).select_from(Candidate).where(Candidate.consent_at.is_(None))) == 0
    no_skill = db.scalar(select(func.count()).select_from(Candidate).where(~Candidate.id.in_(select(CandidateSkill.candidate_id).where(CandidateSkill.confirmed.is_(True)))))
    assert no_skill == 0


def test_application_history_is_a_valid_funnel_path(seeded):
    """Mỗi đơn: bắt đầu bằng applied, mỗi bước hợp lệ, trạng thái hiện tại = bước cuối (nền của phễu BI)."""
    from app.routers.applications import can_transition

    db, _ = seeded
    history: dict[int, list[ApplicationStatusHistory]] = {}
    for h in db.scalars(select(ApplicationStatusHistory).order_by(ApplicationStatusHistory.application_id, ApplicationStatusHistory.changed_at, ApplicationStatusHistory.id)):
        history.setdefault(h.application_id, []).append(h)
    for app in db.scalars(select(Application)):
        steps = history[app.id]
        assert steps[0].from_status is None and steps[0].to_status == "applied"
        for prev, cur in zip(steps, steps[1:]):
            assert cur.from_status == prev.to_status and can_transition(prev.to_status, cur.to_status) and cur.changed_at >= prev.changed_at
        assert steps[-1].to_status == app.status
        assert app.match_score is not None and 0 <= app.match_score <= 100


def test_funnel_has_realistic_shape(seeded):
    from app.routers.bi import funnel_data

    db, _ = seeded
    f = funnel_data(db, None)
    counts = [s["count"] for s in f["stages"]]
    assert counts == sorted(counts, reverse=True) and counts[-1] > 20  # phễu giảm dần, có đủ hồ sơ hired để vẽ biểu đồ
    assert 0.05 < f["total_conversion"] < 0.2 and f["median_time_to_hire_days"] > 0


def test_parser_reads_the_50_seed_cvs_against_synthetic_truth():
    """Đáp án ở cv_manifest.csv do trình sinh tạo (tổng hợp); chỉ dùng để chặn hồi quy của parser."""
    from app.ai import evaluate
    from app.ai.embedder import HashingEmbedder
    from app.ai.skills import SkillIndex

    manifest = read("cv_manifest.csv")
    assert len(manifest) == 50 and all((CV_DIR / r["cv_file"]).exists() for r in manifest)
    assert {r["cv_file"].rsplit(".", 1)[1] for r in manifest} == {"pdf", "docx"}
    gold = {r["cv_file"]: set(r["true_skills"].split("|")) for r in manifest}
    years = {r["cv_file"]: float(r["true_years_exp"]) for r in manifest}
    idx = SkillIndex.from_csv(DATA / "skills.csv", DATA / "skill_aliases.csv")
    table = evaluate.evaluate_parser(CV_DIR, gold, years, index=idx, embedder=HashingEmbedder())
    t12 = table.set_index("tier").loc["T1+2"]
    assert t12["recall"] >= 0.95 and t12["precision"] >= 0.9
    assert table.attrs["years_mae"] <= 0.1
    truth_edu = {r["cv_file"]: int(r["true_education_level"]) for r in manifest}
    assert table.attrs["education"] == truth_edu
    # tầng 2 phải bắt thêm lỗi gõ mà tầng 1 bỏ sót
    assert table.set_index("tier").loc["T1+2", "recall"] > table.set_index("tier").loc["T1", "recall"]
