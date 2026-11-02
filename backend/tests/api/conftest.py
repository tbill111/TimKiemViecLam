from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    pytest.skip("Set TEST_DATABASE_URL to a separate PostgreSQL test database", allow_module_level=True)

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("EMBEDDER", "hash")

import bcrypt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.deps import get_db
from app.main import app
from app.models import Candidate, Company, Job, JobSkill, Location, Recruiter, Skill, User

engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def api():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    password_hash = bcrypt.hashpw(b"Demo@12345", bcrypt.gensalt()).decode()
    with TestSession() as db:
        hanoi = Location(name="Hà Nội", region="Miền Bắc")
        hcm = Location(name="Hồ Chí Minh", region="Miền Nam")
        db.add_all([hanoi, hcm])
        db.flush()
        company_a = Company(name="Alpha Tech", industry="Công nghệ", size_range="50–200", location_id=hanoi.id)
        company_b = Company(name="Beta Tech", industry="Công nghệ", size_range="10–50", location_id=hcm.id)
        skill = Skill(name="React", category="Frontend", learning_steps=[])
        db.add_all([company_a, company_b, skill])
        db.flush()
        candidate_user = User(email="candidate@smartcareer.vn", password_hash=password_hash, role="candidate", full_name="Ứng viên Demo")
        recruiter_a = User(email="hr.a@smartcareer.vn", password_hash=password_hash, role="recruiter", full_name="HR Alpha", company_id=company_a.id)
        recruiter_b = User(email="hr.b@smartcareer.vn", password_hash=password_hash, role="recruiter", full_name="HR Beta", company_id=company_b.id)
        admin = User(email="admin@smartcareer.vn", password_hash=password_hash, role="admin", full_name="Admin")
        db.add_all([candidate_user, recruiter_a, recruiter_b, admin])
        db.flush()
        db.add_all([Recruiter(user_id=recruiter_a.id, company_id=company_a.id), Recruiter(user_id=recruiter_b.id, company_id=company_b.id)])
        candidate = Candidate(user_id=candidate_user.id, external_id="test-candidate", full_name=candidate_user.full_name, profile_json={"preferredLocations": ["Hà Nội"], "preferredWorkTypes": ["Thực tập"]})
        job_a = Job(external_id="test-job-a", company_id=company_a.id, recruiter_id=recruiter_a.id, title="React Intern", category="Frontend Development", level="intern", job_type="internship", work_mode="onsite", location_id=hanoi.id, min_years_exp=0, min_education=0, description="React developer role", responsibilities=[], status="open")
        job_b = Job(external_id="test-job-b", company_id=company_b.id, recruiter_id=recruiter_b.id, title="Backend Engineer", category="Backend Development", level="junior", job_type="full_time", work_mode="hybrid", location_id=hcm.id, min_years_exp=1, min_education=0, description="Backend APIs", responsibilities=[], status="open")
        job_c = Job(external_id="test-job-c", company_id=company_a.id, recruiter_id=recruiter_a.id, title="React Senior", category="Frontend Development", level="senior", job_type="full_time", work_mode="remote", location_id=hanoi.id, min_years_exp=3, min_education=3, description="React platform role", responsibilities=[], status="open")
        db.add_all([candidate, job_a, job_b, job_c])
        db.flush()
        db.add_all([JobSkill(job_id=job_a.id, skill_id=skill.id, priority="required"), JobSkill(job_id=job_c.id, skill_id=skill.id, priority="required")])
        db.commit()
        candidate_id, job_a_id, job_b_id = candidate.id, job_a.id, job_b.id

    def override_get_db():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        client.state = SimpleNamespace()
        client.state.candidate_id = candidate_id
        client.state.job_a_id = job_a_id
        client.state.job_b_id = job_b_id
        yield client
    app.dependency_overrides.pop(get_db, None)  # giữ override get_ai_repo đăng ký ở app.main
    Base.metadata.drop_all(engine)


def auth(client: TestClient, email: str):
    response = client.post("/api/auth/login", json={"email": email, "password": "Demo@12345"})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
