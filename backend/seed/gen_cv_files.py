"""Dựng 50 file CV (PDF và DOCX, 5 bố cục khác nhau) từ 50 ứng viên đầu tiên.

    cd backend && python -m seed.gen_cv_files

Ghi: seed/cv_files/cv_001.* … cv_050.* và seed/data/cv_manifest.csv.

`cv_manifest.csv` có cột `true_skills`, `true_years_exp`, `true_education_level`: đây là đáp án TỔNG HỢP (do chính trình sinh
tạo ra), dùng để kiểm tra parser tự động. Nó KHÔNG thay cho nhãn tay `labels_cv_skills.csv` của Hoàng Anh; báo cáo phải nói rõ
nguồn của từng bảng số liệu. Cách ghi kỹ năng được biến đổi (alias, lỗi gõ) để đo cả tầng 2 của parser.
"""
from __future__ import annotations

import csv
import random
from pathlib import Path
from typing import Any

import docx
from docx.shared import Pt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from xml.sax.saxutils import escape

from .catalog import ALIASES
from .gen_candidates import DATA

SEED = 42
N_CV = 50
OUT = Path(__file__).resolve().parent / "cv_files"
FONT_CANDIDATES = [
    ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]
LABELS = {
    "vi": {"goal": "Mục tiêu", "skills": "Kỹ năng", "exp": "Kinh nghiệm", "edu": "Học vấn", "proj": "Dự án"},
    "en": {"goal": "Objective", "skills": "Skills", "exp": "Experience", "edu": "Education", "proj": "Projects"},
}
COMPANIES = ["Công ty ABC", "Công ty Sao Việt", "Startup Mặt Trời", "Công ty TNHH Đại Dương", "Trung tâm Công nghệ Hoa Mai"]
PROJECTS = ["Website quản lý thư viện", "Ứng dụng đặt lịch khám", "Hệ thống quản lý bán hàng", "Dashboard theo dõi doanh số", "Ứng dụng học từ vựng"]


def register_fonts() -> tuple[str, str]:
    for regular, bold in FONT_CANDIDATES:
        if Path(regular).exists() and Path(bold).exists():
            pdfmetrics.registerFont(TTFont("CVFont", regular))
            pdfmetrics.registerFont(TTFont("CVFont-Bold", bold))
            return "CVFont", "CVFont-Bold"
    raise RuntimeError("Không tìm thấy font TrueType hỗ trợ tiếng Việt (Arial hoặc DejaVu Sans).")


def surface(skill: str, rng: random.Random) -> str:
    """Cách viết kỹ năng trong CV: tên chuẩn, alias hoặc lỗi gõ (bỏ một chữ ở giữa)."""
    r = rng.random()
    if r < 0.30 and ALIASES.get(skill):
        return rng.choice(ALIASES[skill])
    if r < 0.38 and len(skill) >= 8 and skill.isascii() and " " not in skill:
        k = rng.randrange(2, len(skill) - 2)
        return skill[:k] + skill[k + 1:]
    return skill


def fmt(month_index: int) -> str:
    return f"{month_index % 12 + 1:02d}/{month_index // 12}"


def experience(years: float, rng: random.Random) -> tuple[list[tuple[str, str, str]], float]:
    """Các vị trí có khoảng thời gian không chồng nhau; tổng số tháng khớp `years` (kết thúc bao gồm, như parser)."""
    total = round(years * 12)
    if total == 0:
        return [], 0.0
    end_last = 2026 * 12 + 8  # 09/2026
    parts = [total] if total < 12 or rng.random() < 0.5 else [total * 2 // 3, total - total * 2 // 3]
    items: list[tuple[str, str, str]] = []
    end = end_last
    for k, months in enumerate(reversed(parts)):
        start = end - months + 1
        items.append((rng.choice(["Intern", "Junior Developer", "Thực tập sinh", "Cộng tác viên", "Nhân viên"]), rng.choice(COMPANIES), f"{fmt(start)} - {fmt(end)}"))
        end = start - 4  # nghỉ 3 tháng giữa hai vị trí
    return items, round(total / 12, 1)


def edu_line(level: int, university: str) -> str:
    return {1: "Trung cấp nghề Công nghệ thông tin", 2: "Cao đẳng FPT Polytechnic", 3: f"Đại học {university.replace('Đại học ', '').replace('Học viện ', '')}", 4: "Thạc sĩ Công nghệ thông tin – Đại học Quốc gia"}[level] + " 2022 - 2026"


def build_content(c: dict[str, Any], idx: int, rng: random.Random) -> dict[str, Any]:
    skills_true = c["skills"].split("|")
    years = float(c["years_exp"])
    exp_items, true_years = experience(years, rng)
    return {
        "name": c["full_name"], "contact": [f"Email: cand{idx:04d}@example.edu.vn", f"Điện thoại: {c['phone']}"],
        "goal": c["career_goal"], "skills": [surface(s, rng) for s in skills_true], "skills_true": skills_true,
        "exp": exp_items, "true_years": true_years, "edu": edu_line(int(c["education_level"]), c["university"]),
        "edu_level": int(c["education_level"]), "projects": rng.sample(PROJECTS, k=2),
    }


# ----------------------------------------------------------------------------- PDF


def pdf(path: Path, content: dict[str, Any], layout: int, fonts: tuple[str, str]) -> None:
    reg, bold = fonts
    lang = "en" if layout == 3 else "vi"
    L = LABELS[lang]
    body = ParagraphStyle("b", fontName=reg, fontSize=10, leading=14)
    head = ParagraphStyle("h", fontName=bold, fontSize=12, leading=16, spaceBefore=8, spaceAfter=3)
    title = ParagraphStyle("t", fontName=bold, fontSize=18, leading=22)
    P = lambda t, s=body: Paragraph(escape(t), s)  # noqa: E731
    story: list[Any] = [P(content["name"], title), *[P(x) for x in content["contact"]], Spacer(1, 6)]
    story += [P(L["goal"], head), P(content["goal"])]
    if layout == 4:  # kỹ năng ghi cùng dòng với tiêu đề
        story += [P(f"{L['skills']}: {', '.join(content['skills'])}", head)]
    else:
        story += [P(L["skills"], head)]
        story += [P("• " + s) for s in content["skills"]] if layout == 1 else [P(", ".join(content["skills"]))]
    story += [P(L["exp"], head)]
    story += [P(f"{t} – {co}, {span}") for t, co, span in content["exp"]] or [P("Sinh viên chưa đi làm chính thức." if lang == "vi" else "No formal work experience.")]
    story += [P(L["edu"], head), P(content["edu"]), P(L["proj"], head)] + [P(f"• {p}") for p in content["projects"]]
    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm).build(story)


# ----------------------------------------------------------------------------- DOCX


def _para(container: Any, text: str, bold: bool = False, size: int = 11) -> None:
    p = container.add_paragraph()
    run = p.add_run(text)
    run.bold, run.font.size = bold, Pt(size)


def docx_cv(path: Path, content: dict[str, Any], layout: int) -> None:
    L = LABELS["vi"]
    d = docx.Document()
    _para(d, content["name"], True, 18)
    for x in content["contact"]:
        _para(d, x)
    if layout == 0:
        sections = [(L["goal"], [content["goal"]]), (L["skills"], [", ".join(content["skills"])]),
                    (L["exp"], [f"{t} – {co}, {span}" for t, co, span in content["exp"]] or ["Sinh viên chưa đi làm chính thức."]),
                    (L["edu"], [content["edu"]]), (L["proj"], [f"• {p}" for p in content["projects"]])]
        for h, lines in sections:
            _para(d, h, True, 13)
            for ln in lines:
                _para(d, ln)
    else:  # bố cục hai cột bằng bảng
        table = d.add_table(rows=1, cols=2)
        left, right = table.rows[0].cells
        for h, lines in [(L["skills"], [", ".join(content["skills"])]), (L["edu"], [content["edu"]])]:
            _para(left, h, True, 13)
            for ln in lines:
                _para(left, ln)
        for h, lines in [(L["goal"], [content["goal"]]),
                         (L["exp"], [f"{t} – {co}, {span}" for t, co, span in content["exp"]] or ["Sinh viên chưa đi làm chính thức."]),
                         (L["proj"], [f"• {p}" for p in content["projects"]])]:
            _para(right, h, True, 13)
            for ln in lines:
                _para(right, ln)
    d.save(str(path))


def main(n: int = N_CV) -> None:
    rng = random.Random(SEED)
    fonts = register_fonts()
    OUT.mkdir(exist_ok=True)
    with open(DATA / "candidates_generated.csv", encoding="utf-8", newline="") as f:
        cands = list(csv.DictReader(f))[:n]
    manifest = []
    for i, c in enumerate(cands, start=1):
        content = build_content(c, i, rng)
        layout = i % 5  # 0,2 → DOCX; 1,3,4 → PDF
        ext = "docx" if layout in (0, 2) else "pdf"
        name = f"cv_{i:03d}.{ext}"
        (docx_cv(OUT / name, content, layout) if ext == "docx" else pdf(OUT / name, content, layout, fonts))
        manifest.append([name, c["candidate_id"], c["occupation"], "|".join(content["skills_true"]), content["true_years"], content["edu_level"], layout])
    with open(DATA / "cv_manifest.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cv_file", "candidate_id", "occupation", "true_skills", "true_years_exp", "true_education_level", "layout"])
        w.writerows(manifest)
    print(f"Đã dựng {len(manifest)} CV vào {OUT}")


if __name__ == "__main__":
    main()
