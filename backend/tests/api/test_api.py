from __future__ import annotations

from fastapi.testclient import TestClient

from .conftest import auth


def test_login_rejects_wrong_password(api: TestClient):
    response = api.post("/api/auth/login", json={"email": "candidate@smartcareer.vn", "password": "wrong-password"})
    assert response.status_code == 401


def test_role_guard_returns_403(api: TestClient):
    response = api.get("/api/admin/skills", headers=auth(api, "candidate@smartcareer.vn"))
    assert response.status_code == 403


def test_application_duplicate_returns_409(api: TestClient):
    headers = auth(api, "candidate@smartcareer.vn")
    body = {"job_id": api.state.job_a_id}
    assert api.post("/api/applications", json=body, headers=headers).status_code == 201
    response = api.post("/api/applications", json=body, headers=headers)
    assert response.status_code == 409
    assert response.json()["detail"] == "already_applied"


def test_status_skip_returns_contract_409(api: TestClient):
    candidate_headers = auth(api, "candidate@smartcareer.vn")
    applied = api.post("/api/applications", json={"job_id": api.state.job_a_id}, headers=candidate_headers)
    app_id = applied.json()["id"]
    response = api.patch(f"/api/applications/{app_id}/status", json={"status": "interview"}, headers=auth(api, "hr.a@smartcareer.vn"))
    assert response.status_code == 409
    assert response.json() == {"detail": {"detail": "invalid_transition", "from": "applied", "to": "interview"}}


def test_recruiter_cannot_view_other_company_applications(api: TestClient):
    candidate_headers = auth(api, "candidate@smartcareer.vn")
    api.post("/api/applications", json={"job_id": api.state.job_b_id}, headers=candidate_headers)
    response = api.get(f"/api/jobs/{api.state.job_b_id}/applications", headers=auth(api, "hr.a@smartcareer.vn"))
    assert response.status_code == 403


def test_resume_rejects_unsupported_extension(api: TestClient):
    response = api.post("/api/resumes/upload", data={"consent": "true"}, files={"file": ("cv.csv", b"not a cv", "text/csv")}, headers=auth(api, "candidate@smartcareer.vn"))
    assert response.status_code == 415


def test_job_filter_and_pagination(api: TestClient):
    headers = auth(api, "candidate@smartcareer.vn")
    result = api.get("/api/jobs?q=React&location=Hà Nội&category=Frontend Development&page=1&page_size=1", headers=headers)
    assert result.status_code == 200
    payload = result.json()
    assert payload["total"] == 2
    assert payload["page"] == 1 and payload["page_size"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["title"].startswith("React")


def test_apply_accepts_string_job_id(api: TestClient):
    response = api.post("/api/applications", json={"job_id": str(api.state.job_a_id)}, headers=auth(api, "candidate@smartcareer.vn"))
    assert response.status_code == 201


def test_register_blocks_admin_and_requires_company_for_recruiter(api: TestClient):
    body = {"email": "new@smartcareer.vn", "password": "Demo@12345", "full_name": "Người Mới"}
    assert api.post("/api/auth/register", json={**body, "role": "admin"}).status_code == 422
    response = api.post("/api/auth/register", json={**body, "role": "recruiter"})
    assert response.status_code in {400, 422} and "company_name_required" in response.text


def test_other_company_cannot_change_status(api: TestClient):
    applied = api.post("/api/applications", json={"job_id": api.state.job_a_id}, headers=auth(api, "candidate@smartcareer.vn"))
    response = api.patch(f"/api/applications/{applied.json()['id']}/status", json={"status": "screening"}, headers=auth(api, "hr.b@smartcareer.vn"))
    assert response.status_code == 403


def test_resume_over_5mb_returns_413(api: TestClient):
    big = b"%PDF-1.4 " + b"x" * (5 * 1024 * 1024 + 10)
    response = api.post("/api/resumes/upload", data={"consent": "true"}, files={"file": ("cv.pdf", big, "application/pdf")}, headers=auth(api, "candidate@smartcareer.vn"))
    assert response.status_code == 413
