import numpy as np
import pytest

from app.ai.embedder import HashingEmbedder
from app.ai.explain import explain
from app.ai.features import compute_features
from app.ai.scorers import M3_CAP, score_m3, score_pair
from app.ai.types import CandidateInput, JobInput

EMB = HashingEmbedder()


def job(**kw) -> JobInput:
    base = dict(id=1, required=["HTML", "CSS", "React"], preferred=["TypeScript", "Git"], min_years=0, min_edu=0,
                location="Hà Nội", work_type_label="Thực tập", text="frontend react intern")
    base.update(kw)
    return JobInput(**base)


def cand(**kw) -> CandidateInput:
    base = dict(id=1, skills=["HTML", "CSS", "React", "Git"], years_exp=0, edu=3, locations=["Hà Nội"],
                work_types=["Thực tập"], text="sinh viên frontend react")
    base.update(kw)
    return CandidateInput(**base)


def test_features_known_pair():
    f = compute_features(cand(), job(), EMB)
    assert f.values["skill_req"] == 1.0
    assert f.values["skill_pref"] == 0.5  # có Git, thiếu TypeScript
    assert f.values["exp"] == 1.0 and f.values["edu"] == 1.0
    assert f.values["pref"] == 1.0
    assert f.missing_preferred == ["TypeScript"]
    assert 0.0 <= f.values["semantic"] <= 1.0


def test_features_no_preferred_means_full_score():
    assert compute_features(cand(), job(preferred=[]), EMB).values["skill_pref"] == 1.0


def test_experience_and_education_rules():
    f = compute_features(cand(years_exp=1, edu=2), job(min_years=2, min_edu=3), EMB)
    assert f.values["exp"] == 0.5
    assert f.values["edu"] == 0.5  # thấp hơn một bậc
    assert compute_features(cand(edu=1), job(min_edu=3), EMB).values["edu"] == 0.0


def test_preference_remote_and_salary():
    f = compute_features(cand(locations=["Đà Nẵng"], work_types=["Remote"]), job(location="Remote", work_type_label="Remote"), EMB)
    assert f.values["pref"] == 1.0
    f2 = compute_features(cand(sal_min=10, sal_max=15), job(salary_min=3, salary_max=5), EMB)
    assert f2.values["pref"] == pytest.approx(2 / 3)  # địa điểm + hình thức khớp, lương không giao nhau


def test_m3_cap_when_missing_over_half_required():
    c = cand(skills=["Git"], text=job().text)  # thiếu cả 3 kỹ năng bắt buộc nhưng văn bản trùng JD
    j = job()
    out = score_m3(c, j, EMB)
    assert out["total_score"] <= M3_CAP
    assert len(out["missing_required"]) == 3


def test_m3_full_match_scores_high_and_in_range():
    j = job()
    out = score_m3(cand(skills=["HTML", "CSS", "React", "TypeScript", "Git"], text=j.text), j, EMB)
    assert 85 <= out["total_score"] <= 100
    assert set(out["components"]) == {"skill_req", "skill_pref", "semantic", "exp", "edu", "pref"}


def test_cv_empty_does_not_crash():
    out = score_pair("m3", cand(skills=[], text=""), job(), EMB)
    assert 0 <= out["total_score"] <= 50


def test_embeddings_prefilled_are_used():
    v = np.ones(384, dtype=np.float32) / np.sqrt(384)
    f = compute_features(cand(embedding=v), job(embedding=v), EMB)
    assert f.values["semantic"] == pytest.approx(1.0, abs=1e-5)


def test_explain_template():
    s = explain(72, ["React", "Git"], [], ["TypeScript"], ["REST API"])
    assert s == "Khớp 72/100. Đã có React, Git. Thiếu TypeScript (bắt buộc) và REST API (ưu tiên)."
    assert "Đáp ứng đủ" in explain(100, ["A"], [], [], [])
    assert explain(0, [], [], ["A"], []) == "Khớp 0/100. Thiếu A (bắt buộc)."


def test_score_pair_unknown_model():
    with pytest.raises(ValueError):
        score_pair("m9", cand(), job())
