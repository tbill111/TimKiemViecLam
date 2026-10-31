"""Chọn 30 ứng viên × 10 tin để hai người gán nhãn độc lập.

Mỗi ứng viên có 10 tin: 4 cùng nhóm nghề, 3 nhóm gần, 3 nhóm khác – để có đủ cả cặp tốt lẫn cặp kém.
Ứng viên được chọn đều qua các nhóm nghề. Chạy lặp lại cùng seed cho cùng kết quả.

    python -m seed.make_pair_list --candidates seed/data/candidates_generated.csv \
        --jobs seed/data/jobs.csv --out seed/labels/labels_pairs_template.csv
"""
from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path

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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", type=Path, default=Path("seed/data/candidates_generated.csv"))
    ap.add_argument("--jobs", type=Path, default=Path("seed/data/jobs.csv"))
    ap.add_argument("--out", type=Path, default=Path("seed/labels/labels_pairs_template.csv"))
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    pairs = build_pairs(args.candidates, args.jobs, args.n, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["candidate_id", "job_id", "label"])
        w.writerows((c, j, "") for c, j in pairs)
    print(f"Đã ghi {len(pairs)} cặp vào {args.out}")


if __name__ == "__main__":
    main()
