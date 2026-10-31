"""Công cụ phục vụ TEST: sinh nhãn MÔ PHỎNG bằng công thức. KHÔNG dùng làm nhãn nộp (nhãn thật xem backend/seed/labels/NGUON_NHAN.md).

    cd backend && python -m seed.make_pair_list && python -m seed.simulate_labels

Hai "người gán nhãn" giả lập cùng đọc một độ phù hợp tiềm ẩn của cặp (ứng viên, tin) rồi mỗi người cộng nhiễu và độ lệch riêng
(như hai người thật bất đồng nhẹ), sau đó quy về thang 0–3. Độ phù hợp tiềm ẩn dựa trên nhóm nghề, độ phủ kỹ năng bắt buộc/ưu tiên,
kinh nghiệm và học vấn – tức là cùng loại thông tin mà các mô hình dùng – nên mô hình dựa trên quy tắc sẽ trông tốt một cách
có hệ thống. Vì vậy mọi bảng số liệu sinh từ các file này chỉ chứng minh pipeline chạy được; phải thay bằng nhãn tay trước khi
báo cáo hiệu quả mô hình.

Ghi vào seed/labels/: labels_pairs_SYNTH_hung.csv, labels_pairs_SYNTH_hoanganh.csv, labels_cv_skills_SYNTH.csv.
"""
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

from app.ai.skills import has_skill

from .make_pair_list import near_groups, read_rows

HERE = Path(__file__).resolve().parent
DATA, LABELS = HERE / "data", HERE / "labels"
SEED = 2026

# (độ lệch, độ nhiễu riêng) của hai người gán nhãn giả lập
ANNOTATORS = {"hung": (0.03, 0.10), "hoanganh": (-0.03, 0.12)}
SHARED_NOISE = 0.07  # bất định thật của cặp mà cả hai cùng thấy


def _split(v: str) -> list[str]:
    return [x for x in v.split("|") if x]


def latent_fit(cand: dict[str, str], job: dict[str, str]) -> float:
    """Độ phù hợp tiềm ẩn trong [0, 1] (chưa nhiễu)."""
    skills = _split(cand["skills"])
    req, pref = _split(job["required_skills"]), _split(job["preferred_skills"])
    occ = 1.0 if cand["occupation"] == job["category"] else 0.5 if job["category"] in near_groups(cand["occupation"]) else 0.0
    req_cov = sum(has_skill(skills, s) for s in req) / len(req) if req else 1.0
    pref_cov = sum(has_skill(skills, s) for s in pref) / len(pref) if pref else 1.0
    need_years = float(job["min_years_exp"] or 0)
    exp_fit = 1.0 if need_years <= 0 else min(1.0, float(cand["years_exp"]) / need_years)
    need_edu = int(float(job["min_education"] or 0))
    edu_fit = 1.0 if int(cand["education_level"]) >= need_edu else 0.5 if int(cand["education_level"]) == need_edu - 1 else 0.0
    return 0.40 * occ + 0.35 * req_cov + 0.10 * pref_cov + 0.08 * exp_fit + 0.07 * edu_fit


def to_label(x: float) -> int:
    return 0 if x < 0.30 else 1 if x < 0.52 else 2 if x < 0.75 else 3


def simulate(candidates_csv: Path, jobs_csv: Path, template_csv: Path, seed: int = SEED) -> dict[str, list[tuple[str, str, int]]]:
    rng = random.Random(seed)
    cands = {r["candidate_id"]: r for r in read_rows(candidates_csv)}
    jobs = {r["external_id"]: r for r in read_rows(jobs_csv)}
    pairs = [(r["candidate_id"], r["job_id"]) for r in read_rows(template_csv)]
    out: dict[str, list[tuple[str, str, int]]] = {a: [] for a in ANNOTATORS}
    for cid, jid in pairs:
        base = latent_fit(cands[cid], jobs[jid]) + rng.gauss(0, SHARED_NOISE)
        for name, (bias, sigma) in ANNOTATORS.items():
            out[name].append((cid, jid, to_label(base + bias + rng.gauss(0, sigma))))
    return out


def simulate_cv_labels(manifest_csv: Path, seed: int = SEED) -> list[tuple[str, str, float]]:
    """Người đọc CV bỏ sót ~2% kỹ năng và thỉnh thoảng thêm nhầm một kỹ năng (~0,5%/kỹ năng)."""
    rng = random.Random(seed + 1)
    all_skills = [r["name"] for r in read_rows(DATA / "skills.csv")]
    rows = []
    for r in read_rows(manifest_csv):
        truth = _split(r["true_skills"])
        kept = [s for s in truth if rng.random() > 0.02]
        extra = [s for s in rng.sample(all_skills, 2) if s not in truth and rng.random() < 0.05 * 2]
        rows.append((r["cv_file"], "|".join(kept + extra[:1]), float(r["true_years_exp"])))
    return rows


def write_all(out_dir: Path = LABELS) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    result = simulate(DATA / "candidates_generated.csv", DATA / "jobs.csv", out_dir / "labels_pairs_template.csv")
    for name, rows in result.items():
        with open(out_dir / f"labels_pairs_SYNTH_{name}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["candidate_id", "job_id", "label"])
            w.writerows(rows)
    with open(out_dir / "labels_cv_skills_SYNTH.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cv_file", "skills", "years_exp"])
        w.writerows(simulate_cv_labels(DATA / "cv_manifest.csv"))
    (out_dir / "README_SYNTHETIC.md").write_text(
        "# Nhãn MÔ PHỎNG – không phải nhãn tay\n\n"
        "Các file `*_SYNTH*.csv` do `seed/simulate_labels.py` sinh để chạy trọn pipeline (huấn luyện M4, bảng M0–M4, ablation, kappa).\n"
        "Hai người gán nhãn giả lập đọc cùng độ phù hợp tiềm ẩn (nhóm nghề, độ phủ kỹ năng, kinh nghiệm, học vấn) rồi cộng nhiễu riêng, "
        "nên kết quả của các mô hình dựa trên quy tắc bị lạc quan có hệ thống. **Không dùng các bảng số liệu sinh từ đây làm kết luận về hiệu quả mô hình.**\n\n"
        "Khi Hoàng Hưng và Hoàng Anh gán nhãn thật, lưu `labels_pairs_hung.csv`, `labels_pairs_hoanganh.csv`, `labels_cv_skills.csv` ở đây rồi chạy lại "
        "3 notebook (không đặt biến `TH3_LABELS_A/B`, `TH3_CV_LABELS`, `TH3_OUT_DIR`) và xoá `models_store/m4.joblib` mô phỏng trước khi huấn luyện lại.\n",
        encoding="utf-8",
    )
    print(f"Đã ghi nhãn mô phỏng vào {out_dir}")


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    write_all()
