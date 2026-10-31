import numpy as np
import pandas as pd
import pytest

from app.ai import datasets, evaluate, metrics, scorers, train
from app.ai.embedder import HashingEmbedder
from app.ai.types import JobInput
from tests.ai import synth

EMB = HashingEmbedder()


@pytest.fixture(scope="module")
def data(tmp_path_factory):
    paths = synth.build(tmp_path_factory.mktemp("synth"))
    cands, jobs = datasets.load_candidates(paths["cands"]), datasets.load_jobs(paths["jobs"])
    datasets.attach_embeddings(cands, EMB)
    datasets.attach_embeddings(jobs, EMB)
    labels = datasets.load_labels(paths["a"], paths["b"])
    labels["label"] = metrics.merge_labels(labels["label_labels_pairs_a"].to_numpy(), labels["label_labels_pairs_b"].to_numpy())
    labels = labels[labels["label"] >= 0].reset_index(drop=True)  # bỏ cặp lệch >= 2 chờ thảo luận
    return paths, cands, jobs, labels


def test_loaders_follow_documented_format(data):
    paths, cands, jobs, labels = data
    assert len(jobs) == 24 and len(cands) == 24
    j = jobs["job-001"]
    assert j.work_type_label == "Thực tập" and j.required[:2] == ["HTML", "CSS"] and j.min_edu == 3
    assert cands["cand-0001"].work_types == ["Thực tập"] and cands["cand-0001"].embedding is not None
    assert {"candidate_id", "job_id", "label_labels_pairs_a", "label_labels_pairs_b"} <= set(labels.columns)


def test_load_template_csv_from_repo():
    root = datasets.Path(__file__).resolve().parents[2] / "seed" / "data"
    jobs = datasets.load_jobs(root / "jobs.csv")
    assert len(jobs) == 3 and jobs["job-003"].salary_min is None and jobs["job-003"].work_type_label == "Toàn thời gian"


def test_kappa_between_two_raters_reasonable(data):
    _, _, _, labels = data
    k = metrics.weighted_kappa(labels["label_labels_pairs_a"].to_numpy(), labels["label_labels_pairs_b"].to_numpy())
    assert 0.5 < k <= 1.0


def test_evaluate_models_table_shape_and_baseline_sanity(data):
    _, cands, jobs, labels = data
    table = evaluate.evaluate_models(labels, cands, jobs, models=("m0", "m1", "m2", "m3"), embedder=EMB)
    assert list(table.index) == ["m0", "m1", "m2", "m3"]
    assert {"precision@5", "ndcg@10", "mrr", "spearman", "roc_auc", "ms_per_pair"} <= set(table.columns)
    # nhãn tổng hợp suy ra từ độ trùng kỹ năng nên M0/M3 phải xếp tốt hơn ngẫu nhiên
    assert table.loc["m0", "roc_auc"] > 0.8 and table.loc["m3", "roc_auc"] > 0.7


def test_m4_out_of_fold_flow(data, tmp_path, monkeypatch):
    _, cands, jobs, labels = data
    X, feats = evaluate.build_feature_matrix(labels, cands, jobs, EMB)
    y = (labels["label"] >= 2).astype(int).to_numpy()
    groups = labels["candidate_id"].to_numpy()
    oof = train.cross_val_scores(X, y, groups, n_splits=5)
    table = evaluate.evaluate_models(labels, cands, jobs, models=("m3", "m4"), m4_scores=oof * 100, embedder=EMB)
    assert table.loc["m4", "roc_auc"] > 0.7
    model = train.fit_m4(X, y)
    assert set(train.coefficient_table(model)) == set(scorers.FEATURE_NAMES)


def test_ablation_lists_every_feature(data):
    _, cands, jobs, labels = data
    _, feats = evaluate.build_feature_matrix(labels, cands, jobs, EMB)
    table = evaluate.ablation_m3(labels, feats)
    assert list(table["feature_removed"]) == ["(không bỏ)", *scorers.FEATURE_NAMES]
    assert table.loc[0, "delta"] == 0
    # bỏ skill_req (đặc trưng chi phối nhãn tổng hợp) phải làm nDCG giảm
    assert table.set_index("feature_removed").loc["skill_req", "delta"] < 0


def test_error_analysis_returns_worst_pairs(data):
    _, cands, jobs, labels = data
    worst = evaluate.error_analysis(labels, cands, jobs, "m3", n=5, embedder=EMB)
    assert len(worst) == 5
    assert worst["error"].abs().is_monotonic_decreasing


def test_evaluate_parser_tiers_monotonic_recall(data):
    paths, *_ = data
    gold, years = datasets.load_cv_labels(paths["cv_labels"])
    table = evaluate.evaluate_parser(paths["cv_dir"], gold, years, embedder=EMB)
    assert list(table["tier"]) == ["T1", "T1+2", "T1+2+3"]
    assert table["recall"].is_monotonic_increasing or table["recall"].nunique() == 1  # thêm tầng không làm giảm recall
    assert table.loc[0, "f1"] > 0.9
    assert table.attrs["years_mae"] == pytest.approx(0.1, abs=0.15)


def test_fairness_header_change_does_not_change_scores():
    body = "Mục tiêu\nFrontend Developer\nKỹ năng\nReact, Git, HTML, CSS\nKinh nghiệm\nIntern 06/2024 - 08/2024\nHọc vấn\nĐại học Thủy lợi\n"
    a = ("Nguyễn Văn An\nNam, 21 tuổi\nan@example.com\n" + body).encode()
    b = ("Trần Thị Bích\nNữ, 24 tuổi\nbich@example.com\n" + body).encode()
    job = JobInput(1, ["HTML", "CSS", "React"], ["Git"], text="frontend react")
    res = evaluate.fairness_check(a, b, "cv.txt", job, embedder=EMB)
    assert res["identical"], res
