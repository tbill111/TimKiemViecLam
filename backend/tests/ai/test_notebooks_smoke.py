"""Chạy toàn bộ ô code của 3 notebook trên dữ liệu tổng hợp để chắc chắn notebook không lỗi.

Không kiểm tra giá trị số (dữ liệu tổng hợp); chỉ kiểm tra luồng, đường dẫn và các file đầu ra.
"""
from pathlib import Path

import nbformat
import pytest

from tests.ai import synth

REPO = Path(__file__).resolve().parents[3]
NOTEBOOKS = REPO / "notebooks"


def run_notebook(name: str, env: dict, monkeypatch) -> dict:
    nb = nbformat.read(NOTEBOOKS / f"{name}.ipynb", as_version=4)
    for k, v in env.items():
        monkeypatch.setenv(k, str(v))
    monkeypatch.chdir(NOTEBOOKS)
    ns: dict = {"__name__": "__notebook__"}
    for cell in nb.cells:
        if cell.cell_type == "code":
            lines = [ln for ln in cell.source.splitlines() if not ln.startswith(("%", "!"))]
            exec(compile("\n".join(lines), f"{name}.ipynb", "exec"), ns)
    return ns


@pytest.fixture()
def env(tmp_path):
    paths = synth.build(tmp_path / "data")
    (tmp_path / "labels").mkdir()
    for src, dst in ((paths["a"], "labels_pairs_hung.csv"), (paths["b"], "labels_pairs_hoanganh.csv"), (paths["cv_labels"], "labels_cv_skills.csv")):
        (tmp_path / "labels" / dst).write_bytes(src.read_bytes())
    return {
        "EMBEDDER": "hash",
        "TH3_DATA_DIR": tmp_path / "data",
        "TH3_LABELS_DIR": tmp_path / "labels",
        "TH3_OUT_DIR": tmp_path / "out",
        "TH3_MODELS_OUT": tmp_path / "models",
        "TH3_CV_DIR": paths["cv_dir"],
    }, tmp_path


def test_notebooks_exist():
    assert {p.name for p in NOTEBOOKS.glob("*.ipynb")} == {"01_parser_eval.ipynb", "02_train_m4.ipynb", "03_ranking_eval.ipynb"}


def test_parser_notebook_runs(env, monkeypatch):
    env_vars, tmp = env
    run_notebook("01_parser_eval", env_vars, monkeypatch)
    assert (tmp / "out" / "parser_eval.csv").exists()


def test_train_then_ranking_notebooks_run(env, monkeypatch):
    from app.ai import embedder

    embedder.set_embedder(None)  # nạp lại theo EMBEDDER=hash
    env_vars, tmp = env
    run_notebook("02_train_m4", env_vars, monkeypatch)
    assert (tmp / "models" / "m4.joblib").exists() and (tmp / "out" / "m4_coefficients.csv").exists()
    run_notebook("03_ranking_eval", env_vars, monkeypatch)
    for f in ("model_comparison.csv", "ablation_m3.csv", "error_analysis_m3.csv", "kappa.csv"):
        assert (tmp / "out" / f).exists(), f
    embedder.set_embedder(None)
