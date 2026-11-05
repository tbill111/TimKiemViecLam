"""Seed đầy đủ trên PostgreSQL với 50 file CV thật (PDF/DOCX): không lỗi, mỗi CV thành một resume, không trùng kỹ năng.

Lỗi từng gặp (chỉ lộ khi có CV): kỹ năng do CV đề xuất bị xoá rồi chèn lại cùng lượt flush → vi phạm UNIQUE(candidate_id, skill_id).
Chạy `seed.load_seed` trong một tiến trình riêng với TEST_DATABASE_URL (PostgreSQL dùng riêng cho kiểm thử, sẽ bị xoá sạch)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

URL = os.getenv("TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not URL.startswith("postgresql"), reason="cần TEST_DATABASE_URL (PostgreSQL)")
BACKEND = Path(__file__).resolve().parents[2]


def _run(*args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "DATABASE_URL": URL, "EMBEDDER": "hash", "PYTHONIOENCODING": "utf-8"}
    return subprocess.run([sys.executable, *args], cwd=BACKEND, env=env, capture_output=True, text=True, encoding="utf-8", timeout=600)


def test_seed_reset_loads_cv_files_without_duplicates():
    engine = create_engine(URL)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    up = _run("-m", "alembic", "upgrade", "head")
    assert up.returncode == 0, up.stderr[-800:]
    seeded = _run("-m", "seed.load_seed", "--reset")
    assert seeded.returncode == 0, seeded.stderr[-1200:]
    with engine.connect() as conn:
        cv_resumes = conn.execute(text("SELECT count(*) FROM resumes WHERE filename LIKE 'cv\\_%'")).scalar()
        dup = conn.execute(text("SELECT count(*) FROM (SELECT 1 FROM candidate_skills GROUP BY candidate_id, skill_id HAVING count(*) > 1) d")).scalar()
        without_embedding = conn.execute(text("SELECT count(*) FROM candidates WHERE embedding IS NULL")).scalar()
        candidates = conn.execute(text("SELECT count(*) FROM candidates")).scalar()
    assert cv_resumes == 50, cv_resumes
    assert dup == 0 and without_embedding == 0 and candidates == 300
