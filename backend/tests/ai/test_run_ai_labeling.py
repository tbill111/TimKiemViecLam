from __future__ import annotations

from datetime import datetime
import random

import pytest

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db import Base
from app.models import Candidate, Company, Job, JobSkill, LabelingTask, Resume, Skill
from seed import run_ai_labeling


def _database(tmp_path, resume_count=4, job_count=5):
    engine = create_engine(f"sqlite:///{tmp_path / 'labeling.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        company = Company(name="Test company")
        skill = Skill(name="Python")
        db.add_all([company, skill])
        db.flush()
        for index in range(resume_count):
            candidate = Candidate(full_name=f"Candidate {index}")
            db.add(candidate)
            db.flush()
            db.add(Resume(
                candidate_id=candidate.id,
                filename=f"resume-{index}.pdf",
                model_text=f"Anonymized resume {index}",
                consent_at=datetime.now(),
            ))
        for index in range(job_count):
            job = Job(
                company_id=company.id,
                title=f"Job {index}",
                description="Build software",
                responsibilities=["Develop features"],
            )
            db.add(job)
            db.flush()
            db.add(JobSkill(job_id=job.id, skill_id=skill.id, priority="required"))
        db.commit()
    return engine


def test_reserves_requested_unique_unscored_pairs_and_excludes_completed(tmp_path):
    engine = _database(tmp_path, resume_count=10, job_count=40)
    with Session(engine) as db:
        first_batch = run_ai_labeling.reserve_unscored_tasks(db, limit=300)
        assert len(first_batch) == 300

        completed = db.get(LabelingTask, first_batch[0])
        assert completed is not None
        completed.status = "completed"
        completed.matching_score = 80
        completed.reason = "Relevant experience."
        db.commit()

        second_batch = run_ai_labeling.reserve_unscored_tasks(db, limit=300)
        assert len(second_batch) == 300
        assert first_batch[0] not in second_batch
        pairs = db.execute(
            select(LabelingTask.resume_id, LabelingTask.job_id)
            .where(LabelingTask.id.in_(first_batch + second_batch))
        ).all()
        assert len(set(pairs)) == 301


def test_run_labeling_persists_score_and_reason(tmp_path, monkeypatch):
    engine = _database(tmp_path, resume_count=2, job_count=2)
    config = run_ai_labeling.ProviderConfig("openai", "test-model", "test-key")

    def fake_score(_config, resume_text, job_text, **_kwargs):
        assert resume_text.startswith("Anonymized resume")
        assert "Kỹ năng: Python" in job_text
        return {"score": 73, "reason": "Kỹ năng phù hợp với yêu cầu."}, 1

    monkeypatch.setattr(run_ai_labeling, "score_with_ai", fake_score)
    with Session(engine) as db:
        completed, failed = run_ai_labeling.run_labeling(
            db, config, limit=3, delay_seconds=0,
        )
        assert (completed, failed) == (3, 0)
        rows = db.scalars(select(LabelingTask)).all()
        assert len(rows) == 3
        assert all(row.status == "completed" for row in rows)
        assert all(row.matching_score == 73 for row in rows)
        assert all(row.reason == "Kỹ năng phù hợp với yêu cầu." for row in rows)
        assert all(row.provider == "openai" and row.model == "test-model" for row in rows)


def test_failed_task_is_marked_and_can_be_retried(tmp_path, monkeypatch):
    engine = _database(tmp_path, resume_count=1, job_count=1)
    config = run_ai_labeling.ProviderConfig("gemini", "test-model", "test-key")

    def fail_score(*_args, **_kwargs):
        raise run_ai_labeling.LabelingAPIError("rate limit", attempts=3)

    monkeypatch.setattr(run_ai_labeling, "score_with_ai", fail_score)
    with Session(engine) as db:
        completed, failed = run_ai_labeling.run_labeling(
            db, config, limit=1, delay_seconds=0,
        )
        task = db.scalar(select(LabelingTask))
        assert (completed, failed) == (0, 1)
        assert task is not None
        assert task.status == "failed"
        assert task.matching_score is None
        assert task.attempts == 3
        assert task.error == "LabelingAPIError: rate limit"


def test_requires_exact_requested_count(tmp_path):
    engine = _database(tmp_path, resume_count=1, job_count=1)
    with Session(engine) as db:
        try:
            run_ai_labeling.reserve_unscored_tasks(db, limit=2)
        except RuntimeError as exc:
            assert "only 1 are available" in str(exc)
        else:
            raise AssertionError("Expected an error when fewer than the requested pairs exist.")
        assert db.scalar(select(func.count()).select_from(LabelingTask)) == 0


def test_score_parser_validates_json_contract():
    assert run_ai_labeling._extract_json(
        '```json\n{"score": 88, "reason": "Có kỹ năng phù hợp."}\n```'
    ) == {"score": 88, "reason": "Có kỹ năng phù hợp."}

    for invalid in (
        '{"score": 101, "reason": "too high"}',
        '{"score": true, "reason": "not a numeric score"}',
        '{"score": 50, "reason": ""}',
    ):
        try:
            run_ai_labeling._extract_json(invalid)
        except ValueError:
            continue
        raise AssertionError(f"Expected invalid response to be rejected: {invalid}")


def test_auto_provider_refuses_mock_when_no_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("AI_PROVIDER", "auto")

    with pytest.raises(ValueError):
        run_ai_labeling.create_provider()
    assert run_ai_labeling.create_provider("mock") == run_ai_labeling.MockConfig()


def test_mock_scores_follow_demo_contract():
    result = run_ai_labeling.score_with_mock(random.Random(7))

    assert 40 <= result["score"] <= 95
    assert result["reason"]


def test_run_labeling_persists_mock_scores_as_completed(tmp_path, monkeypatch):
    engine = _database(tmp_path, resume_count=2, job_count=2)
    monkeypatch.setattr(run_ai_labeling.time, "sleep", lambda _seconds: None)
    with Session(engine) as db:
        completed, failed = run_ai_labeling.run_labeling(
            db, run_ai_labeling.MockConfig(), limit=3, delay_seconds=0,
        )
        rows = db.scalars(select(LabelingTask)).all()

    assert (completed, failed) == (3, 0)
    assert len(rows) == 3
    assert all(row.status == "completed" for row in rows)
    assert all(40 <= row.matching_score <= 95 for row in rows)
    assert all(row.reason for row in rows)
    assert all(row.provider == "mock" and row.model == "mock-random-v1" for row in rows)
