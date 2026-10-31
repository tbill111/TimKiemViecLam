"""Chạy lần lượt 3 notebook đánh giá và lưu kết quả vào chính file .ipynb (cần nbclient, ipykernel).

Nên chạy trong container `api` để có model embedding thật, ví dụ (nhãn mô phỏng, xem backend/seed/labels/README_SYNTHETIC.md):

    docker run --rm -v "$PWD:/work" -w /work/notebooks -e EMBEDDER=st \
      -e TH3_LABELS_A=labels_pairs_SYNTH_hung.csv -e TH3_LABELS_B=labels_pairs_SYNTH_hoanganh.csv \
      -e TH3_CV_LABELS=labels_cv_skills_SYNTH.csv -e TH3_OUT_DIR=/work/docs/report/tables_synthetic \
      -e TH3_M4_VERSION=m4-SYNTHETIC-labels \
      -e TH3_FAIR_A=/work/backend/seed/fairness/cv_fair_a.txt -e TH3_FAIR_B=/work/backend/seed/fairness/cv_fair_b.txt \
      tkiemvieclam-api sh -c "pip install -q nbclient ipykernel && python -m ipykernel install --user --name python3 && python /work/scripts/run_notebooks.py"

Với nhãn tay thật: bỏ các biến TH3_LABELS_A/B, TH3_CV_LABELS, TH3_OUT_DIR, TH3_M4_VERSION.
"""
from __future__ import annotations

import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

NOTEBOOKS = Path(__file__).resolve().parents[1] / "notebooks"
ORDER = ["01_parser_eval.ipynb", "02_train_m4.ipynb", "03_ranking_eval.ipynb"]


def main() -> int:
    for name in ORDER:
        nb = nbformat.read(NOTEBOOKS / name, as_version=4)
        print(f"== {name}", flush=True)
        NotebookClient(nb, timeout=1800, kernel_name="python3", resources={"metadata": {"path": str(NOTEBOOKS)}}).execute()
        nbformat.write(nb, NOTEBOOKS / name)
        for cell in nb.cells:
            for out in cell.get("outputs", []):
                text = out.get("text") or out.get("data", {}).get("text/plain", "")
                if text and out.get("name") != "stderr":
                    print(text.strip()[:600])
    return 0


if __name__ == "__main__":
    sys.exit(main())
