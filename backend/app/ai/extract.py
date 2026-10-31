"""Trích kỹ năng từ văn bản (CV hoặc JD) theo 3 tầng.

Tầng 1: so khớp n-gram (tối đa `index.max_ngram` từ) với `skills` + `skill_aliases`.
Tầng 2: so khớp mờ bằng rapidfuzz, ngưỡng 90, bắt lỗi gõ như "Javascrip".
Tầng 3: cụm trong mục "Kỹ năng" chưa có trong từ điển được so embedding với tên kỹ năng,
        cosine >= 0,8 thì đề xuất (người dùng phải xác nhận).
"""
from __future__ import annotations

import re
from typing import Iterable, Optional

import numpy as np
from rapidfuzz import fuzz, process

from .embedder import Embedder, get_embedder
from .skills import SkillIndex, tokenize
from .types import SkillHit

FUZZY_CUTOFF = 90
EMBED_CUTOFF = 0.8
FUZZY_MAX_NGRAM = 3
_SOURCE_RANK = {"dict": 0, "fuzzy": 1, "embedding": 2}
_ITEM_SPLIT = re.compile(r"[,;|\n]+")

_default_index: Optional[SkillIndex] = None


def get_default_index() -> SkillIndex:
    global _default_index
    if _default_index is None:
        _default_index = SkillIndex.default()
    return _default_index


def set_default_index(index: Optional[SkillIndex]) -> None:
    global _default_index
    _default_index = index


def _tier1(tokens: list[str], index: SkillIndex, consumed: list[bool]) -> list[tuple[int, SkillHit]]:
    hits: list[tuple[int, SkillHit]] = []
    i = 0
    while i < len(tokens):
        matched = False
        for n in range(min(index.max_ngram, len(tokens) - i), 0, -1):
            name = index.phrases.get(" ".join(tokens[i : i + n]))
            if name:
                hits.append((i, SkillHit(name, "dict", 1.0)))
                for j in range(i, i + n):
                    consumed[j] = True
                i += n
                matched = True
                break
        if not matched:
            i += 1
    return hits


def _tier2(tokens: list[str], index: SkillIndex, consumed: list[bool]) -> list[tuple[int, SkillHit]]:
    keys = [k for k in index.phrases if len(k) >= 5]
    hits: list[tuple[int, SkillHit]] = []
    if not keys:
        return hits
    i = 0
    while i < len(tokens):
        matched = False
        for n in range(min(FUZZY_MAX_NGRAM, len(tokens) - i), 0, -1):
            if any(consumed[i : i + n]):
                continue
            gram = " ".join(tokens[i : i + n])
            if len(gram) < 5 or gram.isdigit():
                continue
            best = process.extractOne(gram, keys, scorer=fuzz.ratio, score_cutoff=FUZZY_CUTOFF)
            if best and best[0][0] == gram[0]:  # lỗi gõ hiếm khi sai chữ cái đầu → giảm khớp nhầm
                key, score, _ = best
                hits.append((i, SkillHit(index.phrases[key], "fuzzy", score / 100)))
                for j in range(i, i + n):
                    consumed[j] = True
                i += n
                matched = True
                break
        if not matched:
            i += 1
    return hits


def _name_vectors(index: SkillIndex, embedder: Embedder) -> np.ndarray:
    cache = getattr(index, "_name_vecs", None)
    if cache is None or cache[0] != (embedder.name, len(index.names)):
        index._name_vecs = ((embedder.name, len(index.names)), embedder.encode(index.names))  # type: ignore[attr-defined]
    return index._name_vecs[1]  # type: ignore[attr-defined]


def _tier3(skills_section: str, index: SkillIndex, embedder: Embedder, known: set[str]) -> list[SkillHit]:
    items = []
    for raw in _ITEM_SPLIT.split(skills_section):
        item = raw.strip(" .:-")
        toks = tokenize(item)
        if not (3 <= len(item) <= 40) or not (1 <= len(toks) <= 4):
            continue
        scratch = [False] * len(toks)
        if _tier1(toks, index, scratch) or _tier2(toks, index, [False] * len(toks)):
            continue  # đã được tầng 1/2 xử lý
        items.append(item)
    if not items or not index.names:
        return []
    item_vecs = embedder.encode(items)
    name_vecs = _name_vectors(index, embedder)
    sims = item_vecs @ name_vecs.T  # vector đã chuẩn hoá L2
    hits: list[SkillHit] = []
    for row in range(len(items)):
        col = int(np.argmax(sims[row]))
        score = float(sims[row, col])
        name = index.names[col]
        if score >= EMBED_CUTOFF and name not in known:
            hits.append(SkillHit(name, "embedding", score))
    return hits


def extract_skills(
    text: str,
    index: Optional[SkillIndex] = None,
    tiers: Iterable[int] = (1, 2, 3),
    embedder: Optional[Embedder] = None,
    skills_section: str = "",
) -> list[SkillHit]:
    """Danh sách kỹ năng chuẩn tìm thấy, theo thứ tự xuất hiện; mỗi kỹ năng một lần."""
    index = index or get_default_index()
    tiers = set(tiers)
    tokens = tokenize(text)
    consumed = [False] * len(tokens)
    positioned: list[tuple[int, SkillHit]] = []
    if 1 in tiers:
        positioned += _tier1(tokens, index, consumed)
    if 2 in tiers:
        positioned += _tier2(tokens, index, consumed)

    best: dict[str, tuple[int, SkillHit]] = {}
    for pos, hit in sorted(positioned, key=lambda x: x[0]):
        cur = best.get(hit.name)
        if cur is None or _SOURCE_RANK[hit.source] < _SOURCE_RANK[cur[1].source]:
            best[hit.name] = (cur[0] if cur else pos, hit)
    result = [h for _, h in sorted(best.values(), key=lambda x: x[0])]

    if 3 in tiers and skills_section:
        known = {h.name for h in result}
        result += _tier3(skills_section, index, embedder or get_embedder(), known)
    return result
