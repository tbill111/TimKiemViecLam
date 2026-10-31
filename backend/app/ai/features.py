"""Sáu đặc trưng cho một cặp (ứng viên, tin), mỗi đặc trưng nằm trong [0, 1].

Không dùng tên, giới tính, tuổi, ảnh làm đặc trưng (yêu cầu công bằng của đề bài).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from .embedder import Embedder, cosine, get_embedder
from .skills import split_skills
from .types import CandidateInput, JobInput

FEATURE_NAMES = ("skill_req", "skill_pref", "semantic", "exp", "edu", "pref")
REMOTE_LABEL = "Remote"


@dataclass
class PairFeatures:
    values: dict[str, float]
    matched_required: list[str]
    missing_required: list[str]
    matched_preferred: list[str]
    missing_preferred: list[str]
    location_match: bool
    work_type_match: bool

    def vector(self) -> list[float]:
        return [self.values[n] for n in FEATURE_NAMES]


def _semantic(cand: CandidateInput, job: JobInput, embedder: Optional[Embedder]) -> float:
    ce, je = cand.embedding, job.embedding
    if ce is None or je is None:
        emb = embedder or get_embedder()
        if ce is None:
            ce = emb.encode([cand.text or " "])[0]
        if je is None:
            je = emb.encode([job.text or " "])[0]
    return (cosine(np.asarray(ce), np.asarray(je)) + 1.0) / 2.0  # đưa [-1, 1] về [0, 1]


def _experience(cand: CandidateInput, job: JobInput) -> float:
    if job.min_years <= 0:
        return 1.0
    return min(1.0, cand.years_exp / job.min_years)


def _education(cand: CandidateInput, job: JobInput) -> float:
    if job.min_edu <= 0 or cand.edu >= job.min_edu:
        return 1.0
    return 0.5 if cand.edu == job.min_edu - 1 else 0.0


def _ranges_overlap(a_min: Optional[float], a_max: Optional[float], b_min: Optional[float], b_max: Optional[float]) -> Optional[bool]:
    if None in (a_min, a_max, b_min, b_max):
        return None
    return a_min <= b_max and b_min <= a_max  # type: ignore[operator]


def _preference(cand: CandidateInput, job: JobInput) -> float:
    """Trung bình của: khớp địa điểm (tin Remote = 1), khớp hình thức, khoảng lương giao nhau.
    Thành phần thiếu dữ liệu (ứng viên chưa nêu mong muốn, tin thoả thuận lương) bị bỏ qua; không có gì để so thì trả 0,5."""
    parts: list[float] = []
    if job.location == REMOTE_LABEL:
        parts.append(1.0)
    elif cand.locations:
        parts.append(1.0 if job.location in cand.locations else 0.0)
    if cand.work_types:
        parts.append(1.0 if job.work_type_label in cand.work_types else 0.0)
    overlap = _ranges_overlap(cand.sal_min, cand.sal_max, job.salary_min, job.salary_max)
    if overlap is not None:
        parts.append(1.0 if overlap else 0.0)
    return sum(parts) / len(parts) if parts else 0.5


def compute_features(cand: CandidateInput, job: JobInput, embedder: Optional[Embedder] = None) -> PairFeatures:
    m_req, x_req = split_skills(cand.skills, job.required)
    m_pref, x_pref = split_skills(cand.skills, job.preferred)
    values = {
        "skill_req": len(m_req) / len(job.required) if job.required else 1.0,
        "skill_pref": len(m_pref) / len(job.preferred) if job.preferred else 1.0,
        "semantic": _semantic(cand, job, embedder),
        "exp": _experience(cand, job),
        "edu": _education(cand, job),
        "pref": _preference(cand, job),
    }
    return PairFeatures(
        values=values,
        matched_required=m_req,
        missing_required=x_req,
        matched_preferred=m_pref,
        missing_preferred=x_pref,
        location_match=job.location in cand.locations,
        work_type_match=job.work_type_label in cand.work_types,
    )
