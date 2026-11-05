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
ANALYSIS_PARAGRAPHS = (
    "Số liệu cho thấy ReactJS và Python chiếm 45% kỹ năng ứng viên, trong khi nhu cầu tuyển dụng tương ứng có dấu hiệu chững lại. Điều này có thể phản ánh sức hút của các công nghệ phổ biến, nguồn học liệu phong phú và ngưỡng gia nhập tương đối thấp, khiến nhiều người cùng đầu tư vào một nhóm kỹ năng. Khi nguồn cung tăng nhanh hơn nhu cầu, hồ sơ chỉ liệt kê kỹ năng mà thiếu dự án, kinh nghiệm hoặc minh chứng năng lực sẽ khó tạo khác biệt. Tuy nhiên, tỷ trọng ứng viên tự nó không chứng minh thị trường đã bão hòa; cần so sánh với số tin tuyển dụng theo thời gian và cùng cách phân loại kỹ năng. View đếm ứng viên theo kỹ năng chỉ thể hiện phía cung, nên kết luận về nhu cầu cần được đối chiếu với dữ liệu kỹ năng yêu cầu trong tin tuyển dụng đang mở.",
    "Mức lương trung bình của Data Engineer và AI Engineer cao hơn khoảng 30% so với Web Developer có thể gắn với nhu cầu về năng lực chuyên sâu, chẳng hạn xây dựng hạ tầng dữ liệu, vận hành pipeline hoặc triển khai mô hình học máy. Nguồn nhân lực có kinh nghiệm thực tiễn trong các lĩnh vực này có thể khan hiếm hơn, trong khi sai sót kỹ thuật gây ảnh hưởng lớn đến hệ thống và hoạt động kinh doanh. Dù vậy, mức chênh lệch không nên được quy hoàn toàn cho chức danh: cấp bậc, địa điểm, quy mô doanh nghiệp, loại hình công việc và độ đầy đủ của dữ liệu lương đều có thể tác động đáng kể. Vì vậy, kết quả nên được xem là xu hướng mô tả, không phải kết luận rằng mọi vị trí Data hoặc AI đều trả lương cao hơn 30%.",
    "Tỷ lệ khoảng 15% hồ sơ đạt trên 75 điểm cho thấy chỉ một phần nhỏ các cặp CV–Job có mức phù hợp cao theo tiêu chí chấm điểm đã chọn. Đây là tín hiệu hữu ích để nhà tuyển dụng ưu tiên xem xét hồ sơ có điểm cao trước, đồng thời nhận diện những yêu cầu thường thiếu ở các hồ sơ còn lại. Tuy nhiên, điểm thấp không đồng nghĩa CV “rác” hay ứng viên rải hồ sơ hàng loạt: nguyên nhân có thể là ứng viên chuyển hướng nghề nghiệp, CV trình bày thiếu từ khóa, hoặc tiêu chí và dữ liệu đầu vào chưa phản ánh đầy đủ năng lực. Muốn xác định hành vi nộp đơn hàng loạt cần kết hợp thêm lịch sử ứng tuyển và đánh giá độc lập của chuyên gia.",
    "Khi kết hợp AI Scoring với BI Dashboard, nhà tuyển dụng có thể chuyển từ đọc hồ sơ hoàn toàn thủ công sang quy trình ưu tiên theo mức độ phù hợp, theo dõi phân bố điểm và phát hiện nhóm kỹ năng hoặc vị trí có chênh lệch cung–cầu. Nhờ đó, hệ thống hỗ trợ giảm công sức sàng lọc ban đầu và hạn chế bỏ sót hồ sơ tiềm năng, chứ chưa đủ căn cứ để khẳng định đã giải quyết triệt để CV rác. Để đưa ra kết luận mạnh hơn, cần kiểm chứng điểm AI trên tập hồ sơ được gán nhãn độc lập, đo độ chính xác ở ngưỡng sử dụng thực tế và so sánh thời gian tuyển dụng, tỷ lệ hồ sơ được mời phỏng vấn trước và sau khi áp dụng.",
)


def insert_before(document: Document, paragraph: Paragraph, text: str, style: str | None = None) -> Paragraph:
    new_paragraph = document.add_paragraph(style=style)
    new_paragraph.add_run(text)
    paragraph._p.addprevious(new_paragraph._p)
    return new_paragraph


def update_report(input_path: Path, output_path: Path, placeholder: str = PLACEHOLDER) -> None:
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
        for paragraph_text in ANALYSIS_PARAGRAPHS:
            document.add_paragraph(paragraph_text)
    else:
        heading = insert_before(document, target, CHAPTER_TITLE, style="Heading 1")
        for paragraph_text in ANALYSIS_PARAGRAPHS:
            insert_before(document, target, paragraph_text)
        target._p.getparent().remove(target._p)

    heading.paragraph_format.keep_with_next = True
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_REPORT, help="input .docx report")
    parser.add_argument("--output", type=Path, help="output .docx path; defaults to overwriting --input")
    parser.add_argument(
        "--placeholder",
        default=PLACEHOLDER,
        help=f"exact paragraph to replace (default: {PLACEHOLDER}); if absent, append at end",
    )
    args = parser.parse_args()
    output_path = args.output or args.input

    try:
        update_report(args.input, output_path, args.placeholder)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Lỗi cập nhật báo cáo: {exc}", file=sys.stderr)
        return 1

    print(f"Đã ghi tiêu đề và 4 đoạn phân tích BI vào: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
