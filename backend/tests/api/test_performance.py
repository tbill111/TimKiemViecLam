"""Yêu cầu phi chức năng: chấm 1 cặp < 200 ms; gợi ý trên 150 và 500 tin < 2 giây (embedding đã tính sẵn khi lưu tin).

Đo qua API thật trên dữ liệu seed (SQLite, embedder thay thế). Với model embedding thật, phần nặng là encode một lần khi lưu CV/tin
nên đường chấm điểm lúc chạy không đổi; vẫn nên đo lại trong Docker (xem docs/E2E.md).
"""
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app import db as dbmod
from app.main import create_app
from app.models import Base, Job, JobSkill
from seed import load_seed
from tests.api.conftest import PASSWORD, auth


@pytest.fixture(scope="module")
def env():
    engine = dbmod.make_engine("sqlite://")
    Base.metadata.create_all(engine)
    dbmod.configure(engine)
    db = dbmod.new_session()
    load_seed.seed(db, applications=False)
    client = TestClient(create_app())
    token = client.post("/api/auth/login", json={"email": "tung.demo@smartcareer.vn", "password": PASSWORD}).json()["access_token"]
    yield client, token, db
    db.close()


def timed(fn, repeat=3):
    best = float("inf")
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - t0)
    return best


def test_single_pair_under_200ms(env):
    client, token, _ = env
    elapsed = timed(lambda: client.post("/api/ai/match", json={"job_id": 1, "model": "m3"}, headers=auth(token)))
    assert elapsed < 0.2, f"{elapsed * 1000:.0f} ms"


def test_recommendations_150_then_500_jobs_under_2s(env):
    client, token, db = env
    r = client.get("/api/candidates/me/matches", headers=auth(token))
    assert r.status_code == 200 and len(r.json()["items"]) == 150
    t150 = timed(lambda: client.get("/api/candidates/me/matches", headers=auth(token)))
    assert t150 < 2.0, f"150 tin: {t150:.2f}s"

    # nhân bản tin tới 500 (giữ kỹ năng và embedding) rồi đo lại
    base = list(db.scalars(select(Job).order_by(Job.id)))
    skills = {j.id: list(db.scalars(select(JobSkill).where(JobSkill.job_id == j.id))) for j in base}
    n = 0
    while len(base) + n < 500:
        src = base[n % len(base)]
        clone = Job(**{c.name: getattr(src, c.name) for c in Job.__table__.columns if c.name not in ("id", "external_id")})
        clone.title = f"{src.title} (bản {n})"
        db.add(clone)
        db.flush()
        db.add_all(JobSkill(job_id=clone.id, skill_id=s.skill_id, is_required=s.is_required) for s in skills[src.id])
        n += 1
    db.commit()
    r500 = client.get("/api/candidates/me/matches", headers=auth(token))
    assert len(r500.json()["items"]) == 500
    t500 = timed(lambda: client.get("/api/candidates/me/matches", headers=auth(token)))
    assert t500 < 2.0, f"500 tin: {t500:.2f}s"
    print(f"\nPerformance: 150 jobs {t150 * 1000:.0f} ms, 500 jobs {t500 * 1000:.0f} ms")
