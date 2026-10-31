"""Các phương pháp chấm điểm M0–M4 với cùng một giao diện: `score_pair(model, cand, job) -> MatchDTO`.

M0  Quy tắc 60/25/15 (port nguyên `calculateSkillMatch` ở frontend) – baseline
M1  TF-IDF + cosine CV–JD
M2  Chỉ dùng embedding (semantic)
M3  Hybrid trọng số cố định + luật chặn
M4  Logistic Regression học trọng số trên 6 đặc trưng
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any, Callable, Optional

from .embedder import Embedder
from .explain import explain
from .features import FEATURE_NAMES, PairFeatures, compute_features
from .skills import split_skills
from .types import MODELS, CandidateInput, JobInput

MODELS_DIR = Path(os.getenv("MODELS_DIR", Path(__file__).resolve().parents[2] / "models_store"))

# Trọng số M0 (khớp MATCH_WEIGHTS ở src/utils/index.ts)
M0_WEIGHTS = {"required": 0.6, "preferred": 0.25, "preference": 0.15}
# Trọng số khởi đầu của M3; nếu M4 tốt hơn thì ghi đè bằng models_store/m3_weights.json
M3_DEFAULT_WEIGHTS = {"skill_req": 0.40, "skill_pref": 0.15, "semantic": 0.25, "exp": 0.10, "edu": 0.05, "pref": 0.05}
M3_CAP = 50  # thiếu hơn một nửa kỹ năng bắt buộc thì điểm không vượt ngưỡng này

MODEL_VERSIONS = {"m0": "m0-rule-v1", "m1": "m1-tfidf-v1", "m2": "m2-semantic-v1", "m3": "m3-hybrid-v1"}


def js_round(x: float) -> int:
    """Math.round của JavaScript (làm tròn nửa lên) để M0 khớp frontend."""
    return int(math.floor(x + 0.5))


def _percent(part: int, total: int) -> int:
    return 0 if total == 0 else js_round(part / total * 100)


def build_dto(
    model: str,
    version: str,
    total: int,
    components: dict[str, Optional[int]],
    f: PairFeatures,
) -> dict[str, Any]:
    total = max(0, min(100, int(total)))
    return {
        "model": model,
        "model_version": version,
        "total_score": total,
        "components": components,
        "matched_required": f.matched_required,
        "missing_required": f.missing_required,
        "matched_preferred": f.matched_preferred,
        "missing_preferred": f.missing_preferred,
        "location_match": f.location_match,
        "work_type_match": f.work_type_match,
        "explanation": explain(total, f.matched_required, f.matched_preferred, f.missing_required, f.missing_preferred),
    }


def _components_from_features(f: PairFeatures) -> dict[str, Optional[int]]:
    return {n: js_round(f.values[n] * 100) for n in FEATURE_NAMES}


# --------------------------------------------------------------------------- M0


def score_m0(cand: CandidateInput, job: JobInput) -> dict[str, Any]:
    """Port đúng `calculateSkillMatch` (src/utils/index.ts); `semantic/exp/edu` để None."""
    m_req, x_req = split_skills(cand.skills, job.required)
    m_pref, x_pref = split_skills(cand.skills, job.preferred)
    required_score = _percent(len(m_req), len(job.required))
    preferred_score = required_score if not job.preferred else _percent(len(m_pref), len(job.preferred))
    location_match = job.location in cand.locations
    work_type_match = job.work_type_label in cand.work_types
    preference_score = (50 if location_match else 0) + (50 if work_type_match else 0)
    total = js_round(
        required_score * M0_WEIGHTS["required"]
        + preferred_score * M0_WEIGHTS["preferred"]
        + preference_score * M0_WEIGHTS["preference"]
    )
    f = PairFeatures({}, m_req, x_req, m_pref, x_pref, location_match, work_type_match)
    components = {
        "skill_req": required_score,
        "skill_pref": preferred_score,
        "semantic": None,
        "exp": None,
        "edu": None,
        "pref": preference_score,
    }
    return build_dto("m0", MODEL_VERSIONS["m0"], total, components, f)


# --------------------------------------------------------------------------- M3

_m3_cache: Optional[tuple[dict[str, float], str]] = None


def load_m3_weights(force: bool = False) -> tuple[dict[str, float], str]:
    global _m3_cache
    if _m3_cache is not None and not force:
        return _m3_cache
    path = MODELS_DIR / "m3_weights.json"
    weights, version = dict(M3_DEFAULT_WEIGHTS), MODEL_VERSIONS["m3"]
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        weights = {k: float(data["weights"][k]) for k in FEATURE_NAMES}
        version = data.get("version", version)
    _m3_cache = (weights, version)
    return _m3_cache


def m3_total(f: PairFeatures, weights: dict[str, float]) -> float:
    s = 100 * sum(weights[n] * f.values[n] for n in FEATURE_NAMES)
    n_req = len(f.matched_required) + len(f.missing_required)
    if n_req > 0 and len(f.missing_required) > n_req / 2:
        s = min(s, float(M3_CAP))
    return s


def score_m3(cand: CandidateInput, job: JobInput, embedder: Optional[Embedder] = None) -> dict[str, Any]:
    weights, version = load_m3_weights()
    f = compute_features(cand, job, embedder)
    return build_dto("m3", version, js_round(m3_total(f, weights)), _components_from_features(f), f)


# --------------------------------------------------------------------------- Điều phối

Scorer = Callable[..., dict[str, Any]]


def score_pair(model: str, cand: CandidateInput, job: JobInput, embedder: Optional[Embedder] = None) -> dict[str, Any]:
    """Chấm một cặp theo model `m0`..`m4`, trả về MatchDTO (xem docs/00_KE_HOACH_KY_THUAT_TH3.md mục 3.4)."""
    model = model.lower()
    if model not in MODELS:
        raise ValueError(f"Model không hợp lệ: {model}")
    if model == "m0":
        return score_m0(cand, job)
    if model == "m3":
        return score_m3(cand, job, embedder)
    raise NotImplementedError(model)
