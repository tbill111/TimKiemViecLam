"""Quy trình đánh giá cho Mục 05: parser (P/R/F1), M0–M4, ablation M3, phân tích lỗi, công bằng.

Các hàm trả về DataFrame để notebook xuất bảng vào báo cáo.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from .embedder import Embedder, get_embedder
from .extract import extract_skills
from .features import FEATURE_NAMES, PairFeatures, compute_features
from .metrics import mae, prf1_micro, rank_metrics
from .parser import extract_education_level, extract_text, extract_years_exp, normalize_text, split_sections
from .scorers import M3_DEFAULT_WEIGHTS, fit_tfidf, js_round, m3_total, score_pair
from .skills import SkillIndex
from .types import MODELS, CandidateInput, JobInput

TIERS = {"T1": (1,), "T1+2": (1, 2), "T1+2+3": (1, 2, 3)}


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def evaluate_parser(
    cv_dir: Path,
    gold_skills: dict[str, set[str]],
    gold_years: Optional[dict[str, float]] = None,
    index: Optional[SkillIndex] = None,
    embedder: Optional[Embedder] = None,
) -> pd.DataFrame:
    """P/R/F1 (micro) của từng tầng trích kỹ năng trên các CV có nhãn tay, và MAE số năm kinh nghiệm."""
    texts: dict[str, tuple[str, dict[str, str]]] = {}
    for name in gold_skills:
        text = normalize_text(extract_text((cv_dir / name).read_bytes(), name))
        texts[name] = (text, split_sections(text))
    gold_names = list(gold_skills)
    # Nhãn tay có thể ghi tên chuẩn khác hoa/thường: so khớp theo chữ thường
    gold = [{s.lower() for s in gold_skills[n]} for n in gold_names]
    rows = []
    for label, tiers in TIERS.items():
        pred = [
            {h.name.lower() for h in extract_skills(texts[n][0], index, tiers, embedder or get_embedder(), texts[n][1].get("skills", ""))}
            for n in gold_names
        ]
        rows.append({"tier": label, **prf1_micro(pred, gold), "n_cv": len(gold_names)})
    out = pd.DataFrame(rows)
    if gold_years:
        names = [n for n in gold_names if n in gold_years]
        pred_years = [extract_years_exp(texts[n][0], texts[n][1]) for n in names]
        out.attrs["years_mae"] = mae(pred_years, [gold_years[n] for n in names])
        out.attrs["education"] = {n: extract_education_level(texts[n][0], texts[n][1]) for n in names}
    return out


# ---------------------------------------------------------------------------
# Xếp hạng M0–M4
# ---------------------------------------------------------------------------


def _pairs(pairs: pd.DataFrame, cands: dict[str, CandidateInput], jobs: dict[str, JobInput]) -> list[tuple[CandidateInput, JobInput]]:
    return [(cands[c], jobs[j]) for c, j in zip(pairs["candidate_id"], pairs["job_id"])]


def build_feature_matrix(
    pairs: pd.DataFrame, cands: dict[str, CandidateInput], jobs: dict[str, JobInput], embedder: Optional[Embedder] = None
) -> tuple[np.ndarray, list[PairFeatures]]:
    feats = [compute_features(c, j, embedder) for c, j in _pairs(pairs, cands, jobs)]
    return np.array([f.vector() for f in feats]), feats


def evaluate_models(
    pairs: pd.DataFrame,
    cands: dict[str, CandidateInput],
    jobs: dict[str, JobInput],
    models: tuple[str, ...] = MODELS,
    m4_scores: Optional[np.ndarray] = None,
    embedder: Optional[Embedder] = None,
) -> pd.DataFrame:
    """Bảng so sánh các phương pháp. `pairs` có cột candidate_id, job_id, label (0–3, nhãn chốt).

    M4 nên truyền `m4_scores` (xác suất×100 trên fold kiểm tra của GroupKFold) để không đo trên dữ liệu đã huấn luyện.
    """
    fit_tfidf([j.text for j in jobs.values()])
    plist = _pairs(pairs, cands, jobs)
    rows = []
    for model in models:
        if model == "m4" and m4_scores is not None:
            scores, ms = np.asarray(m4_scores, dtype=float), float("nan")
        else:
            t0 = time.perf_counter()
            scores = np.array([score_pair(model, c, j, embedder)["total_score"] for c, j in plist], dtype=float)
            ms = (time.perf_counter() - t0) / max(1, len(plist)) * 1000
        frame = pd.DataFrame({"candidate_id": pairs["candidate_id"].to_numpy(), "label": pairs["label"].to_numpy(), "score": scores})
        rows.append({"model": model, **rank_metrics(frame), "ms_per_pair": ms})
    return pd.DataFrame(rows).set_index("model")


def ablation_m3(
    pairs: pd.DataFrame,
    feats: list[PairFeatures],
    weights: Optional[dict[str, float]] = None,
) -> pd.DataFrame:
    """Bỏ lần lượt từng đặc trưng khỏi M3 (đặt trọng số 0, chuẩn hoá phần còn lại), ghi nDCG@10 giảm bao nhiêu."""
    weights = weights or M3_DEFAULT_WEIGHTS

    def ndcg_with(w: dict[str, float]) -> float:
        scores = np.array([js_round(m3_total(f, w)) for f in feats], dtype=float)
        frame = pd.DataFrame({"candidate_id": pairs["candidate_id"].to_numpy(), "label": pairs["label"].to_numpy(), "score": scores})
        return rank_metrics(frame)["ndcg@10"]

    base = ndcg_with(weights)
    rows = [{"feature_removed": "(không bỏ)", "ndcg@10": base, "delta": 0.0}]
    for name in FEATURE_NAMES:
        w = {k: (0.0 if k == name else v) for k, v in weights.items()}
        total = sum(w.values())
        w = {k: v / total for k, v in w.items()}
        n = ndcg_with(w)
        rows.append({"feature_removed": name, "ndcg@10": n, "delta": n - base})
    return pd.DataFrame(rows)


def error_analysis(
    pairs: pd.DataFrame, cands: dict[str, CandidateInput], jobs: dict[str, JobInput], model: str = "m3", n: int = 5,
    embedder: Optional[Embedder] = None,
) -> pd.DataFrame:
    """Các cặp lệch nhiều nhất giữa điểm hệ thống (0–1) và nhãn tay (0–1), kèm kỹ năng thiếu để lý giải nguyên nhân."""
    rows = []
    for (cid, jid, label), (c, j) in zip(pairs[["candidate_id", "job_id", "label"]].itertuples(index=False), _pairs(pairs, cands, jobs)):
        res = score_pair(model, c, j, embedder)
        rows.append(
            {
                "candidate_id": cid, "job_id": jid, "label": label, "score": res["total_score"],
                "error": res["total_score"] / 100 - label / 3,
                "missing_required": "|".join(res["missing_required"]), "matched_required": "|".join(res["matched_required"]),
            }
        )
    df = pd.DataFrame(rows)
    return df.reindex(df["error"].abs().sort_values(ascending=False).index).head(n).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Công bằng
# ---------------------------------------------------------------------------


def fairness_check(cv_a: bytes, cv_b: bytes, filename: str, job: JobInput, index: Optional[SkillIndex] = None, embedder: Optional[Embedder] = None) -> dict:
    """Hai CV chỉ khác tên/giới tính (phần đầu CV) phải cho cùng kỹ năng, năm KN, học vấn và cùng điểm M3."""
    from .embedder import from_bytes
    from .parser import parse_cv

    out = {}
    for tag, data in (("a", cv_a), ("b", cv_b)):
        r = parse_cv(data, filename, index=index, embedder=embedder)
        cand = CandidateInput(
            id=0, skills=[s["name"] for s in r["skills"]], years_exp=r["years_exp"], edu=r["education_level"],
            text=r["model_text"], embedding=from_bytes(r["embedding"]),
        )
        out[tag] = {
            "skills": sorted(s["name"] for s in r["skills"]), "years_exp": r["years_exp"], "education_level": r["education_level"],
            "score_m3": score_pair("m3", cand, job, embedder)["total_score"],
        }
    out["identical"] = out["a"] == out["b"]
    return out
