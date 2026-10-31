"""Huấn luyện M4 (Logistic Regression trên 6 đặc trưng) và các tiện ích gắn với M3.

Dữ liệu: các cặp có nhãn 0–3, nhãn nhị phân "phù hợp" khi >= 2.
Chia GroupKFold theo candidate_id để một ứng viên không vừa ở tập huấn luyện vừa ở tập kiểm tra.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

from .features import FEATURE_NAMES
from .scorers import M3_DEFAULT_WEIGHTS


def _new_model() -> LogisticRegression:
    return LogisticRegression(C=1.0, class_weight="balanced", max_iter=1000)


def cross_val_scores(X: np.ndarray, y: np.ndarray, groups: np.ndarray, n_splits: int = 5) -> np.ndarray:
    """Xác suất "phù hợp" dự đoán trên fold kiểm tra cho từng cặp (không bao giờ thấy chính ứng viên đó khi huấn luyện)."""
    n_groups = len(np.unique(groups))
    n_splits = min(n_splits, n_groups)
    out = np.zeros(len(y), dtype=float)
    for tr, te in GroupKFold(n_splits=n_splits).split(X, y, groups):
        assert not set(groups[tr]) & set(groups[te]), "rò rỉ dữ liệu giữa tập huấn luyện và kiểm tra"
        m = _new_model().fit(X[tr], y[tr])
        out[te] = m.predict_proba(X[te])[:, 1]
    return out


def fit_m4(X: np.ndarray, y: np.ndarray) -> LogisticRegression:
    return _new_model().fit(X, y)


def coefficient_table(model: LogisticRegression) -> dict[str, float]:
    return {n: float(c) for n, c in zip(FEATURE_NAMES, model.coef_[0])}


def save_m4(model: LogisticRegression, path: Path, version: str | None = None, extra: dict[str, Any] | None = None) -> str:
    version = version or f"m4-{dt.date.today().isoformat()}"
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": list(FEATURE_NAMES), "version": version, "extra": extra or {}}, path)
    return version


def m3_weights_from_m4(model: LogisticRegression) -> dict[str, float]:
    """Hệ số dương của M4 chuẩn hoá về tổng 1 (hệ số âm đặt 0) – dùng thay trọng số tay của M3 nếu M4 tốt hơn."""
    coefs = np.clip(model.coef_[0], 0, None)
    if coefs.sum() == 0:
        return dict(M3_DEFAULT_WEIGHTS)
    w = coefs / coefs.sum()
    return {n: float(v) for n, v in zip(FEATURE_NAMES, w)}


def save_m3_weights(weights: dict[str, float], path: Path, version: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"version": version, "weights": weights}, indent=2, ensure_ascii=False), encoding="utf-8")
