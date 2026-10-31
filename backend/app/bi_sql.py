"""Tạo/xoá 4 view BI từ bi/views.sql (chỉ PostgreSQL). Dùng chung cho migration 0002 và `seed.load_seed --reset`."""
from __future__ import annotations

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
    out = []
    for stmt in VIEWS_SQL.read_text(encoding="utf-8").split(";"):
        body = "\n".join(ln for ln in stmt.splitlines() if not ln.strip().startswith("--")).strip()
        if body:
            out.append(body)
    return out


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
