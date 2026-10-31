"""Nạp dữ liệu seed và file nhãn từ CSV (định dạng ở backend/seed/README.md) để huấn luyện và đánh giá.

Dùng chung cho các notebook; không phụ thuộc DB.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

import pandas as pd

from .embedder import Embedder, get_embedder
from .types import CandidateInput, JobInput

WORK_TYPE_LABEL = {"full_time": "Toàn thời gian", "part_time": "Bán thời gian", "internship": "Thực tập"}


def _split(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split("|") if x.strip()]


def _num(value: str) -> Optional[float]:
    value = (value or "").strip()
    return float(value) if value else None


def read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def work_type_label(job_type: str, work_mode: str) -> str:
    """Cùng quy tắc với adapter frontend: làm việc từ xa → 'Remote', còn lại theo loại hình."""
    return "Remote" if work_mode == "remote" else WORK_TYPE_LABEL.get(job_type, "")


def load_jobs(path: Path) -> dict[str, JobInput]:
    out: dict[str, JobInput] = {}
    for i, r in enumerate(read_csv(path), start=1):
        required, preferred = _split(r["required_skills"]), _split(r["preferred_skills"])
        text = " ".join([r["title"], r["description"], " ".join(_split(r["responsibilities"])), " ".join(required + preferred)])
        out[r["external_id"]] = JobInput(
            id=i,
            required=required,
            preferred=preferred,
            min_years=_num(r["min_years_exp"]) or 0.0,
            min_edu=int(_num(r["min_education"]) or 0),
            location=r["location"],
            work_type_label=work_type_label(r["job_type"], r["work_mode"]),
            salary_min=_num(r["salary_min"]),
            salary_max=_num(r["salary_max"]),
            text=text,
        )
    return out


def load_candidates(path: Path) -> dict[str, CandidateInput]:
    out: dict[str, CandidateInput] = {}
    for i, r in enumerate(read_csv(path), start=1):
        skills = _split(r["skills"])
        out[r["candidate_id"]] = CandidateInput(
            id=i,
            skills=skills,
            years_exp=_num(r["years_exp"]) or 0.0,
            edu=int(_num(r["education_level"]) or 0),
            locations=_split(r["locations"]),
            work_types=_split(r["work_types"]),
            sal_min=_num(r.get("expected_salary_min", "")),
            sal_max=_num(r.get("expected_salary_max", "")),
            text=r.get("text") or " ".join(skills),
        )
    return out


def attach_embeddings(items: dict, embedder: Optional[Embedder] = None) -> None:
    """Tính sẵn embedding cho ứng viên/tin (một lần), đúng như khi lưu vào DB."""
    embedder = embedder or get_embedder()
    keys = list(items)
    vecs = embedder.encode([items[k].text or " " for k in keys])
    for k, v in zip(keys, vecs):
        items[k].embedding = v


def load_labels(*paths: Path) -> pd.DataFrame:
    """Ghép nhiều file nhãn: mỗi file thành một cột `label_<tên file>`; cột chung `candidate_id, job_id`."""
    frames = []
    for p in paths:
        df = pd.read_csv(p, dtype={"candidate_id": str, "job_id": str})
        frames.append(df.rename(columns={"label": f"label_{Path(p).stem}"}))
    out = frames[0]
    for df in frames[1:]:
        out = out.merge(df, on=["candidate_id", "job_id"], how="inner")
    return out


def load_cv_labels(path: Path) -> tuple[dict[str, set[str]], dict[str, float]]:
    """labels_cv_skills.csv → ({cv_file: tập kỹ năng}, {cv_file: số năm KN nếu có})."""
    skills: dict[str, set[str]] = {}
    years: dict[str, float] = {}
    for r in read_csv(path):
        skills[r["cv_file"]] = set(_split(r["skills"]))
        if (r.get("years_exp") or "").strip():
            years[r["cv_file"]] = float(r["years_exp"])
    return skills, years
