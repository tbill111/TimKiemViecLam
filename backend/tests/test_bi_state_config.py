"""Cấu hình Superset được đọc từ biến môi trường, nếu thiếu thì từ tệp JSON do dịch vụ `bi-init` ghi (volume `bi_state`)."""
from __future__ import annotations

import json

from app.config import Settings


def test_bi_ids_fall_back_to_state_file(tmp_path, monkeypatch):
    state = tmp_path / "superset.json"
    state.write_text(json.dumps({"SUPERSET_DASHBOARD_ID": "uuid-1", "SUPERSET_FUNNEL_DATASET_ID": "3", "SUPERSET_FUNNEL_STAGES_DATASET_ID": "4"}), encoding="utf-8")
    monkeypatch.setenv("BI_STATE_FILE", str(state))
    for name in ("SUPERSET_DASHBOARD_ID", "SUPERSET_FUNNEL_DATASET_ID", "SUPERSET_FUNNEL_STAGES_DATASET_ID"):
        monkeypatch.delenv(name, raising=False)
    s = Settings()
    assert (s.dashboard_id, s.funnel_dataset_id, s.funnel_stages_dataset_id) == ("uuid-1", "3", "4")
    monkeypatch.setenv("SUPERSET_DASHBOARD_ID", "from-env")
    assert Settings().dashboard_id == "from-env"  # biến môi trường được ưu tiên


def test_bi_ids_empty_when_nothing_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("BI_STATE_FILE", str(tmp_path / "missing.json"))
    monkeypatch.delenv("SUPERSET_DASHBOARD_ID", raising=False)
    assert Settings().dashboard_id == ""
