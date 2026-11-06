"""M4–M6: ba họ mô hình học máy (Logistic Regression, Random Forest, Gradient Boosting) trên 6 đặc trưng."""
import numpy as np
import pytest
from sklearn.metrics import roc_auc_score

from app.ai import scorers, train
from app.ai.embedder import HashingEmbedder
from app.ai.features import FEATURE_NAMES
from app.ai.types import ML_MODELS, MODELS, CandidateInput, JobInput, ModelNotAvailable

EMB = HashingEmbedder()


def _synthetic(n_cand=40, per=10, seed=0, nonlinear=False):
    rng = np.random.default_rng(seed)
    X, y, g = [], [], []
    for c in range(n_cand):
        for _ in range(per):
            f = rng.random(6)
            if nonlinear:  # tương tác giữa hai đặc trưng: mô hình tuyến tính khó học, cây học được
                label = int((f[0] > 0.5) != (f[1] > 0.5))
            else:
                label = int(f[0] > 0.6 and f[1] > 0.4)
            X.append(f); y.append(label); g.append(c)
    return np.array(X), np.array(y), np.array(g)


def test_model_registry_has_seven_models_and_three_ml():
    assert MODELS == ("m0", "m1", "m2", "m3", "m4", "m5", "m6")
    assert ML_MODELS == ("m4", "m5", "m6")
    assert set(train.KINDS) == {"logreg", "random_forest", "gradient_boosting"}


@pytest.mark.parametrize("kind", train.KINDS)
def test_each_family_learns_signal_with_group_cv(kind):
    X, y, g = _synthetic()
    proba = train.cross_val_scores(X, y, g, n_splits=5, kind=kind)
    assert roc_auc_score(y, proba) > 0.9


def test_tree_models_capture_interaction_that_logreg_cannot():
    X, y, g = _synthetic(nonlinear=True)
    auc = {k: roc_auc_score(y, train.cross_val_scores(X, y, g, kind=k)) for k in train.KINDS}
    assert auc["logreg"] < 0.65, auc
    assert auc["random_forest"] > 0.85 and auc["gradient_boosting"] > 0.85, auc


def test_group_cv_never_shares_candidates_between_train_and_test():
    X, y, g = _synthetic(n_cand=12)
    for tr, te in train._group_splits(X, y, g, 5):
        assert not set(g[tr]) & set(g[te])


def test_tuned_logreg_picks_c_from_grid_without_using_test_fold():
    X, y, g = _synthetic()
    assert train.best_logreg_c(X, y, g) in train.LOGREG_C_GRID
    proba = train.cross_val_scores(X, y, g, kind="logreg", tune=True)
    assert roc_auc_score(y, proba) > 0.9


def test_feature_importance_table_covers_all_features():
    X, y, _ = _synthetic()
    for kind in train.KINDS:
        table = train.feature_importance_table(train.fit_model(kind, X, y))
        assert set(table) == set(FEATURE_NAMES)
    rf = train.feature_importance_table(train.fit_model("random_forest", X, y))
    assert rf["skill_req"] > rf["edu"] and sum(rf.values()) == pytest.approx(1.0)


@pytest.mark.parametrize("model_id,kind", [("m5", "random_forest"), ("m6", "gradient_boosting")])
def test_m5_m6_unavailable_until_trained_then_score_pair(tmp_path, monkeypatch, model_id, kind):
    X, y, _ = _synthetic()
    monkeypatch.setattr(scorers, "MODELS_DIR", tmp_path)
    monkeypatch.setattr(scorers, f"_{model_id}_cache", None)
    cand = CandidateInput(1, ["HTML", "CSS"], text="frontend", locations=["Hà Nội"], work_types=["Thực tập"])
    job = JobInput(1, ["HTML", "CSS"], ["Git"], location="Hà Nội", work_type_label="Thực tập", text="frontend")
    with pytest.raises(ModelNotAvailable):
        scorers.score_pair(model_id, cand, job, EMB)
    version = train.save_model(train.fit_model(kind, X, y), tmp_path / f"{model_id}.joblib", model_id, version=f"{model_id}-test")
    out = scorers.score_pair(model_id, cand, job, EMB)
    assert out["model"] == model_id and out["model_version"] == version == f"{model_id}-test"
    assert 0 <= out["total_score"] <= 100 and set(out["components"]) == set(FEATURE_NAMES)


def test_evaluate_models_skips_untrained_ml_by_default_and_uses_oof_when_given(tmp_path, monkeypatch):
    import pandas as pd

    from app.ai import evaluate

    monkeypatch.setattr(scorers, "MODELS_DIR", tmp_path)
    for name in ("_m4_cache", "_m5_cache", "_m6_cache"):
        monkeypatch.setattr(scorers, name, None)
    cands = {f"c{i}": CandidateInput(i, ["A", "B"][: 1 + i % 2], text=f"t{i}") for i in range(6)}
    jobs = {f"j{i}": JobInput(i, ["A", "B"], [], text=f"j{i}") for i in range(4)}
    rows = [(c, j, (hash((c, j)) % 4)) for c in cands for j in jobs]
    labels = pd.DataFrame(rows, columns=["candidate_id", "job_id", "label"])
    table = evaluate.evaluate_models(labels, cands, jobs, embedder=EMB)
    assert list(table.index) == ["m0", "m1", "m2", "m3"]  # M4–M6 chưa huấn luyện nên bị bỏ qua
    oof = np.linspace(0, 100, len(labels))
    table = evaluate.evaluate_models(labels, cands, jobs, embedder=EMB, ml_scores={"m4": oof, "m5": oof, "m6": oof})
    assert {"m4", "m5", "m6"} <= set(table.index)


def test_score_many_batch_equals_score_pair_for_ml_models(tmp_path, monkeypatch):
    X, y, _ = _synthetic()
    monkeypatch.setattr(scorers, "MODELS_DIR", tmp_path)
    cand = CandidateInput(1, ["HTML", "CSS"], text="frontend", locations=["Hà Nội"], work_types=["Thực tập"])
    jobs = [JobInput(i, ["HTML", "CSS", "React"][: 1 + i % 3], ["Git"], location="Hà Nội", work_type_label="Thực tập", text=f"job {i}") for i in range(7)]
    for model_id, kind in (("m4", "logreg"), ("m5", "random_forest"), ("m6", "gradient_boosting")):
        monkeypatch.setattr(scorers, f"_{model_id}_cache", None)
        train.save_model(train.fit_model(kind, X, y), tmp_path / f"{model_id}.joblib", model_id)
        batch = scorers.score_many(model_id, cand, jobs, EMB)
        single = [scorers.score_pair(model_id, cand, j, EMB) for j in jobs]
        assert [b["total_score"] for b in batch] == [s["total_score"] for s in single]
        assert all(b["model"] == model_id for b in batch)
