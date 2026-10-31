from datetime import date
from pathlib import Path

import pytest

from app.ai.embedder import HashingEmbedder, from_bytes
from app.ai.extract import extract_skills
from app.ai.parser import parse_cv, suggest_skills
from app.ai.skills import SkillIndex
from app.ai.types import CvError

SAMPLE_PDF = Path(__file__).resolve().parents[3] / "public" / "cv-mau.pdf"
EMB = HashingEmbedder()


@pytest.fixture(scope="module")
def idx() -> SkillIndex:
    return SkillIndex.default()


def names(hits):
    return [h.name for h in hits]


def test_tier1_alias_normalisation(idx):
    hits = extract_skills("Thành thạo reactjs, nodejs và PostgreSQL", idx, tiers=(1,))
    assert names(hits) == ["React", "Node.js", "PostgreSQL"]
    assert all(h.source == "dict" for h in hits)


def test_tier1_prefers_longest_phrase(idx):
    assert names(extract_skills("Xây dựng REST API bằng Node.js", idx, tiers=(1,))) == ["REST API", "Node.js"]


def test_tier2_fixes_typos(idx):
    hits = extract_skills("Biết Javascrip và Typescrpt", idx, tiers=(1, 2))
    assert set(names(hits)) >= {"JavaScript", "TypeScript"}
    assert all(h.source == "fuzzy" and h.confidence >= 0.9 for h in hits)


def test_tier2_does_not_flag_unrelated_words(idx):
    assert extract_skills("Tôi thích bóng đá và nấu ăn trong thời gian rảnh", idx, tiers=(1, 2)) == []


def test_tier1_only_misses_typo(idx):
    assert extract_skills("Javascrip", idx, tiers=(1,)) == []


class FakeEmbedder:
    """Mỗi kỹ năng một vector đơn vị riêng; cụm bắt đầu bằng 'maria' được coi là gần 'PostgreSQL'."""

    name = "fake"

    def __init__(self, idx):
        self.idx = idx

    def encode(self, texts):
        import numpy as np

        out = np.zeros((len(texts), len(self.idx.names) + 1), dtype=np.float32)
        for r, t in enumerate(texts):
            if t in self.idx.names:
                out[r, self.idx.names.index(t)] = 1.0
            elif t.lower().startswith("maria"):
                out[r, self.idx.names.index("PostgreSQL")] = 0.9
                out[r, -1] = 0.436  # cosine = 0.9
            else:
                out[r, -1] = 1.0
        return out / np.linalg.norm(out, axis=1, keepdims=True)


def test_tier3_suggests_unknown_phrase_close_to_a_skill(idx):
    hits = extract_skills("", idx, tiers=(3,), embedder=FakeEmbedder(idx), skills_section="MariaDB, Nấu ăn")
    assert [(h.name, h.source) for h in hits] == [("PostgreSQL", "embedding")]
    assert hits[0].confidence >= 0.8


def test_tier3_skips_items_already_found_by_dictionary(idx):
    hits = extract_skills("", idx, tiers=(3,), embedder=FakeEmbedder(idx), skills_section="React, Git")
    assert hits == []


def test_dedupe_one_hit_per_skill(idx):
    hits = extract_skills("React React reactjs", idx, tiers=(1,))
    assert names(hits) == ["React"]


def test_suggest_skills_for_jd():
    out = suggest_skills("Yêu cầu: thành thạo React, Git, hiểu biết về Docker")
    assert {"React", "Git", "Docker"} <= {s["name"] for s in out}


def _txt_cv() -> bytes:
    return (
        "Nguyễn Văn An\n"
        "Mục tiêu\nFrontend Developer\n"
        "Kỹ năng\nReactjs, Javascrip, Git, HTML5, CSS3\n"
        "Kinh nghiệm\nFrontend Intern - Công ty ABC 06/2023 - 09/2023\n"
        "Học vấn\nĐại học Thủy lợi 2022 - 2026\n"
    ).encode("utf-8")


def test_parse_cv_end_to_end_txt(idx):
    r = parse_cv(_txt_cv(), "cv.txt", index=idx, embedder=EMB, today=date(2026, 10, 31))
    got = {s["name"] for s in r["skills"]}
    assert {"React", "JavaScript", "Git", "HTML", "CSS"} <= got
    assert r["years_exp"] == pytest.approx(0.3, abs=0.05)  # 4 tháng
    assert r["education_level"] == 3
    assert {"skills", "experience", "education"} <= set(r["sections"])
    assert from_bytes(r["embedding"]).shape == (384,)


def test_parse_cv_empty_and_corrupt(idx):
    with pytest.raises(CvError) as e:
        parse_cv(b"", "cv.txt", index=idx, embedder=EMB)
    assert e.value.code == "no_text"
    with pytest.raises(CvError) as e:
        parse_cv(b"garbage", "cv.docx", index=idx, embedder=EMB)
    assert e.value.code == "corrupt"


@pytest.mark.skipif(not SAMPLE_PDF.exists(), reason="thiếu public/cv-mau.pdf")
def test_parse_cv_real_pdf(idx):
    r = parse_cv(SAMPLE_PDF.read_bytes(), "cv-mau.pdf", index=idx, embedder=EMB)
    assert len(r["skills"]) >= 3
    print({s["name"] for s in r["skills"]}, r["years_exp"], r["education_level"])
