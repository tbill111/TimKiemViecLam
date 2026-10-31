from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import db as dbmod
from app.ai import scorers
from app.ai.embedder import set_embedder
from app.main import create_app
from app.models import Base, Location, Skill, SkillAlias, User
from app.security import hash_password

SKILLS = [
    ("HTML", "Frontend"), ("CSS", "Frontend"), ("JavaScript", "Frontend"), ("React", "Frontend"), ("TypeScript", "Frontend"),
    ("Git", "DevOps"), ("SQL", "Dữ liệu"), ("Python", "Dữ liệu"), ("Docker", "DevOps"), ("REST API", "Backend"),
]
ALIASES = {"reactjs": "React", "html5": "HTML", "js": "JavaScript"}
PASSWORD = "Demo@12345"


@pytest.fixture()
def session():
    set_embedder(None)
    engine = dbmod.make_engine("sqlite://")
    Base.metadata.create_all(engine)
    dbmod.configure(engine)
    scorers._m3_cache = None
    scorers._m4_cache = None
    db = dbmod.new_session()
    skills = {n: Skill(name=n, category=c) for n, c in SKILLS}
    db.add_all(skills.values())
    db.flush()
    db.add_all([SkillAlias(alias=a, skill_id=skills[n].id) for a, n in ALIASES.items()])
    db.add_all([Location(name="Hà Nội", region="Bắc"), Location(name="Hồ Chí Minh", region="Nam"), Location(name="Remote", region="Remote")])
    db.add(User(email="admin@test.vn", password_hash=hash_password(PASSWORD), role="admin", full_name="Admin"))
    db.commit()
    yield db
    db.close()
    engine.dispose()


@pytest.fixture()
def client(session):
    return TestClient(create_app())


def register(client: TestClient, email: str, role: str = "candidate", company: str | None = None, name: str = "Người Dùng") -> dict:
    body = {"email": email, "password": PASSWORD, "role": role, "full_name": name}
    if company:
        body["company_name"] = company
    r = client.post("/api/auth/register", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def login(client: TestClient, email: str) -> str:
    r = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


JOB_BODY = {
    "title": "Frontend Intern", "description": "Làm giao diện web", "responsibilities": ["Viết component"],
    "category": "Frontend Development", "level": "intern", "job_type": "internship", "work_mode": "onsite",
    "location": "Hà Nội", "salary_min": 3, "salary_max": 5, "min_years_exp": 0, "min_education": 3,
    "required_skills": ["HTML", "CSS", "React"], "preferred_skills": ["TypeScript", "Git"],
}


@pytest.fixture()
def world(client):
    """Hai công ty (mỗi công ty một recruiter), hai ứng viên, một tin của công ty A."""
    ra = register(client, "hr-a@test.vn", "recruiter", "Công ty A")
    rb = register(client, "hr-b@test.vn", "recruiter", "Công ty B")
    ca = register(client, "an@test.vn", name="Nguyễn Văn An")
    cb = register(client, "binh@test.vn", name="Trần Thị Bình")
    job = client.post("/api/jobs", json=JOB_BODY, headers=auth(ra["access_token"]))
    assert job.status_code == 201, job.text
    return {"ra": ra, "rb": rb, "ca": ca, "cb": cb, "job": job.json(), "client": client}


def now() -> dt.datetime:
    return dt.datetime(2026, 10, 31, 12, 0, 0)


def user_id(session: Session, email: str) -> int:
    return session.scalar(select(User.id).where(User.email == email))
