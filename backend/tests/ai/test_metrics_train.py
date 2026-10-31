import time

import numpy as np
import pandas as pd
import pytest

from app.ai import scorers
from app.ai.embedder import HashingEmbedder
from app.ai.features import FEATURE_NAMES
from app.ai.metrics import (
    merge_labels,
    mae,
    mrr,
    ndcg_at_k,
    precision_at_k,
    prf1_micro,
    rank_metrics,
    weighted_kappa,
)
from app.ai.train import coefficient_table, cross_val_scores, fit_m4, m3_weights_from_m4, save_m3_weights, save_m4
from app.ai.types import CandidateInput, JobInput, ModelNotAvailable

EMB = HashingEmbedder()


def test_precision_mrr_ndcg_known_values():
    labels = np.array([3, 0, 2, 0, 1, 0])
    perfect = np.array([6, 1, 5, 2, 4, 3.0])
    assert precision_at_k(labels, perfect, k=2) == 1.0
    assert mrr(labels, perfect) == 1.0
    assert ndcg_at_k(labels, perfect, k=10) == pytest.approx(1.0)
    worst = -perfect
    assert mrr(labels, worst) < 1.0
    assert ndcg_at_k(labels, worst, k=10) < ndcg_at_k(labels, perfect, k=10)


def test_rank_metrics_perfect_vs_random():
    rng = np.random.default_rng(0)
    rows = []
    for cid in range(30):
        labels = rng.integers(0, 4, 10)
        for lab in labels:
            rows.append({"candidate_id": cid, "label": int(lab), "score": lab + rng.random() * 0.1})
    good = rank_metrics(pd.DataFrame(rows))
    rnd = rank_metrics(pd.DataFrame(rows).assign(score=lambda d: rng.random(len(d))))
    assert good["ndcg@10"] > rnd["ndcg@10"]
    assert good["roc_auc"] > 0.95 and good["precision@5"] > rnd["precision@5"]
    assert good["n_candidates"] == 30


def test_kappa_and_merge_rules():
    a = np.array([0, 1, 2, 3, 3, 0])
    assert weighted_kappa(a, a) == 1.0
    b = np.array([0, 2, 2, 3, 1, 3])
    merged = merge_labels(a, b)
    assert merged.tolist() == [0, 1, 2, 3, -1, -1]  # lệch 1 bậc: làm tròn xuống; lệch >= 2: -1 (thảo luận)


def test_prf1_micro_and_mae():
    pred = [{"A", "B"}, {"C"}]
    gold = [{"A"}, {"C", "D"}]
    r = prf1_micro(pred, gold)
    assert r["precision"] == pytest.approx(2 / 3) and r["recall"] == pytest.approx(2 / 3)
    assert mae([1.0, 2.0], [1.5, 2.0]) == pytest.approx(0.25)


def _synthetic(n_cand=40, per=10, seed=0):
    rng = np.random.default_rng(seed)
    X, y, g = [], [], []
    for c in range(n_cand):
        for _ in range(per):
            f = rng.random(6)
            label = int(f[0] > 0.6 and f[1] > 0.4)  # nhãn phụ thuộc skill_req và skill_pref
            X.append(f); y.append(label); g.append(c)
    return np.array(X), np.array(y), np.array(g)


def test_m4_group_cv_learns_signal_without_leakage():
    X, y, g = _synthetic()
    proba = cross_val_scores(X, y, g, n_splits=5)
    from sklearn.metrics import roc_auc_score

    assert roc_auc_score(y, proba) > 0.9
    coefs = coefficient_table(fit_m4(X, y))
    assert coefs["skill_req"] > coefs["edu"] and coefs["skill_pref"] > coefs["edu"]


def test_m4_save_load_and_score_pair(tmp_path, monkeypatch):
    X, y, g = _synthetic()
    model = fit_m4(X, y)
    monkeypatch.setattr(scorers, "MODELS_DIR", tmp_path)
    monkeypatch.setattr(scorers, "_m4_cache", None)
    monkeypatch.setattr(scorers, "_m3_cache", None)
    with pytest.raises(ModelNotAvailable):
        scorers.score_pair("m4", CandidateInput(1, ["A"]), JobInput(1, ["A"], []), EMB)
    version = save_m4(model, tmp_path / "m4.joblib")
    cand = CandidateInput(1, ["HTML", "CSS"], text="frontend", locations=["Hà Nội"], work_types=["Thực tập"])
    job = JobInput(1, ["HTML", "CSS"], ["Git"], location="Hà Nội", work_type_label="Thực tập", text="frontend")
    out = scorers.score_pair("m4", cand, job, EMB)
    assert out["model"] == "m4" and out["model_version"] == version and 0 <= out["total_score"] <= 100


def test_m3_weights_override_file(tmp_path, monkeypatch):
    X, y, _ = _synthetic()
    w = m3_weights_from_m4(fit_m4(X, y))
    assert sum(w.values()) == pytest.approx(1.0) and set(w) == set(FEATURE_NAMES)
    monkeypatch.setattr(scorers, "MODELS_DIR", tmp_path)
    monkeypatch.setattr(scorers, "_m3_cache", None)
    save_m3_weights(w, tmp_path / "m3_weights.json", "m3-test")
    weights, version = scorers.load_m3_weights(force=True)
    assert version == "m3-test" and weights["skill_req"] == pytest.approx(w["skill_req"])


def test_m1_and_m2_basic_behaviour():
    scorers.fit_tfidf(["frontend react html css", "kế toán thuế báo cáo", "backend python sql"])
    cand = CandidateInput(1, ["React"], text="lập trình frontend react html css")
    near = JobInput(1, ["React"], [], text="frontend react html css")
    far = JobInput(2, ["React"], [], text="kế toán thuế báo cáo")
    assert scorers.score_pair("m1", cand, near, EMB)["total_score"] > scorers.score_pair("m1", cand, far, EMB)["total_score"]
    assert scorers.score_pair("m2", cand, near, EMB)["total_score"] > scorers.score_pair("m2", cand, far, EMB)["total_score"]
    scorers._tfidf = None


def test_performance_500_jobs_under_two_seconds():
    rng = np.random.default_rng(1)
    skills = [f"Skill{i}" for i in range(60)]
    cand = CandidateInput(1, skills[:12], years_exp=1, edu=3, locations=["Hà Nội"], work_types=["Thực tập"],
                          embedding=EMB.encode(["cv"])[0])
    emb = EMB.encode(["jd"])[0]
    jobs = [
        JobInput(i, list(rng.choice(skills, 5, replace=False)), list(rng.choice(skills, 3, replace=False)),
                 location="Hà Nội", work_type_label="Thực tập", embedding=emb)
        for i in range(500)
    ]
    start = time.perf_counter()
    out = scorers.score_many("m3", cand, jobs, EMB)
    elapsed = time.perf_counter() - start
    assert len(out) == 500 and elapsed < 2.0, f"{elapsed:.2f}s"
