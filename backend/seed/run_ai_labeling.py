"""Use a configured LLM to label unscored resume/job pairs in PostgreSQL.

Run ``alembic upgrade head`` first, then run this module from ``backend/``.
The resume text sent to the configured provider is expected to be the
anonymized ``Resume.model_text`` produced by the CV parser.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
import re
import sys
import time
from dataclasses import dataclass
from typing import Any

import requests
from sqlalchemy import exists, func, select, text, true
from sqlalchemy.orm import Session
from tqdm import tqdm

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if __package__ in (None, ""):
    sys.path.insert(0, BACKEND_ROOT)

from app.db import SessionLocal
from app.models import Job, JobSkill, LabelingTask, Resume, Skill

log = logging.getLogger("ai_labeling")
LOCK_ID = 4815162343
SYSTEM_PROMPT = (
    "Bạn là chuyên gia tuyển dụng, đánh giá mức độ phù hợp nghề nghiệp giữa CV và tin tuyển dụng. "
    "Chỉ dựa trên bằng chứng trong dữ liệu, không suy đoán thông tin còn thiếu và không đánh giá "
    "theo tuổi, giới tính, dân tộc, tình trạng hôn nhân, tôn giáo hay đặc điểm được bảo vệ. "
    "Trả về duy nhất JSON hợp lệ theo schema "
    '{"score": <số nguyên từ 0 đến 100>, "reason": "<lý do ngắn gọn bằng tiếng Việt>"}; '
    "không thêm markdown hoặc trường khác."
)
TRANSIENT_HTTP_STATUSES = {408, 429, 500, 502, 503, 504}


class LabelingAPIError(RuntimeError):
    def __init__(self, message: str, attempts: int):
        super().__init__(message)
        self.attempts = attempts


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    model: str
    api_key: str


@dataclass(frozen=True)
class MockConfig:
    name: str = "mock"
    model: str = "mock-random-v1"


def create_provider(provider: str | None = None) -> ProviderConfig | MockConfig:
    requested = (provider or os.getenv("AI_PROVIDER", "auto")).strip().lower()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()

    if requested == "auto":
        if openai_key:
            requested = "openai"
        elif gemini_key:
            requested = "gemini"
        else:
            log.warning("No AI API key configured; using mock scores for demo/testing.")
            return MockConfig()
    if requested == "openai":
        if not openai_key:
            log.warning("OPENAI_API_KEY is empty; using mock scores for demo/testing.")
            return MockConfig()
        return ProviderConfig("openai", os.getenv("OPENAI_MODEL", "gpt-4o-mini"), openai_key)
    if requested == "gemini":
        if not gemini_key:
            log.warning("GEMINI_API_KEY is empty; using mock scores for demo/testing.")
            return MockConfig()
        return ProviderConfig("gemini", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), gemini_key)
    if requested == "mock":
        return MockConfig()
    raise ValueError(f"Unsupported AI_PROVIDER: {requested!r}; expected auto, openai, gemini, or mock.")


def score_with_mock(rng: random.Random | None = None) -> dict[str, Any]:
    chooser = rng or random.SystemRandom()
    reasons = (
        "Ứng viên có kỹ năng phù hợp với yêu cầu công việc.",
        "Kinh nghiệm của ứng viên đáp ứng một phần yêu cầu vị trí.",
        "Hồ sơ có một số kỹ năng liên quan nhưng còn thiếu kinh nghiệm phù hợp.",
        "Năng lực thể hiện trong hồ sơ phù hợp tốt với mô tả công việc.",
        "Mức độ phù hợp còn hạn chế so với các yêu cầu chính của vị trí.",
    )
    return {"score": chooser.randint(40, 95), "reason": chooser.choice(reasons)}


def _extract_json(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        cleaned = fenced.group(1)
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("AI response was not valid JSON.") from exc
    if not isinstance(result, dict):
        raise ValueError("AI response JSON must be an object.")
    score = result.get("score")
    reason = result.get("reason")
    if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
        raise ValueError("AI score must be an integer from 0 to 100.")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("AI reason must be a non-empty string.")
    return {"score": score, "reason": reason.strip()}


def _provider_content(response: requests.Response, provider: str) -> str:
    payload = response.json()
    if provider == "openai":
        return payload["choices"][0]["message"]["content"]
    parts = payload["candidates"][0]["content"]["parts"]
    return "".join(part["text"] for part in parts if "text" in part)


def score_with_ai(
    config: ProviderConfig,
    resume_text: str,
    job_text: str,
    *,
    session: requests.Session | None = None,
    max_attempts: int = 3,
    retry_base_seconds: float = 2.0,
) -> tuple[dict[str, Any], int]:
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")
    http = session or requests.Session()
    user_prompt = (
        "Đánh giá CV sau với tin tuyển dụng. CV đã được ẩn danh.\n\n"
        f"CV:\n{resume_text[:16000]}\n\nTin tuyển dụng:\n{job_text[:12000]}"
    )
    if config.name == "openai":
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {config.api_key}"}
        body = {
            "model": config.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        }
    elif config.name == "gemini":
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{config.model}:generateContent"
        )
        headers = {"x-goog-api-key": config.api_key}
        body = {
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        }
    else:
        raise ValueError(f"Unsupported provider: {config.name}")

    for attempt in range(1, max_attempts + 1):
        try:
            response = http.post(url, headers=headers, json=body, timeout=(10, 60))
            if response.status_code in TRANSIENT_HTTP_STATUSES:
                message = f"{config.name} returned HTTP {response.status_code}."
                if attempt < max_attempts:
                    time.sleep(retry_base_seconds * (2 ** (attempt - 1)) + random.random())
                    continue
                raise LabelingAPIError(message, attempt)
            if response.status_code >= 400:
                raise LabelingAPIError(
                    f"{config.name} returned HTTP {response.status_code}: {response.text[:500]}",
                    attempt,
                )
            try:
                result = _extract_json(_provider_content(response, config.name))
            except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
                raise ValueError(f"Could not read {config.name} response content.") from exc
            return result, attempt
        except requests.Timeout as exc:
            if attempt == max_attempts:
                raise LabelingAPIError(f"{config.name} request timed out.", attempt) from exc
            time.sleep(retry_base_seconds * (2 ** (attempt - 1)) + random.random())
        except requests.ConnectionError as exc:
            if attempt == max_attempts:
                raise LabelingAPIError(f"Could not connect to {config.name}.", attempt) from exc
            time.sleep(retry_base_seconds * (2 ** (attempt - 1)) + random.random())
    raise LabelingAPIError(f"{config.name} request failed.", max_attempts)


def reserve_unscored_tasks(db: Session, limit: int = 300) -> list[int]:
    if limit < 1:
        raise ValueError("limit must be at least 1.")
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": LOCK_ID})

    available = db.scalars(
        select(LabelingTask.id)
        .where(LabelingTask.status.in_(("pending", "failed")))
        .order_by(LabelingTask.created_at, LabelingTask.id)
        .limit(limit)
    ).all()
    task_ids = list(available)
    slots = limit - len(task_ids)
    if slots:
        existing_pair = exists(
            select(LabelingTask.id).where(
                LabelingTask.resume_id == Resume.id,
                LabelingTask.job_id == Job.id,
            )
        )
        pairs = db.execute(
            select(Resume.id, Job.id)
            .select_from(Resume)
            .join(Job, true())
            .where(
                Resume.is_active.is_(True),
                Resume.model_text != "",
                Job.status == "open",
                ~existing_pair,
            )
            .order_by(func.random())
            .limit(slots)
        ).all()
        for resume_id, job_id in pairs:
            task = LabelingTask(resume_id=resume_id, job_id=job_id, status="pending")
            db.add(task)
            db.flush()
            task_ids.append(task.id)
    if len(task_ids) < limit:
        db.rollback()
        raise RuntimeError(
            f"Need {limit} unscored active-resume/open-job pairs; only {len(task_ids)} are available."
        )
    db.commit()
    return task_ids


def load_task_context(db: Session, task_ids: list[int]) -> list[dict[str, Any]]:
    if not task_ids:
        return []
    rows = db.execute(
        select(
            LabelingTask.id,
            LabelingTask.resume_id,
            LabelingTask.job_id,
            Resume.model_text,
            Job.title,
            Job.category,
            Job.level,
            Job.job_type,
            Job.work_mode,
            Job.description,
            Job.responsibilities,
        )
        .join(Resume, Resume.id == LabelingTask.resume_id)
        .join(Job, Job.id == LabelingTask.job_id)
        .where(LabelingTask.id.in_(task_ids), LabelingTask.matching_score.is_(None))
    ).all()
    job_ids = {row.job_id for row in rows}
    skills_by_job: dict[int, list[str]] = {job_id: [] for job_id in job_ids}
    if job_ids:
        skill_rows = db.execute(
            select(JobSkill.job_id, Skill.name)
            .join(Skill, Skill.id == JobSkill.skill_id)
            .where(JobSkill.job_id.in_(job_ids))
            .order_by(JobSkill.job_id, Skill.name)
        ).all()
        for job_id, skill_name in skill_rows:
            skills_by_job[job_id].append(skill_name)

    contexts = []
    for row in rows:
        responsibilities = row.responsibilities or []
        job_text = "\n".join(
            part for part in (
                f"Chức danh: {row.title}",
                f"Ngành nghề: {row.category}",
                f"Cấp bậc: {row.level}",
                f"Loại công việc: {row.job_type}; hình thức: {row.work_mode}",
                f"Kỹ năng: {', '.join(skills_by_job[row.job_id])}",
                f"Mô tả: {row.description}",
                f"Trách nhiệm: {'; '.join(responsibilities)}",
            ) if part
        )
        contexts.append({
            "task_id": row.id,
            "resume_id": row.resume_id,
            "job_id": row.job_id,
            "resume_text": row.model_text,
            "job_text": job_text,
        })
    return contexts


def run_labeling(
    db: Session,
    config: ProviderConfig | MockConfig,
    *,
    limit: int = 300,
    max_attempts: int = 3,
    retry_base_seconds: float = 2.0,
    delay_seconds: float = 1.0,
) -> tuple[int, int]:
    task_ids = reserve_unscored_tasks(db, limit)
    contexts = load_task_context(db, task_ids)
    completed = 0
    failed = 0
    for context in tqdm(contexts, desc="AI resume/job labeling", unit="pair"):
        try:
            if isinstance(config, MockConfig):
                result, attempts = score_with_mock(), 1
            else:
                result, attempts = score_with_ai(
                    config,
                    context["resume_text"],
                    context["job_text"],
                    max_attempts=max_attempts,
                    retry_base_seconds=retry_base_seconds,
                )
            task = db.get(LabelingTask, context["task_id"])
            if task is None:
                raise RuntimeError(f"Labeling task {context['task_id']} disappeared during processing.")
            task.matching_score = result["score"]
            task.reason = result["reason"]
            task.status = "completed"
            task.attempts += attempts
            task.error = None
            task.provider = config.name
            task.model = config.model
            db.commit()
            completed += 1
        except Exception as exc:
            db.rollback()
            task = db.get(LabelingTask, context["task_id"])
            if task is None:
                raise RuntimeError(f"Labeling task {context['task_id']} disappeared during failure handling.") from exc
            task.status = "failed"
            task.attempts += getattr(exc, "attempts", 1)
            task.error = f"{type(exc).__name__}: {exc}"[:1000]
            task.provider = config.name
            task.model = config.model
            db.commit()
            failed += 1
            log.error("Pair task %s failed: %s", context["task_id"], task.error)
        if delay_seconds > 0:
            time.sleep(delay_seconds)
    return completed, failed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=300, help="number of unscored pairs required")
    parser.add_argument("--provider", choices=("auto", "openai", "gemini", "mock"), default=None)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--retry-base-seconds", type=float, default=2.0)
    parser.add_argument("--delay-seconds", type=float, default=1.0)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if args.limit < 1 or args.max_attempts < 1 or args.retry_base_seconds < 0 or args.delay_seconds < 0:
        parser.error("limit/max-attempts must be positive and delay values must not be negative.")
    try:
        config = create_provider(args.provider)
    except ValueError as exc:
        parser.error(str(exc))
    with SessionLocal() as db:
        completed, failed = run_labeling(
            db,
            config,
            limit=args.limit,
            max_attempts=args.max_attempts,
            retry_base_seconds=args.retry_base_seconds,
            delay_seconds=args.delay_seconds,
        )
    print(f"Labeling finished: {completed} completed, {failed} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
