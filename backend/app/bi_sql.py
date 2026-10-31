"""Tạo/xoá 4 view BI từ bi/views.sql (chỉ PostgreSQL). Dùng chung cho migration 0002 và `seed.load_seed --reset`."""
from __future__ import annotations

import re
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Connection

# backend/app/bi_sql.py → parents[2] là thư mục gốc repo (hoặc /srv trong container)
VIEWS_SQL = Path(__file__).resolve().parents[2] / "bi" / "views.sql"
VIEWS = ("v_skill_supply_demand", "v_salary", "v_funnel", "v_funnel_stages")

GRANT = """
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bi_reader') THEN
        GRANT USAGE ON SCHEMA public TO bi_reader;
        GRANT SELECT ON v_skill_supply_demand, v_salary, v_funnel, v_funnel_stages TO bi_reader;
    END IF;
END
$$
"""


def statements() -> list[str]:
    """Tách bi/views.sql thành từng câu lệnh. Phải bỏ chú thích TRƯỚC khi tách theo ';' (chú thích có thể chứa dấu ';')."""
    lines = (re.sub(r"--.*$", "", ln) for ln in VIEWS_SQL.read_text(encoding="utf-8").splitlines())
    return [stmt.strip() for stmt in "\n".join(lines).split(";") if stmt.strip()]


def apply_views(conn: Connection) -> None:
    if conn.dialect.name != "postgresql":
        return
    for stmt in statements():
        conn.execute(text(stmt))
    conn.execute(text(GRANT))


def drop_views(conn: Connection) -> None:
    if conn.dialect.name != "postgresql":
        return
    for v in reversed(VIEWS):
        conn.execute(text(f"DROP VIEW IF EXISTS {v} CASCADE"))
