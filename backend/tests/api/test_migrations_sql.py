"""Migration chạy được từ DB trống, và SQL PostgreSQL (DDL + view BI) hợp lệ về cú pháp.

Lưu ý: không có máy chủ PostgreSQL trong môi trường test, nên SQL của view chỉ được kiểm tra bằng bộ phân tích cú pháp
của chính PostgreSQL (pglast); chưa được thực thi trên PostgreSQL thật.
"""
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app import db as dbmod
from app.models import Base

BACKEND = Path(__file__).resolve().parents[2]
ROOT = BACKEND.parent


def test_alembic_upgrade_creates_all_15_tables_and_downgrades():
    engine = dbmod.make_engine("sqlite://")
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")
        tables = set(inspect(conn).get_table_names()) - {"alembic_version"}
        assert tables == set(Base.metadata.tables) and len(tables) == 15
        command.downgrade(cfg, "base")
        assert set(inspect(conn).get_table_names()) - {"alembic_version"} == set()


def test_expected_15_tables_by_name():
    assert set(Base.metadata.tables) == {
        "users", "locations", "skills", "skill_aliases", "companies", "candidates", "resumes", "candidate_skills", "recruiters",
        "jobs", "job_skills", "applications", "application_status_history", "match_results", "saved_jobs",
    }


pglast = pytest.importorskip("pglast")


def test_views_sql_parses_as_postgresql():
    stmts = pglast.parse_sql((ROOT / "bi" / "views.sql").read_text(encoding="utf-8"))
    names = [s.stmt.view.relname for s in stmts]
    assert names == ["v_skill_supply_demand", "v_salary", "v_funnel", "v_funnel_stages"]


def test_views_reference_only_existing_columns():
    """Mọi cột bảng được view dùng phải tồn tại trong models (bắt lỗi đổi tên cột)."""
    import re

    sql = (ROOT / "bi" / "views.sql").read_text(encoding="utf-8")
    alias = {"s": "skills", "cs": "candidate_skills", "js": "job_skills", "j": "jobs", "c": "companies", "l": "locations",
             "a": "applications", "h": "application_status_history"}
    for a, col in set(re.findall(r"\b(s|cs|js|j|c|l|a|h)\.([a-z_]+)\b", sql)):
        assert col in Base.metadata.tables[alias[a]].columns, f"{alias[a]}.{col}"


def test_schema_sql_is_current_and_valid():
    import sys

    sys.path.insert(0, str(BACKEND))
    from scripts.dump_schema import OUT, build

    text = build()
    stmts = pglast.parse_sql(text)
    creates = [s for s in stmts if type(s.stmt).__name__ == "CreateStmt"]
    assert len(creates) == 15
    assert OUT.exists() and OUT.read_text(encoding="utf-8") == text, "backend/schema.sql đã cũ: chạy python -m scripts.dump_schema"
