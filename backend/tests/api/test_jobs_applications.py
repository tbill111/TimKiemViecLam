import pytest

from tests.api.conftest import JOB_BODY, auth, register


def test_recruiter_creates_job_and_dto_shape(world):
    job = world["job"]
    assert job["company"]["name"] == "Công ty A" and job["status"] == "open"
    assert job["required_skills"] == ["HTML", "CSS", "React"] and job["preferred_skills"] == ["TypeScript", "Git"]
    assert job["salary_min"] == 3 and job["location"] == "Hà Nội" and job["category"] == "Frontend Development"


def test_create_job_validations(world):
    c, h = world["client"], auth(world["ra"]["access_token"])
    assert c.post("/api/jobs", json={**JOB_BODY, "required_skills": ["HTML", "Skill Lạ"]}, headers=h).status_code == 422
    assert c.post("/api/jobs", json={**JOB_BODY, "salary_min": 9, "salary_max": 3}, headers=h).status_code == 422
    assert c.post("/api/jobs", json={**JOB_BODY, "category": "Không hợp lệ"}, headers=h).status_code == 422
    assert c.post("/api/jobs", json=JOB_BODY, headers=auth(world["ca"]["access_token"])).status_code == 403
    assert c.post("/api/jobs", json=JOB_BODY).status_code == 401


def test_only_owner_company_can_edit_or_close(world):
    c, jid = world["client"], world["job"]["id"]
    other = auth(world["rb"]["access_token"])
    assert c.put(f"/api/jobs/{jid}", json=JOB_BODY, headers=other).status_code == 403
    assert c.delete(f"/api/jobs/{jid}", headers=other).status_code == 403
    mine = auth(world["ra"]["access_token"])
    upd = c.put(f"/api/jobs/{jid}", json={**JOB_BODY, "title": "Frontend Intern (sửa)", "preferred_skills": ["Git"]}, headers=mine)
    assert upd.status_code == 200 and upd.json()["title"].endswith("(sửa)") and upd.json()["preferred_skills"] == ["Git"]
    assert c.delete(f"/api/jobs/{jid}", headers=mine).status_code == 204
    assert c.get(f"/api/jobs/{jid}").json()["status"] == "closed"
    assert c.get("/api/jobs").json()["total"] == 0  # tin đã đóng không còn trong danh sách công khai


def test_anonymous_list_and_filters(world):
    c, h = world["client"], auth(world["ra"]["access_token"])
    c.post("/api/jobs", json={**JOB_BODY, "title": "Data Analyst", "category": "Data Science & Analytics", "location": "Hồ Chí Minh",
                              "job_type": "full_time", "work_mode": "remote", "min_years_exp": 2,
                              "required_skills": ["SQL", "Python"], "preferred_skills": []}, headers=h)
    listing = c.get("/api/jobs").json()
    assert listing["total"] == 2 and "match" not in listing["items"][0]
    assert c.get("/api/jobs", params={"work_type": "Remote"}).json()["total"] == 1
    assert c.get("/api/jobs", params={"work_type": "Thực tập"}).json()["items"][0]["title"] == "Frontend Intern"
    assert c.get("/api/jobs", params={"experience": "2-3 năm"}).json()["items"][0]["title"] == "Data Analyst"
    assert c.get("/api/jobs", params={"experience": "Chưa có kinh nghiệm"}).json()["total"] == 1
    assert c.get("/api/jobs", params={"location": "Hồ Chí Minh"}).json()["total"] == 1
    assert c.get("/api/jobs", params={"location": "Tất cả"}).json()["total"] == 2
    assert c.get("/api/jobs", params={"category": "QA & Testing"}).json()["total"] == 0
    assert c.get("/api/jobs", params={"q": "python"}).json()["total"] == 1  # tìm theo kỹ năng
    page = c.get("/api/jobs", params={"page": 2, "page_size": 1}).json()
    assert page["total"] == 2 and len(page["items"]) == 1


def test_candidate_sees_match_and_relevance_sort(world):
    c, ha = world["client"], auth(world["ca"]["access_token"])
    c.post("/api/jobs", json={**JOB_BODY, "title": "Data Analyst", "category": "Data Science & Analytics",
                              "required_skills": ["SQL", "Python"], "preferred_skills": []}, headers=auth(world["ra"]["access_token"]))
    c.put("/api/candidates/me", json={"skills": ["HTML", "CSS", "React"], "preferredLocations": ["Hà Nội"], "preferredWorkTypes": ["Thực tập"], "consent": True}, headers=ha)
    items = c.get("/api/jobs", headers=ha).json()["items"]
    assert [i["title"] for i in items] == ["Frontend Intern", "Data Analyst"]  # xếp theo điểm khớp
    assert items[0]["match"]["total_score"] > items[1]["match"]["total_score"]
    assert items[0]["match"]["missing_required"] == [] and items[1]["match"]["missing_required"] == ["SQL", "Python"]
    newest = c.get("/api/jobs", params={"sort": "newest"}, headers=ha).json()["items"]
    assert newest[0]["title"] == "Data Analyst"
    detail = c.get(f"/api/jobs/{world['job']['id']}", headers=ha).json()
    assert detail["match"]["model"] == "m3"


def test_mine_lists_own_company_incl_closed(world):
    c = world["client"]
    ra, rb = auth(world["ra"]["access_token"]), auth(world["rb"]["access_token"])
    c.delete(f"/api/jobs/{world['job']['id']}", headers=ra)
    assert c.get("/api/jobs", params={"mine": True}, headers=ra).json()["total"] == 1
    assert c.get("/api/jobs", params={"mine": True}, headers=rb).json()["total"] == 0
    assert c.get("/api/jobs", params={"mine": True}).status_code == 403


def test_locations_and_skills_catalog(world):
    c = world["client"]
    assert {"Hà Nội", "Remote"} <= {x["name"] for x in c.get("/api/locations").json()["items"]}
    assert "React" in {x["name"] for x in c.get("/api/skills").json()["items"]}


# ------------------------------------------------------------------ ứng tuyển


def apply_(c, token, job_id):
    return c.post("/api/applications", json={"job_id": job_id}, headers=auth(token))


def test_apply_records_score_history_and_blocks_duplicates(world):
    c, jid = world["client"], world["job"]["id"]
    token = world["ca"]["access_token"]
    c.put("/api/candidates/me", json={"skills": ["HTML", "CSS"], "consent": True}, headers=auth(token))
    r = apply_(c, token, jid)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "applied" and 0 <= body["match_score"] <= 100
    assert body["history"] == [{"from_status": None, "to_status": "applied", "changed_at": body["history"][0]["changed_at"], "note": ""}]
    assert apply_(c, token, jid).json()["detail"] == "already_applied"
    mine = c.get("/api/applications/me", headers=auth(token)).json()["items"]
    assert len(mine) == 1 and mine[0]["job"]["title"] == "Frontend Intern"
    assert apply_(c, token, 9999).status_code == 404


def test_cannot_apply_to_closed_job_or_as_recruiter(world):
    c, jid = world["client"], world["job"]["id"]
    assert apply_(c, world["ra"]["access_token"], jid).status_code == 403
    c.delete(f"/api/jobs/{jid}", headers=auth(world["ra"]["access_token"]))
    r = apply_(c, world["ca"]["access_token"], jid)
    assert r.status_code == 409 and r.json()["detail"] == "job_closed"


def _status(c, token, app_id, status):
    return c.patch(f"/api/applications/{app_id}/status", json={"status": status}, headers=auth(token))


def test_status_flow_follows_funnel_and_logs_history(world):
    c = world["client"]
    app_id = apply_(c, world["ca"]["access_token"], world["job"]["id"]).json()["id"]
    hr = world["ra"]["access_token"]
    for nxt in ("screening", "interview", "offer", "hired"):
        r = _status(c, hr, app_id, nxt)
        assert r.status_code == 200 and r.json()["status"] == nxt
    history = c.get("/api/applications/me", headers=auth(world["ca"]["access_token"])).json()["items"][0]["history"]
    assert [h["to_status"] for h in history] == ["applied", "screening", "interview", "offer", "hired"]
    assert [h["from_status"] for h in history] == [None, "applied", "screening", "interview", "offer"]


@pytest.mark.parametrize("bad", ["interview", "offer", "hired", "applied"])
def test_jumping_steps_returns_409(world, bad):
    c = world["client"]
    app_id = apply_(c, world["ca"]["access_token"], world["job"]["id"]).json()["id"]
    r = _status(c, world["ra"]["access_token"], app_id, bad)
    assert r.status_code == 409 and r.json()["detail"] == {"detail": "invalid_transition", "from": "applied", "to": bad}


def test_final_states_cannot_change_and_reject_from_any_open_step(world):
    c, hr = world["client"], world["ra"]["access_token"]
    app_id = apply_(c, world["ca"]["access_token"], world["job"]["id"]).json()["id"]
    _status(c, hr, app_id, "screening")
    assert _status(c, hr, app_id, "rejected").status_code == 200
    assert _status(c, hr, app_id, "screening").status_code == 409
    assert _status(c, hr, app_id, "rejected").status_code == 409


def test_other_company_and_candidates_cannot_change_status(world):
    c = world["client"]
    app_id = apply_(c, world["ca"]["access_token"], world["job"]["id"]).json()["id"]
    assert _status(c, world["rb"]["access_token"], app_id, "screening").status_code == 403
    assert _status(c, world["ca"]["access_token"], app_id, "screening").status_code == 403
    assert c.get(f"/api/jobs/{world['job']['id']}/applications", headers=auth(world["rb"]["access_token"])).status_code == 403
    assert _status(c, world["ra"]["access_token"], 9999, "screening").status_code == 404


def test_recruiter_lists_applicants_sorted_by_score(world):
    c = world["client"]
    c.put("/api/candidates/me", json={"skills": ["HTML", "CSS", "React"], "consent": True}, headers=auth(world["ca"]["access_token"]))
    c.put("/api/candidates/me", json={"skills": ["SQL"], "consent": True}, headers=auth(world["cb"]["access_token"]))
    apply_(c, world["cb"]["access_token"], world["job"]["id"])
    apply_(c, world["ca"]["access_token"], world["job"]["id"])
    items = c.get(f"/api/jobs/{world['job']['id']}/applications", headers=auth(world["ra"]["access_token"])).json()["items"]
    assert [i["candidate_name"] for i in items] == ["Nguyễn Văn An", "Trần Thị Bình"]
    assert items[0]["match_score"] > items[1]["match_score"]


def test_saved_jobs_crud(world):
    c, token, jid = world["client"], world["ca"]["access_token"], world["job"]["id"]
    assert c.post(f"/api/saved-jobs/{jid}", headers=auth(token)).status_code == 201
    assert c.post(f"/api/saved-jobs/{jid}", headers=auth(token)).status_code == 201  # idempotent
    items = c.get("/api/saved-jobs", headers=auth(token)).json()["items"]
    assert len(items) == 1 and items[0]["job"]["title"] == "Frontend Intern"
    assert c.delete(f"/api/saved-jobs/{jid}", headers=auth(token)).status_code == 204
    assert c.get("/api/saved-jobs", headers=auth(token)).json()["items"] == []
    assert c.post("/api/saved-jobs/9999", headers=auth(token)).status_code == 404


def test_admin_skill_catalog(client, session):
    from tests.api.conftest import login

    admin = login(client, "admin@test.vn")
    h = auth(admin)
    assert client.post("/api/admin/skills", json={"name": "Vue", "category": "Frontend"}, headers=h).status_code == 201
    assert client.post("/api/admin/skills", json={"name": "Vue"}, headers=h).status_code == 409
    assert client.post("/api/admin/skill-aliases", json={"alias": "VueJS", "skill_name": "Vue"}, headers=h).status_code == 201
    assert client.post("/api/admin/skill-aliases", json={"alias": "vuejs", "skill_name": "Vue"}, headers=h).status_code == 409
    assert client.post("/api/admin/skill-aliases", json={"alias": "x", "skill_name": "Không có"}, headers=h).status_code == 404
    assert {"alias": "vuejs", "skill_name": "Vue"} in client.get("/api/admin/skill-aliases", headers=h).json()["items"]
    cand = register(client, "u@test.vn")["access_token"]
    assert client.get("/api/admin/skills", headers=auth(cand)).status_code == 403


def test_admin_can_edit_skill_and_delete_alias(client, session):
    from tests.api.conftest import login

    h = auth(login(client, "admin@test.vn"))
    skills = client.get("/api/admin/skills", headers=h).json()["items"]
    react = next(s for s in skills if s["name"] == "React")
    upd = client.put(f"/api/admin/skills/{react['id']}", json={"category": "Frontend", "learning_steps": ["Bước 1", " ", "Bước 2"]}, headers=h)
    assert upd.status_code == 200 and upd.json()["learning_steps"] == ["Bước 1", "Bước 2"]  # bỏ dòng trống
    # lộ trình mới được dùng ở Skill Gap
    assert client.put("/api/admin/skills/9999", json={}, headers=h).status_code == 404
    assert client.delete("/api/admin/skill-aliases/reactjs", headers=h).status_code == 204
    assert client.delete("/api/admin/skill-aliases/reactjs", headers=h).status_code == 404
    assert "reactjs" not in {a["alias"] for a in client.get("/api/admin/skill-aliases", headers=h).json()["items"]}
    cand = register(client, "u2@test.vn")["access_token"]
    assert client.put(f"/api/admin/skills/{react['id']}", json={}, headers=auth(cand)).status_code == 403
    assert client.delete("/api/admin/skill-aliases/html5", headers=auth(cand)).status_code == 403
