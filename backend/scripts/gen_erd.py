"""Sinh ERD (DBML) từ app/models.py để không bao giờ lệch schema thật.

    cd backend && python -m scripts.gen_erd          # ghi docs/erd/erd.dbml
Dán nội dung vào dbdiagram.io để xuất ảnh PNG.
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.dialects import postgresql

from app import models  # noqa: F401
from app.db import Base

OUT = Path(__file__).resolve().parents[2] / "docs" / "erd" / "erd.dbml"

# Ba nhóm chính theo đề bài: ứng viên, nhà tuyển dụng, tin tuyển dụng (cộng nhóm tuyển dụng, AI và danh mục)
GROUPS = {
    "Ung_vien": ["users", "candidates", "resumes", "candidate_skills", "saved_jobs"],
    "Nha_tuyen_dung": ["companies", "recruiters"],
    "Tin_tuyen_dung": ["jobs", "job_skills"],
    "Tuyen_dung": ["applications", "application_status_history"],
    "AI_va_danh_muc": ["match_results", "skills", "skill_aliases", "locations"],
}


def build() -> str:
    dialect = postgresql.dialect()
    lines = ["// SmartCareer v2 – ERD. Sinh tự động bởi backend/scripts/gen_erd.py từ app/models.py.", ""]
    refs: list[str] = []
    for table in Base.metadata.sorted_tables:
        lines.append(f"Table {table.name} {{")
        for col in table.columns:
            attrs = []
            if col.primary_key:
                attrs.append("pk")
                if col.autoincrement is True or (col.autoincrement == "auto" and col.type.python_type is int and len(table.primary_key.columns) == 1):
                    attrs.append("increment")
            if not col.nullable and not col.primary_key:
                attrs.append("not null")
            if col.unique:
                attrs.append("unique")
            type_name = col.type.compile(dialect=dialect).lower().replace("timestamp without time zone", "timestamp").replace(", ", ",").replace(" ", "_")
            lines.append(f"  {col.name} {type_name}" + (f" [{', '.join(attrs)}]" if attrs else ""))
            for fk in col.foreign_keys:
                refs.append(f"Ref: {table.name}.{col.name} > {fk.column.table.name}.{fk.column.name}")
        constraints = [c for c in table.constraints if c.__class__.__name__ == "CheckConstraint" and c.name]
        uniques = [c for c in table.constraints if c.__class__.__name__ == "UniqueConstraint" and len(c.columns) > 1]
        if constraints or uniques:
            lines.append("")
            lines.append("  Note: '''")
            for c in constraints:
                lines.append(f"  CHECK {c.name}: {c.sqltext}")
            for c in uniques:
                lines.append(f"  UNIQUE ({', '.join(col.name for col in c.columns)})")
            lines.append("  '''")
        lines += ["}", ""]
    lines += sorted(set(refs)) + [""]
    for group, tables in GROUPS.items():
        lines += [f"TableGroup {group} {{", *[f"  {t}" for t in tables], "}", ""]
    covered = {t for ts in GROUPS.values() for t in ts}
    assert covered == set(Base.metadata.tables), covered ^ set(Base.metadata.tables)
    return "\n".join(lines)


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"Đã ghi {OUT}")
