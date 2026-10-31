"""M0 bằng Python phải cho đúng kết quả của calculateSkillMatch (TypeScript) trên 84 ca (7 hồ sơ x 12 tin).

Tái tạo dữ liệu chuẩn:  npx tsx scripts/export-golden.ts
"""
import json
from pathlib import Path

import pytest

from app.ai.scorers import score_m0
from app.ai.types import CandidateInput, JobInput

GOLDEN = json.loads((Path(__file__).with_name("m0_golden.json")).read_text(encoding="utf-8"))["cases"]


def _inputs(case):
    p, j = case["profile"], case["job"]
    cand = CandidateInput(id=0, skills=p["skills"], locations=p["preferredLocations"], work_types=p["preferredWorkTypes"])
    job = JobInput(id=0, required=j["requiredSkills"], preferred=j["preferredSkills"], location=j["location"], work_type_label=j["workType"])
    return cand, job


def test_golden_has_expected_size():
    assert len(GOLDEN) == 84


@pytest.mark.parametrize("case", GOLDEN, ids=lambda c: f"{c['profile']['id']}-{c['job']['id']}")
def test_m0_matches_typescript(case):
    exp = case["expected"]
    got = score_m0(*_inputs(case))
    assert got["total_score"] == exp["matchScore"]
    assert got["components"]["skill_req"] == exp["requiredScore"]
    assert got["components"]["skill_pref"] == exp["preferredScore"]
    assert got["components"]["pref"] == exp["preferenceScore"]
    assert got["matched_required"] == exp["matchedSkills"]
    assert got["missing_required"] == exp["missingSkills"]
    assert got["matched_preferred"] == exp["matchedPreferred"]
    assert got["missing_preferred"] == exp["missingPreferred"]
    assert got["location_match"] == exp["locationMatch"]
    assert got["work_type_match"] == exp["workTypeMatch"]
