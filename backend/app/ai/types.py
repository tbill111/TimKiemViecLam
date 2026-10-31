"""Kiểu dữ liệu dùng chung giữa tầng AI và tầng API.

Tầng AI là hàm thuần: không import SQLAlchemy. Phần API (Thái Anh) dựng
`CandidateInput` / `JobInput` từ DB rồi gọi `score_pair`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

MODELS = ("m0", "m1", "m2", "m3", "m4")


@dataclass
class JobInput:
    id: int
    required: list[str]
    preferred: list[str]
    min_years: float = 0.0
    # Thang 1-4: 1 Trung cấp, 2 Cao đẳng, 3 Đại học, 4 Thạc sĩ trở lên; 0 = không yêu cầu
    min_edu: int = 0
    location: str = ""
    # Nhãn hình thức làm việc đúng như frontend: "Toàn thời gian" | "Bán thời gian" | "Thực tập" | "Remote"
    work_type_label: str = ""
    salary_min: Optional[float] = None  # triệu VNĐ/tháng
    salary_max: Optional[float] = None
    text: str = ""
    embedding: Optional[np.ndarray] = None


@dataclass
class CandidateInput:
    id: int
    skills: list[str]
    years_exp: float = 0.0
    edu: int = 0
    locations: list[str] = field(default_factory=list)
    work_types: list[str] = field(default_factory=list)
    sal_min: Optional[float] = None
    sal_max: Optional[float] = None
    text: str = ""
    embedding: Optional[np.ndarray] = None


@dataclass
class SkillHit:
    name: str
    source: str  # "dict" | "fuzzy" | "embedding"
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "source": self.source, "confidence": round(self.confidence, 3)}


class CvError(Exception):
    """Lỗi đọc CV. `code` ánh xạ sang HTTP: unsupported_type→415, too_large→413, no_text/corrupt→422."""

    def __init__(self, code: str, message: str = ""):
        super().__init__(message or code)
        self.code = code


class ModelNotAvailable(Exception):
    """Model chưa được huấn luyện (ví dụ thiếu models_store/m4.joblib)."""
