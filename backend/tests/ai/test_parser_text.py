from datetime import date
from pathlib import Path

import pytest

from app.ai.parser import (
    extract_education_level,
    extract_text,
    extract_years_exp,
    merge_months,
    normalize_text,
    split_sections,
)
from app.ai.types import CvError

TODAY = date(2026, 10, 31)
SAMPLE_PDF = Path(__file__).resolve().parents[3] / "public" / "cv-mau.pdf"


def test_normalize_removes_bullets_and_collapses_spaces():
    out = normalize_text("•  React   và Git\n\n  ●  Docker  ")
    assert out == "React và Git\nDocker"


def test_split_sections_bilingual_headings():
    text = "Nguyễn Văn A\nKỹ năng: React, Git\nExperience\nIntern tại ABC 06/2023 - 09/2023\nHọc vấn\nĐại học Thủy lợi 2022 - 2026"
    sec = split_sections(text)
    assert "React" in sec["skills"]
    assert "ABC" in sec["experience"]
    assert "Thủy lợi" in sec["education"]
    assert sec["header"] == "Nguyễn Văn A"


def test_merge_months_no_double_count_of_overlap():
    # 01/2023-06/2023 (6 tháng) và 04/2023-12/2023 chồng nhau -> hợp là 01/2023-12/2023 = 12 tháng
    a = (2023 * 12 + 0, 2023 * 12 + 5)
    b = (2023 * 12 + 3, 2023 * 12 + 11)
    assert merge_months([a, b]) == 12


def test_years_exp_from_month_year_ranges():
    text = "Kinh nghiệm\nFrontend Intern 06/2023 - 09/2023\nDeveloper 01/2024 - 12/2024"
    assert extract_years_exp(text, today=TODAY) == pytest.approx(1.3, abs=0.05)  # 4 + 12 tháng = 16 tháng


def test_years_exp_present_and_overlap():
    text = "Kinh nghiệm\nA 2023 - nay\nB 2024 - 2025"  # B nằm trọn trong A: không cộng thêm
    # 01/2023 -> 10/2026 = 46 tháng ≈ 3.8 năm
    assert extract_years_exp(text, today=TODAY) == pytest.approx(3.8, abs=0.05)


def test_years_exp_ignores_education_dates():
    text = "Học vấn\nĐại học Thủy lợi 2022 - 2026\nKinh nghiệm\nIntern 06/2025 - 08/2025"
    assert extract_years_exp(text, today=TODAY) == pytest.approx(0.2, abs=0.05)  # 3 tháng


def test_years_exp_phrase_fallback_and_zero():
    assert extract_years_exp("Tôi có 2 năm kinh nghiệm làm web", today=TODAY) == 2.0
    assert extract_years_exp("Sinh viên mới ra trường", today=TODAY) == 0.0


def test_education_level_mapping():
    assert extract_education_level("Học vấn\nThạc sĩ CNTT") == 4
    assert extract_education_level("Học vấn\nĐại học Bách Khoa") == 3
    assert extract_education_level("Học vấn\nCao đẳng FPT") == 2
    assert extract_education_level("Học vấn\nTrung cấp nghề") == 1
    assert extract_education_level("Không có thông tin") == 0


def test_extract_text_errors():
    with pytest.raises(CvError) as e:
        extract_text(b"x" * (5 * 1024 * 1024 + 1), "cv.pdf")
    assert e.value.code == "too_large"
    with pytest.raises(CvError) as e:
        extract_text(b"abc", "cv.exe")
    assert e.value.code == "unsupported_type"
    with pytest.raises(CvError) as e:
        extract_text(b"   ", "cv.txt")
    assert e.value.code == "no_text"
    with pytest.raises(CvError) as e:
        extract_text(b"not a pdf", "cv.pdf")
    assert e.value.code == "corrupt"


@pytest.mark.skipif(not SAMPLE_PDF.exists(), reason="thiếu public/cv-mau.pdf")
def test_extract_text_real_pdf():
    text = extract_text(SAMPLE_PDF.read_bytes(), "cv-mau.pdf")
    assert len(text) > 100
