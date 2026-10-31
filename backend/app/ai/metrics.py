"""Chỉ số đánh giá mô hình gợi ý (mục 6.3 của kế hoạch).

Với mỗi ứng viên, một phương pháp xếp ~10 tin; so thứ tự xếp với nhãn tay 0–3.
Nhãn nhị phân "phù hợp" khi nhãn >= 2. Kết quả là trung bình trên các ứng viên.
Các tin đồng điểm được xếp bằng bốc ngẫu nhiên cố định (seed) để không bị lợi/hại theo thứ tự đầu vào.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import cohen_kappa_score, ndcg_score, roc_auc_score

RELEVANT = 2


def _order(scores: np.ndarray, seed: int) -> np.ndarray:
    jitter = np.random.default_rng(seed).random(len(scores))
    return np.lexsort((jitter, -scores))  # điểm giảm dần, đồng điểm theo jitter


def precision_at_k(labels: np.ndarray, scores: np.ndarray, k: int = 5, seed: int = 0) -> float:
    top = _order(scores, seed)[:k]
    return float(np.mean(labels[top] >= RELEVANT)) if len(top) else 0.0


def mrr(labels: np.ndarray, scores: np.ndarray, seed: int = 0) -> float:
    for rank, idx in enumerate(_order(scores, seed), start=1):
        if labels[idx] >= RELEVANT:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(labels: np.ndarray, scores: np.ndarray, k: int = 10) -> float:
    if len(labels) < 2 or labels.max() == 0:
        return float("nan")  # không có tin phù hợp nào để xếp
    return float(ndcg_score([labels], [scores], k=k))


def spearman(labels: np.ndarray, scores: np.ndarray) -> float:
    if np.ptp(labels) == 0 or np.ptp(scores) == 0:
        return float("nan")
    return float(spearmanr(labels, scores).statistic)


def rank_metrics(df: pd.DataFrame, seed: int = 0) -> dict[str, float]:
    """`df` có cột candidate_id, label (0–3), score. Trả về trung bình theo ứng viên + ROC-AUC toàn cục."""
    rows = []
    for i, (_, g) in enumerate(df.groupby("candidate_id")):
        y, s = g["label"].to_numpy(), g["score"].to_numpy(dtype=float)
        rows.append(
            {
                "precision@5": precision_at_k(y, s, 5, seed + i),
                "ndcg@10": ndcg_at_k(y, s, 10),
                "mrr": mrr(y, s, seed + i),
                "spearman": spearman(y, s),
            }
        )
    res = pd.DataFrame(rows).mean(skipna=True).to_dict()
    binary = (df["label"] >= RELEVANT).astype(int)
    res["roc_auc"] = float(roc_auc_score(binary, df["score"])) if binary.nunique() == 2 else float("nan")
    res["n_candidates"] = int(df["candidate_id"].nunique())
    return res


def weighted_kappa(a: np.ndarray, b: np.ndarray) -> float:
    """Cohen's kappa có trọng số bình phương cho hai người gán nhãn (mục tiêu >= 0,6)."""
    return float(cohen_kappa_score(a, b, weights="quadratic"))


def merge_labels(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Quy tắc chốt nhãn: lệch >= 2 bậc trả -1 (cần thảo luận), lệch 1 bậc lấy trung bình làm tròn xuống."""
    a, b = np.asarray(a), np.asarray(b)
    merged = np.floor((a + b) / 2).astype(int)
    merged[np.abs(a - b) >= 2] = -1
    return merged


def prf1_micro(pred: list[set[str]], gold: list[set[str]]) -> dict[str, float]:
    """Precision/Recall/F1 (micro) cho kỹ năng trích được so với nhãn tay, gộp tất cả CV."""
    tp = sum(len(p & g) for p, g in zip(pred, gold))
    fp = sum(len(p - g) for p, g in zip(pred, gold))
    fn = sum(len(g - p) for p, g in zip(pred, gold))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def mae(pred: list[float], gold: list[float]) -> Optional[float]:
    return float(np.mean(np.abs(np.asarray(pred) - np.asarray(gold)))) if pred else None
