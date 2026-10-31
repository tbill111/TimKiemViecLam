"""Nhãn mô phỏng: tất định, đủ thang 0–3, hai người bất đồng vừa phải và luôn được gắn cờ là mô phỏng."""
from pathlib import Path

import numpy as np
import pandas as pd

from app.ai.metrics import weighted_kappa
from seed import simulate_labels as sim

LABELS = Path(sim.LABELS)


def test_simulation_is_deterministic_and_covers_the_scale():
    template = LABELS / "labels_pairs_template.csv"
    a = sim.simulate(sim.DATA / "candidates_generated.csv", sim.DATA / "jobs.csv", template)
    b = sim.simulate(sim.DATA / "candidates_generated.csv", sim.DATA / "jobs.csv", template)
    assert a == b
    assert len(a["hung"]) == len(a["hoanganh"]) == 300
    for rows in a.values():
        assert {r[2] for r in rows} == {0, 1, 2, 3}


def test_two_simulated_annotators_agree_reasonably_but_not_perfectly():
    a = pd.read_csv(LABELS / "labels_pairs_SYNTH_hung.csv")
    b = pd.read_csv(LABELS / "labels_pairs_SYNTH_hoanganh.csv")
    assert list(zip(a.candidate_id, a.job_id)) == list(zip(b.candidate_id, b.job_id))
    k = weighted_kappa(a.label.to_numpy(), b.label.to_numpy())
    assert 0.6 <= k < 0.99, k  # đạt mục tiêu kappa nhưng không trùng khít
    assert (a.label != b.label).any()


def test_fit_is_higher_for_same_occupation_and_full_skill_coverage():
    cand = {"occupation": "Frontend Development", "skills": "HTML|CSS|JavaScript|React|Git", "years_exp": "1", "education_level": "3"}
    job = {"category": "Frontend Development", "required_skills": "HTML|CSS|React", "preferred_skills": "Git", "min_years_exp": "0", "min_education": "3"}
    other = {**job, "category": "Digital Marketing", "required_skills": "Viết nội dung|Mạng xã hội", "preferred_skills": ""}
    assert sim.latent_fit(cand, job) > 0.9 > sim.latent_fit(cand, other)
    assert sim.to_label(0.9) == 3 and sim.to_label(0.1) == 0


def test_synthetic_files_are_flagged_by_name_and_notice():
    notice = (LABELS / "README_SYNTHETIC.md").read_text(encoding="utf-8")
    assert "MÔ PHỎNG" in notice and "Không dùng" in notice
    assert not (LABELS / "labels_pairs_hung.csv").exists(), "file nhãn tay thật phải do người gán tạo, không do trình sinh"
    assert not (LABELS / "labels_cv_skills.csv").exists()
