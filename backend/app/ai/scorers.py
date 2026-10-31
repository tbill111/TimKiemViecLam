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
from .types import MODELS, CandidateInput, JobInput, ModelNotAvailable

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


# --------------------------------------------------------------------------- M1: TF-IDF

_tfidf = None  # (vectorizer đã fit trên toàn bộ tin) hoặc None


def _tokens(text: str) -> list[str]:
    """Từ đơn + cặp từ liền kề; dùng underthesea tách từ tiếng Việt nếu cài được."""
    import re
    import unicodedata

    text = unicodedata.normalize("NFC", text).lower()
    try:
        from underthesea import word_tokenize

        words = [w.replace(" ", "_") for w in word_tokenize(text)]
    except Exception:
        words = re.findall(r"\w+", text)
    words = [w for w in words if re.search(r"\w", w)]
    return words + [f"{a}__{b}" for a, b in zip(words, words[1:])]


def fit_tfidf(corpus: list[str]) -> None:
    """Fit IDF trên toàn bộ tin tuyển dụng (gọi một lần khi khởi động hoặc khi huấn luyện)."""
    global _tfidf
    from sklearn.feature_extraction.text import TfidfVectorizer

    _tfidf = TfidfVectorizer(analyzer=_tokens, sublinear_tf=True).fit(corpus)


def _tfidf_cosine(cand_text: str, job_text: str) -> float:
    from sklearn.feature_extraction.text import TfidfVectorizer

    vec = _tfidf
    if vec is None:  # chưa có kho văn bản: fit tạm trên chính hai văn bản
        vec = TfidfVectorizer(analyzer=_tokens, sublinear_tf=True).fit([cand_text, job_text])
    m = vec.transform([cand_text, job_text])
    return float((m[0].multiply(m[1])).sum())  # TfidfVectorizer đã chuẩn hoá L2


def score_m1(cand: CandidateInput, job: JobInput, embedder: Optional[Embedder] = None) -> dict[str, Any]:
    f = compute_features(cand, job, embedder)
    total = js_round(max(0.0, _tfidf_cosine(cand.text, job.text)) * 100)
    return build_dto("m1", MODEL_VERSIONS["m1"], total, _components_from_features(f), f)


# --------------------------------------------------------------------------- M2: chỉ embedding


def score_m2(cand: CandidateInput, job: JobInput, embedder: Optional[Embedder] = None) -> dict[str, Any]:
    f = compute_features(cand, job, embedder)
    return build_dto("m2", MODEL_VERSIONS["m2"], js_round(f.values["semantic"] * 100), _components_from_features(f), f)


# --------------------------------------------------------------------------- M4: Logistic Regression

_m4_cache: Optional[dict[str, Any]] = None


def load_m4(force: bool = False) -> dict[str, Any]:
    global _m4_cache
    if _m4_cache is not None and not force:
        return _m4_cache
    path = MODELS_DIR / "m4.joblib"
    if not path.exists():
        raise ModelNotAvailable("Chưa huấn luyện M4 (thiếu models_store/m4.joblib).")
    import joblib

    _m4_cache = joblib.load(path)
    return _m4_cache


def score_m4(cand: CandidateInput, job: JobInput, embedder: Optional[Embedder] = None) -> dict[str, Any]:
    artifact = load_m4()
    f = compute_features(cand, job, embedder)
    proba = float(artifact["model"].predict_proba([f.vector()])[0][1])
    return build_dto("m4", artifact.get("version", "m4"), js_round(proba * 100), _components_from_features(f), f)


# --------------------------------------------------------------------------- Điều phối

Scorer = Callable[..., dict[str, Any]]


def score_pair(model: str, cand: CandidateInput, job: JobInput, embedder: Optional[Embedder] = None) -> dict[str, Any]:
    """Chấm một cặp theo model `m0`..`m4`, trả về MatchDTO (xem docs/00_KE_HOACH_KY_THUAT_TH3.md mục 3.4)."""
    model = model.lower()
    if model not in MODELS:
        raise ValueError(f"Model không hợp lệ: {model}")
    if model == "m0":
        return score_m0(cand, job)
    return {"m1": score_m1, "m2": score_m2, "m3": score_m3, "m4": score_m4}[model](cand, job, embedder)


def score_many(model: str, cand: CandidateInput, jobs: list[JobInput], embedder: Optional[Embedder] = None) -> list[dict[str, Any]]:
    """Chấm một ứng viên với nhiều tin; nên truyền sẵn `embedding` cho tin để đạt < 2 giây với 500 tin."""
    return [score_pair(model, cand, j, embedder) for j in jobs]
