import csv
from collections import Counter
from datetime import datetime
import json
import random

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import Candidate, Company, Job, Location, Resume
from seed.make_pair_list import build_database_pairs, build_pairs, near_groups, write_pairs_json

CATS = ["Frontend Development", "Backend Development", "Data Science & Analytics", "QA & Testing", "Software Engineering"]


def _write(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def make_data(tmp_path, n_cand=60, n_jobs=60):
    cands = [(f"cand-{i:04d}", CATS[i % len(CATS)]) for i in range(n_cand)]
    jobs = [(f"job-{i:03d}", CATS[(i * 3) % len(CATS)]) for i in range(n_jobs)]
    _write(tmp_path / "c.csv", ["candidate_id", "occupation"], cands)
    _write(tmp_path / "j.csv", ["external_id", "category"], jobs)
    return tmp_path / "c.csv", tmp_path / "j.csv", dict(jobs)


def test_30_candidates_10_unique_jobs_each(tmp_path):
    c, j, _ = make_data(tmp_path)
    pairs = build_pairs(c, j)
    assert len(pairs) == 300
    per = Counter(cid for cid, _ in pairs)
    assert len(per) == 30 and set(per.values()) == {10}
    assert all(len({jid for cid2, jid in pairs if cid2 == cid}) == 10 for cid in per)


def test_composition_same_near_far(tmp_path):
    c, j, job_cat = make_data(tmp_path)
    occ = {cid: o for cid, o in csv.reader(open(c, encoding="utf-8")) if cid != "candidate_id"}
    pairs = build_pairs(c, j)
    for cid in {p[0] for p in pairs}:
        cats = [job_cat[jid] for c2, jid in pairs if c2 == cid]
        same = sum(x == occ[cid] for x in cats)
        near = sum(x in near_groups(occ[cid]) for x in cats)
        assert same == 4 and near == 3, (cid, same, near)


def test_candidates_spread_over_occupations_and_deterministic(tmp_path):
    c, j, _ = make_data(tmp_path)
    p1, p2 = build_pairs(c, j), build_pairs(c, j)
    assert p1 == p2
    occ = {cid: o for cid, o in csv.reader(open(c, encoding="utf-8")) if cid != "candidate_id"}
    counts = Counter(occ[cid] for cid in {p[0] for p in p1})
    assert set(counts) == set(CATS) and max(counts.values()) - min(counts.values()) <= 1


def test_different_seed_changes_selection(tmp_path):
    c, j, _ = make_data(tmp_path)
    assert build_pairs(c, j, seed=1) != build_pairs(c, j, seed=2)


def _database_with_resumes_and_jobs(tmp_path, n_resumes=5, n_jobs=10):
    engine = create_engine(f"sqlite:///{tmp_path / 'pairs.db'}")
    Base.metadata.create_all(
        engine,
        tables=[
            Location.__table__,
            Company.__table__,
            Candidate.__table__,
            Resume.__table__,
            Job.__table__,
        ],
    )
    with Session(engine) as db:
        company = Company(name="Test company")
        db.add(company)
        db.flush()
        for index in range(n_resumes):
            candidate = Candidate(full_name=f"Candidate {index}")
            db.add(candidate)
            db.flush()
            db.add(Resume(
                candidate_id=candidate.id,
                filename=f"resume-{index}.pdf",
                consent_at=datetime.now(),
            ))
        for index in range(n_jobs):
            db.add(Job(company_id=company.id, title=f"Job {index}"))
        db.commit()
    return engine


def test_database_pairs_are_unique_and_reference_selected_rows(tmp_path):
    engine = _database_with_resumes_and_jobs(tmp_path)
    with Session(engine) as db:
        pairs = build_database_pairs(db, n_resumes=5, n_jobs=10, n_pairs=30, rng=random.Random(42))

    resume_job_pairs = {(pair["resume_id"], pair["job_id"]) for pair in pairs}
    assert len(pairs) == 30
    assert len(resume_job_pairs) == 30
    assert len({pair["resume_id"] for pair in pairs}) == 5
    assert len({pair["job_id"] for pair in pairs}) == 10
    assert all({"resume_id", "candidate_id", "job_id"} == pair.keys() for pair in pairs)

    output = tmp_path / "labels" / "pairs.json"
    write_pairs_json(pairs, output)
    assert len(json.loads(output.read_text(encoding="utf-8"))) == 30


def test_default_database_selection_creates_exactly_300_unique_pairs(tmp_path):
    engine = _database_with_resumes_and_jobs(tmp_path, n_resumes=50, n_jobs=150)
    with Session(engine) as db:
        pairs = build_database_pairs(db)

    assert len(pairs) == 300
    assert len({(pair["resume_id"], pair["job_id"]) for pair in pairs}) == 300


def test_database_pair_generation_requires_enough_active_resumes(tmp_path):
    engine = _database_with_resumes_and_jobs(tmp_path, n_resumes=2)
    with Session(engine) as db:
        with pytest.raises(RuntimeError, match="Need 5 active resumes; found 2"):
            build_database_pairs(db, n_resumes=5, n_jobs=10, n_pairs=30)
