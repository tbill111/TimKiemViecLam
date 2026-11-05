"""`alembic upgrade head` phải chạy được trên PostgreSQL TRỐNG (đúng như `docker compose up` trên máy sạch).

Lỗi từng gặp: 0001 dùng create_all trên metadata hiện tại (đã gồm bảng `labeling_tasks`) rồi 0003 tạo lại bảng đó → DuplicateTable.
Test này chỉ chạy khi có TEST_DATABASE_URL trỏ tới một CSDL PostgreSQL dùng riêng cho kiểm thử (sẽ bị xoá sạch)."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text

URL = os.getenv("TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not URL.startswith("postgresql"), reason="cần TEST_DATABASE_URL (PostgreSQL)")

BACKEND = Path(__file__).resolve().parents[2]
VIEWS = {"v_skill_supply_demand", "v_salary", "v_funnel", "v_funnel_stages", "vw_candidate_skills", "vw_salary_trends", "vw_ai_matching_stats"}


def _wipe(engine):
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


def _alembic(command: str, target: str):
    from alembic import command as cmd
    from alembic.config import Config

    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    old = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = URL
    try:
        getattr(cmd, command)(cfg, target)
    finally:
        if old is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = old


def test_upgrade_head_on_empty_postgres_creates_all_tables_and_views():
    engine = create_engine(URL)
    _wipe(engine)
    _alembic("upgrade", "head")
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    assert {"users", "candidates", "jobs", "applications", "application_status_history", "labeling_tasks", "alembic_version"} <= tables
    assert len(tables - {"alembic_version", "labeling_tasks"}) == 15
    with engine.connect() as conn:
        views = {r[0] for r in conn.execute(text("SELECT table_name FROM information_schema.views WHERE table_schema='public'"))}
    assert VIEWS <= views, VIEWS - views
    _alembic("upgrade", "head")  # chạy lại không lỗi (idempotent)
    _wipe(engine)


def test_downgrade_to_base_then_upgrade_again():
    engine = create_engine(URL)
    _wipe(engine)
    _alembic("upgrade", "head")
    _alembic("downgrade", "base")
    assert not (set(inspect(engine).get_table_names()) - {"alembic_version"})
    _alembic("upgrade", "head")
    _wipe(engine)
