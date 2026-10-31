"""Câu giải thích điểm khớp sinh theo mẫu (không dùng LLM, kết quả xác định)."""
from __future__ import annotations

_MAX_LISTED = 5


def _join(items: list[str]) -> str:
    shown = items[:_MAX_LISTED]
    text = ", ".join(shown)
    return text + ", …" if len(items) > _MAX_LISTED else text


def explain(total: int, matched_required: list[str], matched_preferred: list[str], missing_required: list[str], missing_preferred: list[str]) -> str:
    """Ví dụ: "Khớp 72/100. Đã có React, Git. Thiếu TypeScript (bắt buộc) và REST API (ưu tiên)."."""
    parts = [f"Khớp {total}/100."]
    have = matched_required + matched_preferred
    if have:
        parts.append(f"Đã có {_join(have)}.")
    missing: list[str] = []
    if missing_required:
        missing.append(f"{_join(missing_required)} (bắt buộc)")
    if missing_preferred:
        missing.append(f"{_join(missing_preferred)} (ưu tiên)")
    if missing:
        parts.append("Thiếu " + " và ".join(missing) + ".")
    else:
        parts.append("Đáp ứng đủ các kỹ năng được nêu.")
    return " ".join(parts)
