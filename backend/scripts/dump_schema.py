"""Xuất DDL PostgreSQL của 15 bảng + 4 view BI ra backend/schema.sql (không cần máy chủ CSDL).

    cd backend && python -m scripts.dump_schema
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from app import models  # noqa: F401
from app.db import Base

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parents[1] / "schema.sql"


def build() -> str:
    dialect = postgresql.dialect()
    parts = ["-- SmartCareer v2: CSDL tác nghiệp (PostgreSQL 16). Sinh tự động từ app/models.py bằng scripts/dump_schema.py.", ""]
    for table in Base.metadata.sorted_tables:
        parts.append(str(CreateTable(table).compile(dialect=dialect)).strip() + ";")
        parts += [str(CreateIndex(ix).compile(dialect=dialect)).strip() + ";" for ix in sorted(table.indexes, key=lambda i: i.name or "")]
        parts.append("")
    parts += ["-- ===== View BI (bi/views.sql) =====", "", (ROOT / "bi" / "views.sql").read_text(encoding="utf-8")]
    return "\n".join(parts)


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"Đã ghi {OUT}")
