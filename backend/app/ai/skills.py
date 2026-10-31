"""Chuẩn hoá và so khớp kỹ năng.

`has_skill` là bản port từ `hasSkill` trong `src/utils/index.ts`; hai bên phải cho cùng kết quả
(xem tests/golden/test_m0_parity.py).
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

_WS = re.compile(r"\s+")
_LEVEL_SUFFIX = re.compile(r"\s+cơ bản$")
_ALT_SPLIT = re.compile(r"\s+hoặc\s+|/")
_COMPOSITE = re.compile(r"\s+hoặc\s+")
_TOKEN = re.compile(r"[\w+#]+(?:\.[\w+#]+)*", re.UNICODE)

DEFAULT_SKILLS_JSON = Path(__file__).with_name("default_skills.json")


def normalize_skill(s: str) -> str:
    """normalizeSkill: chữ thường, gộp khoảng trắng, cắt hai đầu."""
    return _WS.sub(" ", s.lower()).strip()


def strip_level(s: str) -> str:
    """stripLevel: bỏ hậu tố ' cơ bản' để 'Python cơ bản' == 'Python'."""
    return _LEVEL_SUFFIX.sub("", s).strip()


def alternatives(skill: str) -> list[str]:
    """Tách 'A hoặc B' / 'A/B' thành các lựa chọn đã chuẩn hoá."""
    return [x for x in (strip_level(p.strip()) for p in _ALT_SPLIT.split(normalize_skill(skill))) if x]


def has_skill(profile_skills: Iterable[str], skill: str) -> bool:
    """Ứng viên có kỹ năng yêu cầu không (so khớp nguyên tên, không khớp một phần)."""
    owned = {strip_level(normalize_skill(s)) for s in profile_skills}
    return any(alt in owned for alt in alternatives(skill))


def split_skills(profile_skills: list[str], required: list[str]) -> tuple[list[str], list[str]]:
    matched: list[str] = []
    missing: list[str] = []
    for sk in required:
        (matched if has_skill(profile_skills, sk) else missing).append(sk)
    return matched, missing


def tokenize(text: str) -> list[str]:
    """Tách token cho việc dò kỹ năng; giữ nguyên 'node.js', 'c++', 'c#'."""
    return _TOKEN.findall(unicodedata.normalize("NFC", text).lower())


@dataclass
class SkillIndex:
    """Từ điển kỹ năng + alias để dò trong văn bản.

    `phrases` ánh xạ chuỗi token (nối bằng khoảng trắng) → tên kỹ năng chuẩn.
    """

    names: list[str] = field(default_factory=list)
    categories: dict[str, str] = field(default_factory=dict)
    phrases: dict[str, str] = field(default_factory=dict)
    max_ngram: int = 1

    def _add_phrase(self, phrase: str, canonical: str) -> None:
        toks = tokenize(phrase)
        if not toks:
            return
        key = " ".join(toks)
        if len(toks) == 1 and len(key) < 2:  # tránh khớp ký tự đơn
            return
        self.phrases.setdefault(key, canonical)
        self.max_ngram = max(self.max_ngram, len(toks))

    def add_skill(self, name: str, category: str = "") -> None:
        if _COMPOSITE.search(name.lower()):  # tên có nhiều lựa chọn không dùng làm từ khoá
            return
        if name not in self.categories:
            self.names.append(name)
        self.categories[name] = category
        self._add_phrase(name, name)
        stripped = strip_level(normalize_skill(name))
        if stripped != normalize_skill(name):
            self._add_phrase(stripped, name)

    def add_alias(self, alias: str, skill_name: str) -> None:
        if skill_name in self.categories:
            self._add_phrase(alias, skill_name)

    @classmethod
    def from_rows(cls, skills: Iterable[tuple[str, str]], aliases: Iterable[tuple[str, str]]) -> "SkillIndex":
        """`skills` = (name, category); `aliases` = (alias, skill_name). Dùng khi nạp từ DB."""
        idx = cls()
        for name, cat in skills:
            idx.add_skill(name, cat)
        for alias, skill_name in aliases:
            idx.add_alias(alias, skill_name)
        return idx

    @classmethod
    def from_csv(cls, skills_csv: Path, aliases_csv: Path) -> "SkillIndex":
        with open(skills_csv, encoding="utf-8", newline="") as f:
            skills = [(r["name"].strip(), r.get("category", "").strip()) for r in csv.DictReader(f)]
        with open(aliases_csv, encoding="utf-8", newline="") as f:
            aliases = [(r["alias"].strip(), r["skill_name"].strip()) for r in csv.DictReader(f)]
        return cls.from_rows(skills, aliases)

    @classmethod
    def default(cls) -> "SkillIndex":
        """Từ điển khởi tạo (xuất từ src/data) khi chưa có CSV/DB."""
        data = json.loads(DEFAULT_SKILLS_JSON.read_text(encoding="utf-8"))
        idx = cls()
        for s in data["skills"]:
            idx.add_skill(s["name"], s.get("category", ""))
        for skill_name, aliases in data["aliases"].items():
            for a in aliases:
                idx.add_alias(a, skill_name)
        return idx
