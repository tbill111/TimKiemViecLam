"""Append the prepared BI analysis chapter to the project report."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from docx import Document
from docx.text.paragraph import Paragraph

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT = REPOSITORY_ROOT / "docs" / "report" / "BaoCao_TH3.docx"
CHAPTER_TITLE = "CHƯƠNG: KẾT QUẢ TRỰC QUAN HÓA (BI) VÀ ĐÁNH GIÁ HIỆU QUẢ"
PLACEHOLDER = "{{BI_ANALYSIS}}"


def build_analysis(database_url: str) -> list[str]:
    """Sinh nhận định từ số liệu THẬT trong các BI view (không dùng số cố định)."""
    from sqlalchemy import create_engine, text

    engine = create_engine(database_url)
    try:
        with engine.connect() as conn:
            skills = conn.execute(text(
                "SELECT skill_name, candidate_count, open_job_count FROM vw_candidate_skills "
                "ORDER BY candidate_count DESC LIMIT 5")).all()
            total_cand = conn.execute(text("SELECT COALESCE(SUM(candidate_count),0) FROM vw_candidate_skills")).scalar() or 0
            salary = conn.execute(text(
                "SELECT title, SUM(average_salary * salary_posting_count) / NULLIF(SUM(salary_posting_count),0) AS avg_salary, "
                "SUM(salary_posting_count) AS n FROM vw_salary_trends GROUP BY title ORDER BY avg_salary DESC NULLS LAST")).all()
            stats = conn.execute(text(
                "SELECT score_bucket, pair_count, percentage FROM vw_ai_matching_stats ORDER BY 1")).all()
    finally:
        engine.dispose()

    paragraphs: list[str] = []
    if skills and total_cand:
        top = "; ".join(f"{r.skill_name} ({r.candidate_count} ứng viên, {r.open_job_count} tin đang mở)" for r in skills)
        paragraphs.append(
            f"Năm kỹ năng có nhiều ứng viên nhất là: {top}. Đối chiếu cột số tin đang mở cho thấy kỹ năng nào cung vượt cầu "
            "và ngược lại. Dữ liệu ứng viên là dữ liệu hư cấu do hệ thống sinh, nên đây là minh hoạ cách đọc biểu đồ, "
            "không phải kết luận về thị trường thật.")
    valid = [r for r in salary if r.avg_salary is not None]
    if len(valid) >= 2:
        hi, lo = valid[0], valid[-1]
        diff = (float(hi.avg_salary) / float(lo.avg_salary) - 1) * 100 if lo.avg_salary else 0
        paragraphs.append(
            f"Trong dữ liệu tin tuyển dụng, vị trí có lương trung bình cao nhất là {hi.title} ({float(hi.avg_salary):.1f} triệu VNĐ/tháng, "
            f"{hi.n} tin) và thấp nhất là {lo.title} ({float(lo.avg_salary):.1f} triệu VNĐ/tháng, {lo.n} tin), chênh khoảng {diff:.0f}%. "
            "Mức chênh còn chịu ảnh hưởng của cấp bậc, địa điểm và dữ liệu lương mô phỏng, nên chỉ nên xem là xu hướng mô tả.")
    total_pairs = sum(int(r.pair_count) for r in stats)
    if total_pairs:
        parts = ", ".join(f"{r.score_bucket}: {r.pair_count} cặp ({float(r.percentage):.1f}%)" for r in stats)
        paragraphs.append(
            f"Trên {total_pairs} cặp CV–Job đã được gán điểm bởi mô hình AI (không tính điểm mock), phân bố là {parts}. "
            "Đây là nhãn do AI gán, chưa được người kiểm chứng độc lập, nên không đủ căn cứ kết luận về độ chính xác hay về CV rác.")
    else:
        paragraphs.append("Chưa có cặp CV–Job nào được AI gán điểm thật (không tính mock), nên chưa có phân tích phân bố điểm.")
    return paragraphs


def insert_before(document: Document, paragraph: Paragraph, text: str, style: str | None = None) -> Paragraph:
    new_paragraph = document.add_paragraph(style=style)
    new_paragraph.add_run(text)
    paragraph._p.addprevious(new_paragraph._p)
    return new_paragraph


def update_report(input_path: Path, output_path: Path, paragraphs: list[str], placeholder: str = PLACEHOLDER) -> None:
    if not input_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy file báo cáo: {input_path}")

    document = Document(input_path)
    if any(paragraph.text.strip() == CHAPTER_TITLE for paragraph in document.paragraphs):
        raise ValueError(f"Báo cáo đã có tiêu đề chương này; không chèn trùng: {CHAPTER_TITLE}")

    target = next(
        (paragraph for paragraph in document.paragraphs if paragraph.text.strip() == placeholder),
        None,
    )
    if target is None:
        heading = document.add_paragraph(CHAPTER_TITLE, style="Heading 1")
        for paragraph_text in paragraphs:
            document.add_paragraph(paragraph_text)
    else:
        heading = insert_before(document, target, CHAPTER_TITLE, style="Heading 1")
        for paragraph_text in paragraphs:
            insert_before(document, target, paragraph_text)
        target._p.getparent().remove(target._p)

    heading.paragraph_format.keep_with_next = True
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_REPORT, help="input .docx report")
    parser.add_argument("--output", type=Path, help="output .docx path; mặc định <input>.bi.docx (không ghi đè input)")
    parser.add_argument("--in-place", action="store_true", help="ghi đè --input")
    parser.add_argument("--database-url", default=None, help="mặc định lấy từ DATABASE_URL")
    parser.add_argument(
        "--placeholder",
        default=PLACEHOLDER,
        help=f"exact paragraph to replace (default: {PLACEHOLDER}); if absent, append at end",
    )
    args = parser.parse_args()
    output_path = args.output or (args.input if args.in_place else args.input.with_suffix(".bi.docx"))

    try:
        import os
        from dotenv import load_dotenv
        load_dotenv(REPOSITORY_ROOT / ".env")
        url = args.database_url or os.getenv("DATABASE_URL", "")
        if not url:
            raise ValueError("Thiếu DATABASE_URL")
        paragraphs = build_analysis(url)
        update_report(args.input, output_path, paragraphs, args.placeholder)
    except Exception as exc:
        print(f"Lỗi cập nhật báo cáo: {exc}", file=sys.stderr)
        return 1

    print(f"Đã ghi tiêu đề và các đoạn phân tích BI (số liệu từ DB) vào: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
