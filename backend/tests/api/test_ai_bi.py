"""AI và BI qua API thật (repo SQL trên SQLite), không dùng repository giả."""
import datetime as dt

import httpx
import pytest
from sqlalchemy import select

from app.ai import scorers
from app.models import Application, ApplicationStatusHistory, Candidate, Job
from tests.api.conftest import JOB_BODY, auth, register

CV = (
    "Nguyễn Văn An\nan@example.com\n"
    "Kỹ năng\nReactjs, HTML5, CSS, Javascrip, Git\n"
    "Kinh nghiệm\nFrontend Intern - Công ty ABC 06/2024 - 09/2024\n"
    "Học vấn\nĐại học Thủy lợi 2022 - 2026\n"
).encode("utf-8")


def upload(c, token, consent="true", name="cv.txt", data=CV):
    return c.post("/api/resumes/upload", files={"file": (name, data)}, data={"consent": consent}, headers=auth(token))


def test_upload_cv_suggests_skills_then_candidate_confirms(world):
    c, token = world["client"], world["ca"]["access_token"]
    r = upload(c, token)
    assert r.status_code == 200, r.text
    body = r.json()
    names = {s["name"] for s in body["skills"]}
    assert {"React", "HTML", "CSS", "JavaScript", "Git"} <= names  # alias và lỗi gõ đều được chuẩn hoá
    assert body["education_level"] == 3 and body["years_exp"] == pytest.approx(0.3, abs=0.1) and body["resume_id"]
    # chưa xác nhận nên chưa tính vào hồ sơ
    assert c.get("/api/candidates/me", headers=auth(token)).json()["skills"] == []
    suggested = c.get("/api/candidates/me/skills", headers=auth(token)).json()["skills"]
    assert suggested and all(s["source"] == "cv" and s["confirmed"] is False for s in suggested)
    c.put("/api/candidates/me/skills", json={"skills": ["React", "HTML", "Git"]}, headers=auth(token))
    assert c.get("/api/candidates/me", headers=auth(token)).json()["skills"] == ["HTML", "React", "Git"]


def test_upload_requires_consent_and_validates_files(world):
    c, token = world["client"], world["ca"]["access_token"]
    assert upload(c, token, consent="false").status_code == 400
    assert upload(c, token, name="cv.exe").status_code == 415
    assert upload(c, token, data=b"  ").status_code == 422
    assert upload(c, token, data=b"a" * (5 * 1024 * 1024 + 5)).status_code == 413
    assert upload(c, world["ra"]["access_token"]).status_code == 403
    assert upload(c, token, name="cv.pdf", data=b"khong-phai-pdf").status_code == 422


def test_new_upload_replaces_active_resume(world, session):
    c, token = world["client"], world["ca"]["access_token"]
    first, second = upload(c, token).json()["resume_id"], upload(c, token).json()["resume_id"]
    from app.models import Resume

    actives = session.scalars(select(Resume.id).where(Resume.is_active.is_(True))).all()
    assert actives == [second] and first != second


def test_match_and_recommendations_use_confirmed_skills(world, tmp_path, monkeypatch):
    monkeypatch.setattr(scorers, "MODELS_DIR", tmp_path)  # độc lập với m4.joblib (mô phỏng) đã commit trong models_store
    monkeypatch.setattr(scorers, "_m4_cache", None)
    c, token = world["client"], world["ca"]["access_token"]
    c.put("/api/candidates/me", json={"skills": ["HTML", "CSS"], "preferredLocations": ["Hà Nội"], "preferredWorkTypes": ["Thực tập"], "consent": True}, headers=auth(token))
    jid = world["job"]["id"]
    for model in ("m0", "m1", "m2", "m3"):
        r = c.post("/api/ai/match", json={"job_id": jid, "model": model}, headers=auth(token))
        assert r.status_code == 200 and r.json()["model"] == model
    m3 = c.post("/api/ai/match", json={"job_id": jid}, headers=auth(token)).json()
    assert m3["matched_required"] == ["HTML", "CSS"] and m3["missing_required"] == ["React"] and m3["missing_preferred"] == ["TypeScript", "Git"]
    assert "Thiếu React (bắt buộc)" in m3["explanation"]
    assert c.post("/api/ai/match", json={"job_id": jid, "model": "m4"}, headers=auth(token)).status_code == 503
    rec = c.get("/api/candidates/me/recommendations", params={"top": 5}, headers=auth(token)).json()["items"]
    assert rec[0]["job_id"] == jid
    items = c.get("/api/candidates/me/matches", headers=auth(token)).json()["items"]
    assert [i["job_id"] for i in items] == [jid]


def test_match_results_are_persisted_per_model_version(world, session):
    c, token = world["client"], world["ca"]["access_token"]
    c.put("/api/candidates/me", json={"skills": ["HTML"], "consent": True}, headers=auth(token))
    for model in ("m0", "m3", "m3"):
        c.post("/api/ai/match", json={"job_id": world["job"]["id"], "model": model}, headers=auth(token))
    from app.models import MatchResult

    rows = session.scalars(select(MatchResult)).all()
    assert sorted(r.model_version for r in rows) == ["m0-rule-v1", "m3-hybrid-v1"]  # m3 gọi hai lần vẫn một dòng


def test_skill_gap_with_default_learning_steps(world, session):
    c, token = world["client"], world["ca"]["access_token"]
    c.put("/api/candidates/me", json={"skills": ["HTML"], "consent": True}, headers=auth(token))
    from app.models import Skill

    session.scalar(select(Skill).where(Skill.name == "React")).learning_steps = ["Học React cơ bản", "Làm mini project"]
    session.commit()
    gap = c.get("/api/candidates/me/skill-gap", params={"job_id": world["job"]["id"]}, headers=auth(token)).json()
    skills = [m["skill"] for m in gap["missing"]]
    assert skills[:2] == ["CSS", "React"] or skills[:2] == ["React", "CSS"]
    react = next(m for m in gap["missing"] if m["skill"] == "React")
    assert react["learning_steps"] == ["Học React cơ bản", "Làm mini project"] and react["jobs_demanding"] == 1 and react["required"] is True
    css = next(m for m in gap["missing"] if m["skill"] == "CSS")
    assert len(css["learning_steps"]) == 3  # lộ trình mặc định
    assert [m["required"] for m in gap["missing"]] == [True, True, False, False]


def test_ranked_candidates_only_applicants_of_own_job(world):
    c, jid = world["client"], world["job"]["id"]
    c.put("/api/candidates/me", json={"skills": ["HTML", "CSS", "React"], "consent": True}, headers=auth(world["ca"]["access_token"]))
    c.put("/api/candidates/me", json={"skills": ["SQL"], "consent": True}, headers=auth(world["cb"]["access_token"]))
    c.post("/api/applications", json={"job_id": jid}, headers=auth(world["ca"]["access_token"]))
    # Bình chưa nộp nên không được xuất hiện dù có hồ sơ
    r = c.get(f"/api/jobs/{jid}/ranked-candidates", headers=auth(world["ra"]["access_token"]))
    assert r.status_code == 200
    assert [i["full_name"] for i in r.json()["items"]] == ["Nguyễn Văn An"] and r.json()["items"][0]["status"] == "applied"
    assert c.get(f"/api/jobs/{jid}/ranked-candidates", headers=auth(world["rb"]["access_token"])).status_code == 403
    assert c.get(f"/api/jobs/{jid}/ranked-candidates", headers=auth(world["ca"]["access_token"])).status_code == 403
    # nhà tuyển dụng chỉ chấm được ứng viên đã nộp vào tin của mình
    ok = c.post("/api/ai/match", json={"job_id": jid, "candidate_id": 1}, headers=auth(world["ra"]["access_token"]))
    assert ok.status_code == 200
    no = c.post("/api/ai/match", json={"job_id": jid, "candidate_id": 2}, headers=auth(world["ra"]["access_token"]))
    assert no.status_code == 403


def test_extract_skills_for_job_description(world):
    c = world["client"]
    r = c.post("/api/ai/extract-skills", json={"text": "Cần thành thạo reactjs, Git và hiểu Docker"}, headers=auth(world["ra"]["access_token"]))
    assert {s["name"] for s in r.json()["skills"]} == {"React", "Git", "Docker"}
    assert c.post("/api/ai/extract-skills", json={"text": "x"}, headers=auth(world["ca"]["access_token"])).status_code == 403


def test_m4_available_after_training(world, tmp_path, monkeypatch):
    import numpy as np

    from app.ai.train import fit_m4, save_m4

    rng = np.random.default_rng(0)
    X = rng.random((200, 6))
    save_m4(fit_m4(X, (X[:, 0] > 0.5).astype(int)), tmp_path / "m4.joblib", "m4-test")
    monkeypatch.setattr(scorers, "MODELS_DIR", tmp_path)
    monkeypatch.setattr(scorers, "_m4_cache", None)
    c, token = world["client"], world["ca"]["access_token"]
    c.put("/api/candidates/me", json={"skills": ["HTML"], "consent": True}, headers=auth(token))
    r = c.post("/api/ai/match", json={"job_id": world["job"]["id"], "model": "m4"}, headers=auth(token))
    assert r.status_code == 200 and r.json()["model_version"] == "m4-test"


# ------------------------------------------------------------------ BI


def add_application(session, cand_id, job_id, history, score=None, days_ago=30):
    """history: danh sách (trạng thái, ngày sau khi nộp)."""
    applied = dt.datetime(2026, 10, 1) - dt.timedelta(days=days_ago - 30)
    app = Application(candidate_id=cand_id, job_id=job_id, match_score=score, status=history[-1][0], applied_at=applied, updated_at=applied)
    session.add(app)
    session.flush()
    prev = None
    for status, offset in history:
        session.add(ApplicationStatusHistory(application_id=app.id, from_status=prev, to_status=status, changed_at=applied + dt.timedelta(days=offset)))
        prev = status
    session.commit()
    return app


@pytest.fixture()
def funnel_world(world, session):
    """4 đơn vào tin của công ty A: 1 hired, 1 dừng ở offer, 1 rớt ở phỏng vấn, 1 mới nộp."""
    cand_ids = [c.id for c in session.scalars(select(Candidate).order_by(Candidate.id))]
    jid = world["job"]["id"]
    # Thêm hai ứng viên nữa
    for e in ("c@test.vn", "d@test.vn"):
        register(world["client"], e)
    cand_ids = [c.id for c in session.scalars(select(Candidate).order_by(Candidate.id))]
    add_application(session, cand_ids[0], jid, [("applied", 0), ("screening", 2), ("interview", 5), ("offer", 8), ("hired", 10)], score=85)
    add_application(session, cand_ids[1], jid, [("applied", 0), ("screening", 1), ("interview", 4), ("offer", 7)], score=65)
    add_application(session, cand_ids[2], jid, [("applied", 0), ("screening", 1), ("interview", 3), ("rejected", 6)], score=45)
    add_application(session, cand_ids[3], jid, [("applied", 0)], score=20)
    return world


def test_funnel_counts_ever_reached_not_current_status(funnel_world):
    c = funnel_world["client"]
    data = c.get("/api/bi/funnel", headers=auth(funnel_world["ra"]["access_token"])).json()
    counts = {s["stage"]: s["count"] for s in data["stages"]}
    # Hồ sơ đã hired vẫn được đếm ở screening/interview/offer: đếm "từng đạt", không đếm trạng thái hiện tại
    assert counts == {"applied": 4, "screening": 3, "interview": 3, "offer": 2, "hired": 1}
    conv = {s["stage"]: s["conversion_from_prev"] for s in data["stages"]}
    assert conv["screening"] == 0.75 and conv["interview"] == 1.0 and conv["offer"] == pytest.approx(0.6667, abs=1e-4) and conv["hired"] == 0.5
    assert data["total_conversion"] == 0.25 and data["median_time_to_hire_days"] == 10.0
    bands = {b["band"]: (b["applications"], b["hired"]) for b in data["by_score_band"]}
    assert bands == {"0–40": (1, 0), "40–60": (1, 0), "60–80": (1, 0), "80–100": (1, 1)}


def test_funnel_is_scoped_to_company_but_admin_sees_all(funnel_world, session):
    c = funnel_world["client"]
    rb = c.get("/api/bi/funnel", headers=auth(funnel_world["rb"]["access_token"])).json()
    assert rb["stages"][0]["count"] == 0 and rb["total_conversion"] is None
    from tests.api.conftest import login

    admin = auth(login(c, "admin@test.vn"))
    assert c.get("/api/bi/funnel", headers=admin).json()["stages"][0]["count"] == 4
    assert c.get("/api/bi/funnel", params={"company_id": 999}, headers=admin).json()["stages"][0]["count"] == 0
    assert c.get("/api/bi/funnel", headers=auth(funnel_world["ca"]["access_token"])).status_code == 403


def test_summary_skills_and_salary(funnel_world, session):
    c = funnel_world["client"]
    c.put("/api/candidates/me/skills", json={"skills": ["HTML", "React"]}, headers=auth(funnel_world["ca"]["access_token"]))
    c.put("/api/candidates/me/skills", json={"skills": ["HTML"]}, headers=auth(funnel_world["cb"]["access_token"]))
    summary = c.get("/api/bi/summary", headers=auth(funnel_world["ca"]["access_token"])).json()
    assert summary == {"candidates": 4, "open_jobs": 1, "applications": 4, "hire_rate": 0.25}
    hr = auth(funnel_world["ra"]["access_token"])
    rows = {r["skill"]: r for r in c.get("/api/bi/skills", headers=hr).json()["items"]}
    assert rows["HTML"]["so_ung_vien"] == 2 and rows["HTML"]["so_tin_yeu_cau"] == 1 and rows["HTML"]["shortage"] == 0.5
    assert rows["React"]["so_ung_vien"] == 1 and rows["React"]["shortage"] == 1.0
    assert rows["SQL"]["so_ung_vien"] == 0 and rows["SQL"]["shortage"] is None
    # tin có lương 3–5 triệu đăng hôm nay → trung vị 4.0
    sal = c.get("/api/bi/salary", headers=hr).json()
    assert sal["items"][0]["level"] == "intern" and sal["items"][0]["median_salary"] == 4.0 and sal["items"][0]["n"] == 1
    assert c.get("/api/bi/skills", headers=auth(funnel_world["ca"]["access_token"])).status_code == 403


def test_salary_skips_negotiable_jobs(funnel_world, session):
    c, hr = funnel_world["client"], auth(funnel_world["ra"]["access_token"])
    c.post("/api/jobs", json={**JOB_BODY, "title": "Thoả thuận", "salary_min": None, "salary_max": None}, headers=hr)
    assert c.get("/api/bi/salary", headers=hr).json()["items"][0]["n"] == 1


def _mock_superset(monkeypatch, calls):
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.url.path, request.read().decode()))
        if request.url.path.endswith("/security/login"):
            return httpx.Response(200, json={"access_token": "ADMIN-JWT"})
        assert request.headers["authorization"] == "Bearer ADMIN-JWT"
        return httpx.Response(200, json={"token": "GUEST-TOKEN"})

    real = httpx.Client
    monkeypatch.setattr("app.routers.bi.httpx.Client", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))


def test_guest_token_applies_company_rls_for_recruiter(world, monkeypatch):
    import json

    from app.config import get_settings

    s = get_settings()
    for k, v in {"superset_url": "http://superset:8088", "superset_dashboard_id": "uuid-123", "superset_rls_dataset_ids": "7,8"}.items():
        monkeypatch.setattr(s, k, v)
    calls: list = []
    _mock_superset(monkeypatch, calls)
    r = world["client"].get("/api/bi/guest-token", headers=auth(world["ra"]["access_token"]))
    assert r.status_code == 200 and r.json() == {"token": "GUEST-TOKEN", "dashboard_id": "uuid-123", "superset_domain": s.superset_public_url}
    sent = json.loads(calls[-1][1])
    assert sent["resources"] == [{"type": "dashboard", "id": "uuid-123"}]
    cid = world["ra"]["user"]["company_id"]
    assert sent["rls"] == [{"dataset": 7, "clause": f"company_id = {cid}"}, {"dataset": 8, "clause": f"company_id = {cid}"}]
    from tests.api.conftest import login

    world["client"].get("/api/bi/guest-token", headers=auth(login(world["client"], "admin@test.vn")))
    assert json.loads(calls[-1][1])["rls"] == []  # quản trị xem toàn thị trường


def test_guest_token_refused_for_recruiter_without_rls_datasets(world, monkeypatch):
    """Thiếu cấu hình RLS thì không cấp token cho recruiter (tránh lộ dữ liệu công ty khác)."""
    from app.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "superset_url", "http://superset:8088")
    monkeypatch.setattr(s, "superset_dashboard_id", "uuid-123")
    monkeypatch.setattr(s, "superset_rls_dataset_ids", "")
    r = world["client"].get("/api/bi/guest-token", headers=auth(world["ra"]["access_token"]))
    assert r.status_code == 503 and r.json()["detail"] == "superset_not_configured"


def test_guest_token_unconfigured_or_forbidden(world, monkeypatch):
    from app.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "superset_url", "")  # độc lập với biến môi trường của máy chạy test
    monkeypatch.setattr(s, "superset_dashboard_id", "")
    c = world["client"]
    assert c.get("/api/bi/guest-token", headers=auth(world["ra"]["access_token"])).json()["detail"] == "superset_not_configured"
    assert c.get("/api/bi/guest-token", headers=auth(world["ca"]["access_token"])).status_code == 403


def test_profile_embedding_is_stored_on_save_and_scoring_does_not_re_encode(world, session, monkeypatch):
    """Yêu cầu phi chức năng: embedding tính sẵn khi lưu; chấm điểm lúc yêu cầu không được mã hoá lại hồ sơ/tin."""
    c, token = world["client"], world["ca"]["access_token"]
    c.put("/api/candidates/me", json={"skills": ["HTML", "CSS", "React"], "careerGoal": "Frontend", "consent": True}, headers=auth(token))
    cand = session.scalar(select(Candidate).where(Candidate.full_name == "Nguyễn Văn An"))
    session.refresh(cand)
    assert cand.embedding is not None and len(cand.embedding) == 384 * 4

    def boom(text):
        raise AssertionError("không được mã hoá lại khi chấm điểm")

    monkeypatch.setattr("app.services.ai_repo.embed_text", boom)
    monkeypatch.setattr("app.services.jobs.embed_text", boom)
    r = c.post("/api/ai/match", json={"job_id": world["job"]["id"], "model": "m3"}, headers=auth(token))
    assert r.status_code == 200 and r.json()["components"]["semantic"] is not None
    assert c.get("/api/candidates/me/matches", headers=auth(token)).status_code == 200


def test_confirming_skills_refreshes_profile_embedding(world, session):
    c, token = world["client"], world["ca"]["access_token"]
    c.put("/api/candidates/me/skills", json={"skills": ["HTML"]}, headers=auth(token))
    cand = session.scalar(select(Candidate).where(Candidate.full_name == "Nguyễn Văn An"))
    session.refresh(cand)
    first = cand.embedding
    c.put("/api/candidates/me/skills", json={"skills": ["Python", "SQL", "Docker"]}, headers=auth(token))
    session.refresh(cand)
    assert cand.embedding is not None and cand.embedding != first


def test_m1_tfidf_is_fitted_on_job_corpus_and_ranks_by_text(world):
    c, ra, token = world["client"], auth(world["ra"]["access_token"]), world["ca"]["access_token"]
    c.post("/api/jobs", json={**JOB_BODY, "title": "Data Analyst", "description": "Phân tích dữ liệu bằng SQL và Python, báo cáo Power BI",
                              "category": "Data Science & Analytics", "required_skills": ["SQL", "Python"], "preferred_skills": []}, headers=ra)
    c.put("/api/candidates/me", json={"skills": ["HTML", "CSS", "React"], "careerGoal": "Làm giao diện web frontend React", "consent": True}, headers=auth(token))
    jobs = c.get("/api/jobs", headers=auth(token)).json()["items"]
    score = {j["title"]: c.post("/api/ai/match", json={"job_id": j["id"], "model": "m1"}, headers=auth(token)).json()["total_score"] for j in jobs}
    assert score["Frontend Intern"] > score["Data Analyst"], score
