"""Vẽ ERD PNG từ metadata SQLAlchemy (không cần Graphviz/PlantUML).

    cd backend && python ../scripts/render_erd.py        # ghi docs/erd/erd.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app import models  # noqa: E402,F401
from app.db import Base  # noqa: E402

OUT = ROOT / "docs" / "erd" / "erd.png"
# (nhóm, màu nền, tên, danh sách bảng) – ba nhóm chính của đề: ứng viên / nhà tuyển dụng / tin tuyển dụng
GROUPS = [
    ("Ứng viên", "#E3F2FD", ["users", "candidates", "resumes", "candidate_skills", "saved_jobs"]),
    ("Tuyển dụng (đơn ứng tuyển, kết quả khớp)", "#F3E5F5", ["applications", "application_status_history", "match_results"]),
    ("Tin tuyển dụng", "#E8F5E9", ["jobs", "job_skills"]),
    ("Nhà tuyển dụng", "#FFF3E0", ["companies", "recruiters"]),
    ("Danh mục", "#ECEFF1", ["skills", "skill_aliases", "locations"]),
]
LINE, ROWH, W, GAP = 0.19, 0.19, 3.1, 0.5


def height(t) -> float:
    return 0.35 + ROWH * len(t.columns)


def main() -> None:
    tables = Base.metadata.tables
    pos: dict[str, tuple[float, float, float]] = {}  # name -> (x, ytop, h)
    fig_w = len(GROUPS) * (W + 1.0)
    maxh = max(sum(height(tables[n]) + GAP for n in g[2]) for g in GROUPS) + 1.2
    fig, ax = plt.subplots(figsize=(fig_w, maxh))
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, maxh)
    ax.axis("off")
    for gi, (title, color, names) in enumerate(GROUPS):
        x = 0.3 + gi * (W + 1.0)
        y = maxh - 0.8
        gh = sum(height(tables[n]) + GAP for n in names)
        ax.add_patch(Rectangle((x - 0.15, y - gh + 0.1), W + 0.3, gh + 0.55, fc=color, ec="#90A4AE", lw=1, zorder=0))
        ax.text(x + W / 2, y + 0.4, title, ha="center", va="center", fontsize=10, fontweight="bold")
        for n in names:
            h = height(tables[n])
            pos[n] = (x, y, h)
            y -= h + GAP
    assert set(pos) == set(tables), set(pos) ^ set(tables)
    # đường khoá ngoại (vẽ trước, dưới các bảng)
    for n, t in tables.items():
        for c in t.columns:
            for fk in c.foreign_keys:
                a, b = pos[n], pos[fk.column.table.name]
                ca = (a[0] + (W if a[0] < b[0] else 0), a[1] - a[2] / 2)
                cb = (b[0] + (0 if a[0] < b[0] else W), b[1] - b[2] / 2)
                if a[0] == b[0]:
                    ca, cb = (a[0] + W, a[1] - a[2] / 2), (b[0] + W, b[1] - b[2] / 2)
                ax.annotate("", xy=cb, xytext=ca, arrowprops=dict(arrowstyle="->", color="#546E7A", lw=0.7, alpha=0.7,
                                                                  connectionstyle="arc3,rad=0.12"), zorder=1)
    for n, t in tables.items():
        x, y, h = pos[n]
        ax.add_patch(FancyBboxPatch((x, y - h), W, h, boxstyle="round,pad=0,rounding_size=0.05", fc="white", ec="#37474F", lw=1, zorder=2))
        ax.add_patch(Rectangle((x, y - 0.3), W, 0.3, fc="#37474F", ec="#37474F", zorder=3))
        ax.text(x + 0.08, y - 0.15, n, color="white", fontsize=8.5, fontweight="bold", va="center", zorder=4)
        for i, c in enumerate(t.columns):
            tag = "PK" if c.primary_key else ("FK" if c.foreign_keys else "")
            mark = "" if c.nullable or c.primary_key else " *"
            label = f"{c.name}{mark}"
            ax.text(x + 0.08, y - 0.3 - ROWH * (i + 0.5), label, fontsize=6.8, va="center", zorder=4)
            ax.text(x + W - 0.08, y - 0.3 - ROWH * (i + 0.5), f"{tag}  {c.type.compile(dialect=__import__('sqlalchemy.dialects.postgresql', fromlist=['x']).dialect()).lower()}".strip(),
                    fontsize=6, va="center", ha="right", color="#607D8B", zorder=4)
    ax.text(0.3, 0.25, "SmartCareer v2 – ERD 15 bảng (sinh từ app/models). * = NOT NULL; mũi tên = khoá ngoại (từ bảng con tới bảng cha).",
            fontsize=8, color="#455A64")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=130, bbox_inches="tight")
    print("Đã ghi", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
