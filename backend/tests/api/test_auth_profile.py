from tests.api.conftest import PASSWORD, auth, login, register


def test_register_login_me(client):
    reg = register(client, "an@test.vn", name="Nguyễn Văn An")
    assert reg["user"]["role"] == "candidate" and reg["token_type"] == "bearer"
    token = login(client, "AN@test.vn")  # email không phân biệt hoa thường
    me = client.get("/api/auth/me", headers=auth(token)).json()
    assert me["email"] == "an@test.vn" and me["full_name"] == "Nguyễn Văn An"


def test_duplicate_email_and_bad_credentials(client):
    register(client, "an@test.vn")
    dup = client.post("/api/auth/register", json={"email": "an@test.vn", "password": PASSWORD, "role": "candidate", "full_name": "X"})
    assert dup.status_code == 409 and dup.json()["detail"] == "email_taken"
    assert client.post("/api/auth/login", json={"email": "an@test.vn", "password": "sai-mat-khau"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "ko-co@test.vn", "password": PASSWORD}).status_code == 401


def test_validation_and_no_admin_registration(client):
    short = client.post("/api/auth/register", json={"email": "a@test.vn", "password": "123", "role": "candidate", "full_name": "A"})
    assert short.status_code == 422
    admin = client.post("/api/auth/register", json={"email": "a@test.vn", "password": PASSWORD, "role": "admin", "full_name": "A"})
    assert admin.status_code == 422
    no_company = client.post("/api/auth/register", json={"email": "r@test.vn", "password": PASSWORD, "role": "recruiter", "full_name": "R"})
    assert no_company.status_code == 422


def test_recruiter_registration_creates_company_and_reuses_it(client):
    a = register(client, "hr1@test.vn", "recruiter", "Công ty Mẫu")
    b = register(client, "hr2@test.vn", "recruiter", "Công ty Mẫu")
    assert a["user"]["company_id"] == b["user"]["company_id"] is not None


def test_protected_routes_need_token_and_role(client):
    assert client.get("/api/candidates/me").status_code == 401
    assert client.get("/api/candidates/me", headers={"Authorization": "Bearer rac-roi"}).status_code == 401
    rec = register(client, "hr@test.vn", "recruiter", "Công ty A")
    assert client.get("/api/candidates/me", headers=auth(rec["access_token"])).status_code == 403


def test_profile_roundtrip_with_skills_and_consent(client):
    token = register(client, "an@test.vn", name="Nguyễn Văn An")["access_token"]
    body = {
        "fullName": "Nguyễn Văn An", "university": "ĐH Thủy lợi", "major": "CNTT", "year": "Năm 4", "phone": "0912345678",
        "careerGoal": "Frontend", "skills": ["HTML", "reactjs", "Python cơ bản", "Kỹ năng lạ"],
        "preferredLocations": ["Hà Nội"], "preferredWorkTypes": ["Thực tập"], "languages": ["Tiếng Anh"],
        "projects": [{"name": "Web"}], "experience": [{"position": "Intern"}], "certificates": [{"name": "TOEIC"}], "consent": True,
    }
    r = client.put("/api/candidates/me", json=body, headers=auth(token))
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["skills"] == ["HTML", "React", "Python"]  # alias và hậu tố "cơ bản" được chuẩn hoá; kỹ năng lạ bị bỏ
    assert out["consent"] is True and out["profileCompletion"] == 100 and out["email"] == "an@test.vn"
    again = client.get("/api/candidates/me", headers=auth(token)).json()
    assert again["preferredLocations"] == ["Hà Nội"] and again["projects"] == [{"name": "Web"}]


def test_confirm_skills_replaces_set_and_reports_unresolved(client):
    token = register(client, "an@test.vn")["access_token"]
    client.put("/api/candidates/me/skills", json={"skills": ["HTML", "CSS"]}, headers=auth(token))
    r = client.put("/api/candidates/me/skills", json={"skills": ["CSS", "Git", "Không có"]}, headers=auth(token)).json()
    assert r["skills"] == ["CSS", "Git"] and r["unresolved"] == ["Không có"]
    listed = client.get("/api/candidates/me/skills", headers=auth(token)).json()["skills"]
    assert {s["name"] for s in listed} == {"CSS", "Git"} and all(s["confirmed"] for s in listed)


def test_delete_profile_removes_account(client, world):
    token = world["ca"]["access_token"]
    client.post("/api/applications", json={"job_id": world["job"]["id"]}, headers=auth(token))
    assert client.delete("/api/candidates/me", headers=auth(token)).status_code == 204
    assert client.get("/api/auth/me", headers=auth(token)).status_code == 401
    assert client.post("/api/auth/login", json={"email": "an@test.vn", "password": PASSWORD}).status_code == 401
