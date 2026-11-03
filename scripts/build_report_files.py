"""Dựng docs/report/BaoCao_TH3.docx từ BaoCao_TH3.md và docs/report/Slide_TH3.pptx.

    pip install python-docx python-pptx
    python scripts/build_report_files.py
"""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.shared import Inches
from pptx import Presentation
from pptx.util import Inches as PI, Pt

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "report"


def add_runs(par, text: str) -> None:
    for part in re.split(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)", text):
        if part.startswith("**") and part.endswith("**"):
            par.add_run(part[2:-2]).bold = True
        elif part.startswith("`") and part.endswith("`"):
            par.add_run(part[1:-1]).font.name = "Consolas"
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            par.add_run(part[1:-1]).italic = True
        else:
            par.add_run(part)


def build_docx() -> None:
    doc = Document()
    lines = (REPORT / "BaoCao_TH3.md").read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("#"):
            level = len(ln) - len(ln.lstrip("#"))
            doc.add_heading(ln.lstrip("# ").strip(), level=min(level - 1, 3) if level > 1 else 0)
        elif ln.startswith("!["):
            m = re.match(r"!\[(.*?)\]\((.*?)\)", ln)
            doc.add_picture(str(REPORT / m.group(2)), width=Inches(6.2))
            doc.add_paragraph(m.group(1)).italic = True
        elif ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|[\s\-|]+\|$", lines[i]):
                    rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            t = doc.add_table(rows=len(rows), cols=len(rows[0]), style="Table Grid")
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    cell = t.cell(r, c)
                    cell.text = ""
                    add_runs(cell.paragraphs[0], val)
            continue
        elif ln.startswith("> "):
            add_runs(doc.add_paragraph(style="Intense Quote"), ln[2:])
        elif ln.startswith("- "):
            add_runs(doc.add_paragraph(style="List Bullet"), ln[2:])
        elif ln.strip():
            add_runs(doc.add_paragraph(), ln)
        i += 1
    doc.save(REPORT / "BaoCao_TH3.docx")


SLIDES = [
    ("TH3 – SmartCareer v2", ["Hệ thống Tìm việc Thông minh tích hợp AI và BI", "Nhóm 3 · báo cáo: Hoàng Anh (phân tích, kiểm thử, báo cáo)"], None),
    ("Bài toán và mục tiêu", ["Ứng viên mới khó biết hợp vị trí nào, thiếu kỹ năng gì; nhà tuyển dụng sàng lọc thủ công", "Matching Score 0–100 có giải thích (M0–M4)", "Dashboard BI: ứng viên theo kỹ năng, xu hướng lương, tỷ lệ chuyển đổi", "Kế thừa SmartCareer (prototype React); thêm backend, CSDL, AI, BI"], None),
    ("01 · Yêu cầu: 4 tác nhân, F01–F10", ["Tác nhân: ứng viên, nhà tuyển dụng, quản trị, dịch vụ AI", "F01 tài khoản · F02 hồ sơ · F03 tải CV · F04 quản lý tin · F05 Matching Score", "F06 gợi ý/xếp hạng · F07 ứng tuyển + trạng thái · F08 Skill Gap · F09 BI · F10 danh mục kỹ năng", "Phi chức năng: < 200 ms/cặp, 500 tin < 2 s; giải thích được; bcrypt/JWT; đồng ý dữ liệu; công bằng"], None),
    ("01 · Use Case", ["Quan hệ include: Tải CV → Trích kỹ năng; Xem việc gợi ý → Tính Matching Score; Đổi trạng thái → Ghi lịch sử"], "docs/usecase/usecase.png"),
    ("01 · ERD 15 bảng", ["Ba nhóm: ứng viên / nhà tuyển dụng / tin tuyển dụng, cộng tuyển dụng và danh mục"], "docs/erd/erd.png"),
    ("Trạng thái ứng tuyển và phân quyền", ["applied → screening → interview → offer → hired; từ bước chưa cuối → rejected", "Nhảy cóc hoặc đổi trạng thái cuối → 409 invalid_transition", "Mỗi lần đổi ghi application_status_history; phễu BI đếm hồ sơ từng đạt mỗi bước", "Recruiter công ty khác → 403"], None),
    ("02 · Mô hình AI", ["TODO (Tùng): CV parser 3 tầng, 6 đặc trưng, M0–M4", "TODO: bảng P/R/F1 và bảng so sánh M0–M4 — chỉ điền khi có docs/report/tables/", "M0 Python khớp bản TypeScript 100% trên 84 ca (test tự động)"], None),
    ("03 · Dashboard BI", ["TODO (Hưng): ảnh dashboard, 3–4 nhận định", "Ba view SQL: v_skill_supply_demand, v_salary, v_funnel; RLS theo công ty", "Lưu ý: đơn ứng tuyển là mô phỏng — chỉ minh hoạ cách tính"], None),
    ("04 · Kiến trúc và giao diện", ["docker compose: db (PostgreSQL 16), api (FastAPI), superset, web (React + nginx)", "Giao diện theo vai trò: ứng viên, nhà tuyển dụng (Kanban 6 cột), quản trị", "Chế độ demo VITE_OFFLINE_DEMO=true chạy không cần backend", "TODO (Ngọc Anh): ảnh màn hình"], None),
    ("05 · Kiểm thử", ["pytest: 178 passed (PostgreSQL 16 tạm); không có DB: 167 passed, 1 skipped", "33 test case theo F01–F10: 20 đạt bằng kiểm thử tự động, 13 chưa chạy (giao diện/Docker)", "Phủ 401/403/409/413/415/422/503; công bằng khi đổi tên/giới tính ở đầu CV", "TODO: ghi kết quả thủ công cho 13 ca còn lại"], None),
    ("Hạn chế và hướng phát triển", ["Dữ liệu mô phỏng; hiệu quả mô hình chỉ kết luận từ nhãn gán tay (30 ứng viên × 10 tin)", "Chưa có NER huấn luyện riêng (PhoBERT); CV ảnh scan không đọc được", "Hướng: học từ phản hồi thật, đặc trưng nhóm nghề, mở rộng danh mục kỹ năng"], None),
]


def build_pptx() -> None:
    prs = Presentation()
    prs.slide_width, prs.slide_height = PI(13.333), PI(7.5)
    for title, bullets, image in SLIDES:
        s = prs.slides.add_slide(prs.slide_layouts[5])
        s.shapes.title.text = title
        s.shapes.title.text_frame.paragraphs[0].font.size = Pt(32)
        width = PI(5.2) if image else PI(12)
        box = s.shapes.add_textbox(PI(0.6), PI(1.5), width, PI(5.5))
        tf = box.text_frame
        tf.word_wrap = True
        for n, b in enumerate(bullets):
            p = tf.paragraphs[0] if n == 0 else tf.add_paragraph()
            p.text = "• " + b
            p.font.size = Pt(20)
            p.space_after = Pt(10)
        if image:
            s.shapes.add_picture(str(ROOT / image), PI(6.2), PI(1.4), height=PI(5.8))
    prs.save(REPORT / "Slide_TH3.pptx")


if __name__ == "__main__":
    build_docx()
    build_pptx()
    print("OK", len(SLIDES), "slide")
