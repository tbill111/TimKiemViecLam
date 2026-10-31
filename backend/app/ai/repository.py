"""Hợp đồng truy cập dữ liệu của tầng AI.

Router AI/CV (Tùng) chỉ làm việc qua `AIRepository`; Thái Anh hiện thực bản SQLAlchemy
(ví dụ `app/services/ai_repo.py`) và gắn vào ứng dụng trong `main.py`:

    from app.ai.repository import get_ai_repo
    app.dependency_overrides[get_ai_repo] = lambda db=Depends(get_db): SqlAIRepository(db)

Tầng này không import SQLAlchemy.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Protocol

from .types import CandidateInput, JobInput


@dataclass
class ApplicantRow:
    """Một ứng viên đã nộp đơn vào một tin."""

    candidate: CandidateInput
    full_name: str
    application_id: int
    status: str  # applied|screening|interview|offer|hired|rejected
    applied_at: str  # ISO 8601


class AIRepository(Protocol):
    # --- ứng viên ---------------------------------------------------------
    def candidate_input_for_user(self, user_id: int) -> Optional[CandidateInput]:
        """Ứng viên (đã gắn kỹ năng đã xác nhận, CV đang dùng, embedding) của tài khoản; None nếu chưa có hồ sơ."""

    def candidate_input(self, candidate_id: int) -> Optional[CandidateInput]: ...

    # --- tin --------------------------------------------------------------
    def job_input(self, job_id: int) -> Optional[JobInput]: ...

    def open_jobs(self) -> list[JobInput]:
        """Mọi tin đang mở, đã gắn sẵn `embedding` để chấm 500 tin dưới 2 giây."""

    def job_company_id(self, job_id: int) -> Optional[int]: ...

    def applicants_for_job(self, job_id: int) -> list[ApplicantRow]: ...

    # --- danh mục ----------------------------------------------------------
    def skill_index_rows(self) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
        """(skills=[(name, category)], aliases=[(alias, skill_name)])."""

    def open_jobs_requiring(self, skill: str) -> int:
        """Số tin đang mở yêu cầu kỹ năng này (bắt buộc hoặc ưu tiên)."""

    def learning_steps(self, skill: str) -> list[str]: ...

    # --- ghi ---------------------------------------------------------------
    def save_resume(self, user_id: int, filename: str, parsed: dict[str, Any], consent: bool) -> int:
        """Lưu CV (`parsed` gồm text, skills, years_exp, education_level, sections, embedding: bytes). Trả resume_id.
        Các kỹ năng trích được lưu vào candidate_skills với source='cv', confirmed=False."""

    def save_match(self, candidate_id: int, job_id: int, match: dict[str, Any]) -> None:
        """Upsert vào match_results (PK candidate_id, job_id, model_version)."""


def get_ai_repo() -> AIRepository:
    """Dependency của FastAPI. Mặc định chưa cấu hình – `main.py` phải ghi đè (xem docstring đầu file)."""
    raise NotImplementedError("Chưa cấu hình AIRepository: ghi đè get_ai_repo trong app.dependency_overrides.")
