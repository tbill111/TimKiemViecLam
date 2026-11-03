"""Sinh ERD (DBML) từ app/models/entities.py để không bao giờ lệch schema thật.

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
    lines = ["// SmartCareer v2 – ERD. Sinh tự động bởi backend/scripts/gen_erd.py từ app/models/entities.py.", ""]
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
        constraints = sorted((c for c in table.constraints if c.__class__.__name__ == "CheckConstraint" and c.name), key=lambda c: c.name)
        uniques = sorted((c for c in table.constraints if c.__class__.__name__ == "UniqueConstraint" and len(c.columns) > 1), key=lambda c: c.name or "")
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


PUML_OUT = OUT.with_suffix(".puml")
GROUP_TITLE = {"Ung_vien": "Ứng viên", "Nha_tuyen_dung": "Nhà tuyển dụng", "Tin_tuyen_dung": "Tin tuyển dụng",
               "Tuyen_dung": "Tuyển dụng (đơn ứng tuyển)", "AI_va_danh_muc": "AI và danh mục"}
GROUP_COLOR = {"Ung_vien": "#E3F2FD", "Nha_tuyen_dung": "#FFF3E0", "Tin_tuyen_dung": "#E8F5E9", "Tuyen_dung": "#F3E5F5", "AI_va_danh_muc": "#ECEFF1"}


def build_puml() -> str:
    """ERD dạng PlantUML (đọc được khi in), nhóm theo 3 đối tượng của đề bài: ứng viên, nhà tuyển dụng, tin tuyển dụng."""
    lines = ["@startuml", "' Sinh tự động bởi backend/scripts/gen_erd.py. Xuất PNG: plantuml -tpng docs/erd/erd.puml",
             "hide circle", "skinparam linetype ortho", "skinparam shadowing false", "skinparam defaultFontName Arial", "left to right direction", ""]
    dialect = postgresql.dialect()
    refs: list[str] = []
    for group, tables in GROUPS.items():
        lines.append(f'package "{GROUP_TITLE[group]}" {GROUP_COLOR[group]} {{')
        for name in tables:
            t = Base.metadata.tables[name]
            lines.append(f"  entity {name} {{")
            pk = [c for c in t.columns if c.primary_key]
            for c in pk:
                lines.append(f"    * {c.name} : {c.type.compile(dialect=dialect).lower()} <<PK>>")
            lines.append("    --")
            for c in t.columns:
                if c.primary_key:
                    continue
                mark = "*" if not c.nullable else " "
                fk = " <<FK>>" if c.foreign_keys else ""
                lines.append(f"    {mark} {c.name} : {c.type.compile(dialect=dialect).lower()}{fk}")
            lines.append("  }")
            for c in t.columns:
                for fk in c.foreign_keys:
                    refs.append(f"{name} }}o--|| {fk.column.table.name} : {c.name}")
        lines += ["}", ""]
    lines += sorted(set(refs)) + ["@enduml", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    PUML_OUT.write_text(build_puml(), encoding="utf-8")
    print(f"Đã ghi {PUML_OUT}")
