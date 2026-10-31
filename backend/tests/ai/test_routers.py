from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.ai.embedder import HashingEmbedder, set_embedder
from app.ai.repository import ApplicantRow, get_ai_repo
from app.ai.types import CandidateInput, JobInput
from app.deps import get_current_user
from app.routers import ai as ai_router
from app.routers import resumes as resumes_router


class FakeRepo:
    def __init__(self):
        emb = HashingEmbedder()
        self.candidates = {
            1: CandidateInput(1, ["HTML", "CSS", "Git"], years_exp=0.5, edu=3, locations=["Hà Nội"], work_types=["Thực tập"], text="frontend", embedding=emb.encode(["frontend"])[0]),
            2: CandidateInput(2, ["Python", "SQL"], years_exp=1, edu=3, locations=["Hồ Chí Minh"], work_types=["Thực tập"], text="data", embedding=emb.encode(["data"])[0]),
        }
        self.jobs = {
            10: JobInput(10, ["HTML", "CSS", "React"], ["TypeScript", "Git"], location="Hà Nội", work_type_label="Thực tập", text="frontend", embedding=emb.encode(["frontend"])[0]),
            11: JobInput(11, ["Python", "SQL"], ["Power BI"], location="Hồ Chí Minh", work_type_label="Thực tập", text="data", embedding=emb.encode(["data"])[0]),
        }
        self.company = {10: 100, 11: 200}
        self.saved: list[tuple[Any, ...]] = []
        self.resumes: list[dict] = []

    def candidate_input_for_user(self, user_id): return self.candidates.get(user_id)
    def candidate_input(self, cid): return self.candidates.get(cid)
    def job_input(self, jid): return self.jobs.get(jid)
    def open_jobs(self): return list(self.jobs.values())
    def job_company_id(self, jid): return self.company.get(jid)

    def applicants_for_job(self, jid):
        return [ApplicantRow(self.candidates[1], "Ứng viên A", 7, "applied", "2026-10-30T00:00:00Z")] if jid == 10 else []

    def skill_index_rows(self): return [], []  # dùng từ điển mặc định
    def open_jobs_requiring(self, skill): return {"React": 5, "TypeScript": 3, "Power BI": 2}.get(skill, 0)
    def learning_steps(self, skill): return [f"Học {skill}"] if skill == "React" else []

    def save_resume(self, user_id, filename, parsed, consent):
        self.resumes.append({"user": user_id, "filename": filename, "consent": consent, "keys": set(parsed)})
        return 99

    def save_match(self, cid, jid, match): self.saved.append((cid, jid, match["model"]))


@pytest.fixture()
def env():
    set_embedder(HashingEmbedder())
    repo = FakeRepo()
    app = FastAPI()
    app.include_router(ai_router.router)
    app.include_router(resumes_router.router)
    app.dependency_overrides[get_ai_repo] = lambda: repo
    state = {"user": SimpleNamespace(id=1, role="candidate", company_id=None)}
    app.dependency_overrides[get_current_user] = lambda: state["user"]
    yield TestClient(app), repo, state
    set_embedder(None)


def login(state, role, uid=1, company=None):
    state["user"] = SimpleNamespace(id=uid, role=role, company_id=company)


def test_match_candidate_default_model_and_saved(env):
    client, repo, _ = env
    r = client.post("/ai/match", json={"job_id": 10})
    assert r.status_code == 200
    body = r.json()
    assert body["model"] == "m3" and 0 <= body["total_score"] <= 100
    assert body["missing_required"] == ["React"] and "Thiếu" in body["explanation"]
    assert repo.saved == [(1, 10, "m3")]


@pytest.mark.parametrize("model", ["m0", "m1", "m2", "m3"])
def test_match_all_available_models(env, model):
    client, _, _ = env
    r = client.post("/ai/match", json={"job_id": 10, "model": model})
    assert r.status_code == 200 and r.json()["model"] == model


def test_match_m4_not_trained_returns_503_and_bad_model_422(env, monkeypatch, tmp_path):
    from app.ai import scorers

    monkeypatch.setattr(scorers, "MODELS_DIR", tmp_path)
    monkeypatch.setattr(scorers, "_m4_cache", None)
    client, _, _ = env
    assert client.post("/ai/match", json={"job_id": 10, "model": "m4"}).status_code == 503
    assert client.post("/ai/match", json={"job_id": 10, "model": "zzz"}).status_code == 422


def test_match_unknown_job_404_and_candidate_cannot_use_other_profile(env):
    client, _, _ = env
    assert client.post("/ai/match", json={"job_id": 999}).status_code == 404
    assert client.post("/ai/match", json={"job_id": 10, "candidate_id": 2}).status_code == 403


def test_recruiter_match_rules(env):
    client, _, state = env
    login(state, "recruiter", uid=50, company=100)
    assert client.post("/ai/match", json={"job_id": 10}).status_code == 422  # thiếu candidate_id
    assert client.post("/ai/match", json={"job_id": 10, "candidate_id": 1}).status_code == 200
    assert client.post("/ai/match", json={"job_id": 10, "candidate_id": 2}).status_code == 403  # chưa nộp
    login(state, "recruiter", uid=51, company=200)
    assert client.post("/ai/match", json={"job_id": 10, "candidate_id": 1}).status_code == 403  # tin công ty khác


def test_matches_and_recommendations(env):
    client, _, _ = env
    items = client.get("/candidates/me/matches").json()["items"]
    assert {i["job_id"] for i in items} == {10, 11}
    top = client.get("/candidates/me/recommendations?top=1").json()["items"]
    assert len(top) == 1 and top[0]["job_id"] == 10  # hồ sơ frontend phù hợp tin frontend hơn


def test_skill_gap_orders_required_first(env):
    client, _, _ = env
    r = client.get("/candidates/me/skill-gap?job_id=10").json()
    assert [m["skill"] for m in r["missing"]] == ["React", "TypeScript"]
    assert r["missing"][0]["required"] is True and r["missing"][1]["required"] is False
    assert r["missing"][0]["jobs_demanding"] == 5 and r["missing"][0]["learning_steps"] == ["Học React"]
    # kỹ năng chưa có dữ liệu riêng dùng lộ trình mặc định (3 bước)
    assert len(r["missing"][1]["learning_steps"]) == 3 and "TypeScript" in r["missing"][1]["learning_steps"][0]


def test_ranked_candidates_permissions(env):
    client, _, state = env
    assert client.get("/jobs/10/ranked-candidates").status_code == 403  # ứng viên không được xem
    login(state, "recruiter", uid=50, company=100)
    r = client.get("/jobs/10/ranked-candidates")
    assert r.status_code == 200
    only = r.json()["items"][0]
    assert only["candidate_id"] == 1 and only["application_id"] == 7 and only["status"] == "applied"
    login(state, "recruiter", uid=51, company=200)
    assert client.get("/jobs/10/ranked-candidates").status_code == 403
    login(state, "admin", uid=1)
    assert client.get("/jobs/10/ranked-candidates").status_code == 200


def test_extract_skills_recruiter_only(env):
    client, _, state = env
    assert client.post("/ai/extract-skills", json={"text": "cần React và Docker"}).status_code == 403
    login(state, "recruiter", uid=50, company=100)
    r = client.post("/ai/extract-skills", json={"text": "cần React và Docker"})
    assert {s["name"] for s in r.json()["skills"]} == {"React", "Docker"}


def test_upload_requires_consent_and_maps_errors(env):
    client, repo, _ = env
    cv = "Kỹ năng\nReact, Git, Docker, HTML, CSS\nHọc vấn\nĐại học Thủy lợi\n".encode()
    assert client.post("/resumes/upload", files={"file": ("cv.txt", cv)}).status_code == 400
    ok = client.post("/resumes/upload", files={"file": ("cv.txt", cv)}, data={"consent": "true"})
    assert ok.status_code == 200
    body = ok.json()
    assert body["resume_id"] == 99 and {"React", "Git"} <= {s["name"] for s in body["skills"]}
    assert body["education_level"] == 3 and "skills" in body["sections_found"]
    assert repo.resumes[0]["consent"] is True and "embedding" in repo.resumes[0]["keys"]
    consent = {"consent": "true"}
    assert client.post("/resumes/upload", files={"file": ("cv.exe", cv)}, data=consent).status_code == 415
    assert client.post("/resumes/upload", files={"file": ("cv.txt", b"  ")}, data=consent).status_code == 422
    assert client.post("/resumes/upload", files={"file": ("cv.pdf", b"nope")}, data=consent).status_code == 422
    assert client.post("/resumes/upload", files={"file": ("cv.txt", b"a" * (5 * 1024 * 1024 + 10))}, data=consent).status_code == 413


def test_upload_forbidden_for_recruiter(env):
    client, _, state = env
    login(state, "recruiter", uid=50, company=100)
    r = client.post("/resumes/upload", files={"file": ("cv.txt", b"x" * 100)}, data={"consent": "true"})
    assert r.status_code == 403
