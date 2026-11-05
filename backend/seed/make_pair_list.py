"""Randomly select database resumes and jobs and export unique labeling pairs as JSON.

Run from ``backend/`` with ``python -m seed.make_pair_list``.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Job, Resume

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "labels" / "pair_list.json"

# Nhóm "gần" của từng JobCategory (đối xứng được xử lý trong `near_groups`)
NEAR = {
    "Frontend Development": ["Software Engineering", "UI/UX Design", "Backend Development"],
    "Backend Development": ["Software Engineering", "Frontend Development", "Data Science & Analytics"],
    "Software Engineering": ["Frontend Development", "Backend Development", "QA & Testing"],
    "QA & Testing": ["Software Engineering", "IT Support"],
    "Data Science & Analytics": ["Business Analysis", "Backend Development"],
    "Business Analysis": ["Data Science & Analytics", "Business Operations"],
    "Business Operations": ["Business Analysis", "Digital Marketing"],
    "Digital Marketing": ["Business Operations", "UI/UX Design"],
    "UI/UX Design": ["Frontend Development", "Digital Marketing"],
    "IT Support": ["QA & Testing", "Software Engineering"],
}
PER_CANDIDATE = {"same": 4, "near": 3, "far": 3}


def near_groups(category: str) -> set[str]:
    out = set(NEAR.get(category, []))
    out |= {k for k, v in NEAR.items() if category in v}
    out.discard(category)
    return out


def read_rows(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def pick_candidates(cands: list[dict[str, str]], n: int, rng: random.Random) -> list[dict[str, str]]:
    by_occ: dict[str, list[dict[str, str]]] = defaultdict(list)
    for c in cands:
        by_occ[c["occupation"]].append(c)
    for lst in by_occ.values():
        rng.shuffle(lst)
    chosen: list[dict[str, str]] = []
    occs = sorted(by_occ)
    while len(chosen) < min(n, len(cands)):
        for occ in occs:  # vòng tròn qua các nhóm nghề
            if by_occ[occ] and len(chosen) < n:
                chosen.append(by_occ[occ].pop())
    return chosen


def pick_jobs(candidate_occ: str, jobs: list[dict[str, str]], rng: random.Random) -> list[dict[str, str]]:
    near = near_groups(candidate_occ)
    pools = {
        "same": [j for j in jobs if j["category"] == candidate_occ],
        "near": [j for j in jobs if j["category"] in near],
        "far": [j for j in jobs if j["category"] != candidate_occ and j["category"] not in near],
    }
    chosen: list[dict[str, str]] = []
    used: set[str] = set()
    for key in ("same", "near", "far"):
        pool = [j for j in pools[key] if j["external_id"] not in used]
        rng.shuffle(pool)
        for j in pool[: PER_CANDIDATE[key]]:
            chosen.append(j)
            used.add(j["external_id"])
    total = sum(PER_CANDIDATE.values())
    if len(chosen) < total:  # nhóm thiếu tin thì bù từ phần còn lại để đủ 10
        rest = [j for j in jobs if j["external_id"] not in used]
        rng.shuffle(rest)
        chosen += rest[: total - len(chosen)]
    return chosen


def build_pairs(candidates_csv: Path, jobs_csv: Path, n_candidates: int = 30, seed: int = 42) -> list[tuple[str, str]]:
    rng = random.Random(seed)
    cands, jobs = read_rows(candidates_csv), read_rows(jobs_csv)
    pairs: list[tuple[str, str]] = []
    for c in pick_candidates(cands, n_candidates, rng):
        for j in pick_jobs(c["occupation"], jobs, rng):
            pairs.append((c["candidate_id"], j["external_id"]))
    return pairs


def build_database_pairs(
    db: Session,
    n_resumes: int = 50,
    n_jobs: int = 150,
    n_pairs: int = 300,
    rng: random.Random | None = None,
) -> list[dict[str, int]]:
    if min(n_resumes, n_jobs, n_pairs) <= 0:
        raise ValueError("Resume, job, and pair counts must all be positive.")

    resumes = db.execute(
        select(Resume.id, Resume.candidate_id)
        .where(Resume.is_active.is_(True))
        .order_by(func.random())
        .limit(n_resumes)
    ).all()
    jobs = db.scalars(
        select(Job.id)
        .order_by(func.random())
        .limit(n_jobs)
    ).all()

    if len(resumes) < n_resumes:
        raise RuntimeError(f"Need {n_resumes} active resumes; found {len(resumes)}.")
    if len(jobs) < n_jobs:
        raise RuntimeError(f"Need {n_jobs} jobs; found {len(jobs)}.")
    if n_pairs > len(resumes) * len(jobs):
        raise ValueError(
            f"Cannot create {n_pairs} unique pairs from {len(resumes)} resumes "
            f"and {len(jobs)} jobs."
        )

    chooser = rng or random.SystemRandom()
    pair_indexes = chooser.sample(range(len(resumes) * len(jobs)), n_pairs)
    pairs: list[dict[str, int]] = []
    for pair_index in pair_indexes:
        resume_index, job_index = divmod(pair_index, len(jobs))
        resume = resumes[resume_index]
        pairs.append({
            "resume_id": resume.id,
            "candidate_id": resume.candidate_id,
            "job_id": jobs[job_index],
        })
    return pairs


def write_pairs_json(pairs: list[dict[str, int]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pairs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUTPUT, help="JSON output file")
    args = ap.parse_args()
    with SessionLocal() as db:
        pairs = build_database_pairs(db)
    write_pairs_json(pairs, args.out)
    print(f"Wrote {len(pairs)} unique resume/job pairs to {args.out}")


if __name__ == "__main__":
    main()
