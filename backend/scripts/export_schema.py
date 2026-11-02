"""Export the current SQLAlchemy model metadata as PostgreSQL DDL."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.schema import CreateIndex, CreateTable
from sqlalchemy.dialects import postgresql

from app import models  # noqa: F401
from app.db import Base

destination = Path(__file__).resolve().parents[1] / "schema.sql"
dialect = postgresql.dialect()
parts = ["-- Generated from app.models.entities; apply Alembic migrations for BI views.\n"]
for table in Base.metadata.sorted_tables:
    parts.append(str(CreateTable(table).compile(dialect=dialect)).strip() + ";\n")
    for index in table.indexes:
        parts.append(str(CreateIndex(index).compile(dialect=dialect)).strip() + ";\n")
destination.write_text("\n".join(parts), encoding="utf-8")
print(f"Wrote {destination}")
