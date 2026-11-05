"""Huấn luyện các mô hình học máy trên 6 đặc trưng: M4 (Logistic Regression), M5 (Random Forest), M6 (Gradient Boosting)
và các tiện ích gắn với M3.

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
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

from .features import FEATURE_NAMES
from .scorers import M3_DEFAULT_WEIGHTS


# Ba họ mô hình học máy được so sánh. Siêu tham số của cây được chọn cố định từ trước (không dò trên dữ liệu kiểm tra),
# nông và có regularization vì chỉ có ~300 cặp: cây sâu sẽ nhớ thuộc lòng thay vì học quy luật.
KINDS = ("logreg", "random_forest", "gradient_boosting")
LOGREG_C_GRID = (0.1, 0.3, 1.0, 3.0, 10.0)
SEED = 42


def _new_model(kind: str = "logreg", C: float = 1.0):
    if kind == "logreg":
        return LogisticRegression(C=C, class_weight="balanced", max_iter=1000)
    if kind == "random_forest":
        return RandomForestClassifier(n_estimators=300, max_depth=4, min_samples_leaf=5, class_weight="balanced_subsample", random_state=SEED, n_jobs=1)
    if kind == "gradient_boosting":
        return GradientBoostingClassifier(n_estimators=150, learning_rate=0.05, max_depth=2, subsample=0.8, min_samples_leaf=5, random_state=SEED)
    raise ValueError(f"Họ mô hình không hợp lệ: {kind}")


def _group_splits(X: np.ndarray, y: np.ndarray, groups: np.ndarray, n_splits: int):
    n_splits = min(n_splits, len(np.unique(groups)))
    for tr, te in GroupKFold(n_splits=n_splits).split(X, y, groups):
        assert not set(groups[tr]) & set(groups[te]), "rò rỉ dữ liệu giữa tập huấn luyện và kiểm tra"
        yield tr, te


def best_logreg_c(X: np.ndarray, y: np.ndarray, groups: np.ndarray, n_splits: int = 5, grid: tuple = LOGREG_C_GRID) -> float:
    """Chọn C của Logistic Regression bằng GroupKFold (log-loss thấp nhất); nhiều C bằng nhau thì lấy C nhỏ (regularization mạnh)."""
    from sklearn.metrics import log_loss

    best_c, best_loss = grid[0], float("inf")
    for c in grid:
        proba = np.zeros(len(y))
        for tr, te in _group_splits(X, y, groups, n_splits):
            proba[te] = _new_model("logreg", c).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
        loss = log_loss(y, np.clip(proba, 1e-6, 1 - 1e-6))
        if loss < best_loss - 1e-9:
            best_c, best_loss = c, loss
    return best_c


def cross_val_scores(
    X: np.ndarray, y: np.ndarray, groups: np.ndarray, n_splits: int = 5, kind: str = "logreg", tune: bool = False,
) -> np.ndarray:
    """Xác suất "phù hợp" dự đoán trên fold kiểm tra cho từng cặp (không bao giờ thấy chính ứng viên đó khi huấn luyện).

    `tune=True` (chỉ logreg): chọn C **bên trong** từng fold huấn luyện (GroupKFold lồng) nên điểm kiểm tra không bị rò rỉ
    từ việc dò siêu tham số."""
    out = np.zeros(len(y), dtype=float)
    for tr, te in _group_splits(X, y, groups, n_splits):
        c = best_logreg_c(X[tr], y[tr], groups[tr], n_splits=max(2, n_splits - 1)) if (tune and kind == "logreg") else 1.0
        m = _new_model(kind, c).fit(X[tr], y[tr])
        out[te] = m.predict_proba(X[te])[:, 1]
    return out


def fit_model(kind: str, X: np.ndarray, y: np.ndarray, C: float = 1.0):
    return _new_model(kind, C).fit(X, y)


def fit_m4(X: np.ndarray, y: np.ndarray, C: float = 1.0) -> LogisticRegression:
    return _new_model("logreg", C).fit(X, y)


def feature_importance_table(model) -> dict[str, float]:
    """Hệ số (Logistic Regression) hoặc độ quan trọng đặc trưng (cây) theo tên đặc trưng."""
    values = model.coef_[0] if hasattr(model, "coef_") else model.feature_importances_
    return {n: float(v) for n, v in zip(FEATURE_NAMES, values)}


def coefficient_table(model: LogisticRegression) -> dict[str, float]:
    return {n: float(c) for n, c in zip(FEATURE_NAMES, model.coef_[0])}


def save_model(model, path: Path, model_id: str, version: str | None = None, extra: dict[str, Any] | None = None) -> str:
    version = version or f"{model_id}-{dt.date.today().isoformat()}"
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": list(FEATURE_NAMES), "version": version, "extra": extra or {}}, path)
    return version


def save_m4(model: LogisticRegression, path: Path, version: str | None = None, extra: dict[str, Any] | None = None) -> str:
    return save_model(model, path, "m4", version, extra)


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
