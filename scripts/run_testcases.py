"""Chạy tự động các test case thủ công trong docs/testcases.md bằng gọi API thật trên một stack đang chạy.

    python scripts/run_testcases.py --api http://localhost:8000/api [--web http://localhost:8080]

Phủ: TC05 (401 và chuyển về /login), TC06, TC07, TC10, TC11, TC13, TC23, TC27, TC28, TC29. Mỗi ca in `OK` hoặc `FAIL` kèm chi tiết;
mã thoát 1 nếu có ca lỗi. Dữ liệu tạo ra (tài khoản, tin) mang tiền tố `tc-` để dọn tay nếu cần. Nên chạy sau `load_seed --reset`.
TC26 (số liệu BI khớp SQL) do `scripts/check_bi_views.py` kiểm; TC31 do `scripts/e2e_ui.py --offline`; TC32 là `docker compose up` trên máy sạch.
"""
from __future__ import annotations

import argparse
import sys
import time

import httpx

sys.stdout.reconfigure(encoding="utf-8")
PASSWORD = "Demo@12345"
results: list[tuple[str, bool, str]] = []


def case(code: str, ok: bool, detail: str = "") -> None:
    results.append((code, ok, detail))
    print(f"  {'OK  ' if ok else 'FAIL'} {code}{(' – ' + detail) if detail else ''}")


class Api:
    def __init__(self, base: str):
        self.c = httpx.Client(base_url=base, timeout=60)

    def login(self, email: str, password: str = PASSWORD) -> dict[str, str]:
        r = self.c.post("/auth/login", json={"email": email, "password": password})
        r.raise_for_status()
        return {"Authorization": "Bearer " + r.json()["access_token"]}

    def register(self, role: str, email: str, name: str, company: str | None = None) -> dict[str, str]:
        body = {"email": email, "password": PASSWORD, "role": role, "full_name": name}
        if company:
            body["company_name"] = company
        r = self.c.post("/auth/register", json=body)
        r.raise_for_status()
        return {"Authorization": "Bearer " + r.json()["access_token"]}


def pick_job_of(api: Api, headers: dict[str, str]) -> int:
    items = api.c.get("/jobs", params={"mine": "true", "page_size": 5}, headers=headers).json()["items"]
    return int(items[0]["id"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000/api")
    ap.add_argument("--web", default=None, help="địa chỉ giao diện để kiểm TC05 phía trình duyệt (cần playwright)")
    args = ap.parse_args()
    api = Api(args.api)
    stamp = int(time.time())

    hr1, hr5, admin = api.login("hr1@smartcareer.vn"), api.login("hr5@smartcareer.vn"), api.login("admin@smartcareer.vn")
    print("== API")

    # TC05
    no_token = api.c.get("/candidates/me").status_code
    garbage = api.c.get("/candidates/me", headers={"Authorization": "Bearer khong-phai-token"}).status_code
    detail = f"không token {no_token}, token rác {garbage}"
    ok = no_token == 401 and garbage == 401
    if args.web:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            b = p.chromium.launch()
            page = b.new_page()
            page.goto(args.web + "/employer/jobs")
            page.wait_for_timeout(2500)
            ok = ok and page.url.rstrip("/").endswith("/login")
            detail += f"; /employer/jobs → {page.url.replace(args.web, '')}"
            b.close()
    case("TC05", ok, detail)

    # TC06
    cand = api.register("candidate", f"tc-cand-{stamp}@smartcareer.vn", "Ứng viên Kiểm thử")
    put = api.c.put("/candidates/me", headers=cand, json={"fullName": "Ứng viên Kiểm thử", "university": "Đại học Bách khoa", "major": "Công nghệ thông tin",
                                                           "careerGoal": "Backend", "preferredLocations": ["Hà Nội"], "years_exp": 1.5, "education_level": 3})
    got = api.c.get("/candidates/me", headers=cand).json()
    case("TC06", put.status_code == 200 and got.get("university") == "Đại học Bách khoa" and got.get("major") == "Công nghệ thông tin",
         f"PUT {put.status_code}; tải lại: university={got.get('university')!r}, major={got.get('major')!r}")

    # TC10
    job_id = pick_job_of(api, hr1)
    job = api.c.get(f"/jobs/{job_id}", headers=cand).json()
    required = job["required_skills"]
    before = api.c.post("/ai/match", headers=cand, json={"job_id": job_id, "model": "m3"}).json()["total_score"]
    put_skills = api.c.put("/candidates/me/skills", headers=cand, json={"skills": required})
    saved = api.c.get("/candidates/me/skills", headers=cand).json()
    names = {s["name"] if isinstance(s, dict) else s for s in saved.get("skills", saved.get("items", []))}
    after = api.c.post("/ai/match", headers=cand, json={"job_id": job_id, "model": "m3"}).json()["total_score"]
    case("TC10", put_skills.status_code == 200 and set(required) <= names and after > before, f"lưu {len(names)} kỹ năng; điểm khớp {before} → {after}")

    # TC11 + TC13
    new_job = {"title": f"tc-Kiểm thử Frontend {stamp}", "description": "Cần React và Docker.", "category": "Frontend Development", "level": "junior",
               "job_type": "full_time", "work_mode": "onsite", "location": "Hà Nội", "min_years_exp": 1, "responsibilities": ["Viết giao diện"],
               "required_skills": ["React"], "preferred_skills": ["Docker"]}
    created = api.c.post("/jobs", headers=hr1, json=new_job)
    cj = created.json()
    mine = [j["title"] for j in api.c.get("/jobs", headers=hr1, params={"mine": "true", "page_size": 100}).json()["items"]]
    case("TC11", created.status_code == 201 and cj["company"]["name"] and new_job["title"] in mine, f"{created.status_code}; công ty {cj['company']['name']}")
    new_id = int(cj["id"])
    upd = api.c.put(f"/jobs/{new_id}", headers=hr1, json={**new_job, "title": new_job["title"] + " (sửa)"})
    other = api.c.put(f"/jobs/{new_id}", headers=hr5, json={**new_job, "title": "chiếm quyền"})
    other_del = api.c.delete(f"/jobs/{new_id}", headers=hr5)

    # TC23: đủ luật trạng thái (dùng tin vừa tạo, hai ứng viên)
    c2 = api.register("candidate", f"tc-cand2-{stamp}@smartcareer.vn", "Ứng viên Hai")
    a1 = api.c.post("/applications", headers=cand, json={"job_id": new_id}).json()["id"]
    a2 = api.c.post("/applications", headers=c2, json={"job_id": new_id}).json()["id"]
    steps = [api.c.patch(f"/applications/{a1}/status", headers=hr1, json={"status": s}).status_code for s in ("screening", "interview", "offer", "hired")]
    after_final = api.c.patch(f"/applications/{a1}/status", headers=hr1, json={"status": "rejected"})
    history = api.c.get("/applications/me", headers=cand).json()["items"][0]["history"]
    api.c.patch(f"/applications/{a2}/status", headers=hr1, json={"status": "screening"})
    api.c.patch(f"/applications/{a2}/status", headers=hr1, json={"status": "interview"})
    reject = api.c.patch(f"/applications/{a2}/status", headers=hr1, json={"status": "rejected"})
    after_reject = api.c.patch(f"/applications/{a2}/status", headers=hr1, json={"status": "offer"})
    case("TC23", steps == [200, 200, 200, 200] and after_final.status_code == 409 and reject.status_code == 200 and after_reject.status_code == 409
         and [h["to_status"] for h in history] == ["applied", "screening", "interview", "offer", "hired"] and history[0]["from_status"] is None,
         f"4 bước {steps}; sau hired {after_final.status_code}; reject từ interview {reject.status_code}; sau rejected {after_reject.status_code}; {len(history)} dòng lịch sử")

    # TC13 (đóng tin sau khi đã dùng làm tin thử)
    closed = api.c.delete(f"/jobs/{new_id}", headers=hr1)
    listing = api.c.get("/jobs", headers=cand, params={"q": "tc-Kiểm thử", "page_size": 50}).json()["items"]
    case("TC13", upd.status_code == 200 and other.status_code == 403 and other_del.status_code == 403 and closed.status_code in (200, 204)
         and not any(j["title"].startswith("tc-Kiểm thử") and j.get("status", "open") == "open" for j in listing),
         f"sửa {upd.status_code}; công ty khác sửa {other.status_code}, đóng {other_del.status_code}; đóng tin {closed.status_code}")

    # TC07 (xoá hồ sơ của ứng viên hai, đã có đơn)
    deleted = api.c.delete("/candidates/me", headers=c2)
    relog = api.c.post("/auth/login", json={"email": f"tc-cand2-{stamp}@smartcareer.vn", "password": PASSWORD})
    case("TC07", deleted.status_code == 204 and relog.status_code in (401, 403), f"DELETE {deleted.status_code}; đăng nhập lại {relog.status_code}")

    # TC27
    f1 = api.c.get("/bi/funnel", headers=hr1).json()
    f5 = api.c.get("/bi/funnel", headers=hr5).json()
    fa = api.c.get("/bi/funnel", headers=admin).json()

    def total(payload: dict) -> int:
        return sum(r["applications"] for r in payload["stages"] if r["stage"] == "applied")

    t1, t5, ta = total(f1), total(f5), total(fa)
    case("TC27", t1 != t5 and ta > t1 + t5 and all(r["company_id"] == f1["stages"][0]["company_id"] for r in f1["stages"]),
         f"hồ sơ nộp: hr1={t1}, hr5={t5}, admin={ta}")

    # TC28
    import jwt

    def rls(headers: dict[str, str]):
        r = api.c.get("/bi/guest-token", headers=headers)
        if r.status_code != 200:
            return r.status_code, None
        return 200, jwt.decode(r.json()["token"], options={"verify_signature": False}).get("rls_rules")

    s1, r1 = rls(hr1)
    s5, r5 = rls(hr5)
    sa, ra = rls(admin)
    sc, _ = rls(cand)
    clause_ok = lambda r, n: bool(r) and all(x["clause"] == f"company_id = {n}" for x in r) and len(r) == 2  # noqa: E731
    case("TC28", (s1, s5, sa) == (200, 200, 200) and clause_ok(r1, 1) and clause_ok(r5, 5) and not ra and sc == 403,
         f"hr1 {r1}; hr5 {[x['clause'] for x in r5 or []]}; admin rls={ra}; ứng viên {sc}")

    # TC29
    alias = f"reakt{stamp % 1000}"
    cand_forbidden = api.c.get("/admin/skills", headers=cand).status_code
    add = api.c.post("/admin/skill-aliases", headers=admin, json={"alias": alias, "skill_name": "React"})
    hit = [s["name"] for s in api.c.post("/ai/extract-skills", headers=hr1, json={"text": f"thành thạo {alias}"}).json()["skills"]]
    dele = api.c.delete(f"/admin/skill-aliases/{alias}", headers=admin)
    miss = [s["name"] for s in api.c.post("/ai/extract-skills", headers=hr1, json={"text": f"thành thạo {alias}"}).json()["skills"]]
    case("TC29", cand_forbidden == 403 and add.status_code in (200, 201) and "React" in hit and dele.status_code in (200, 204) and "React" not in miss,
         f"ứng viên {cand_forbidden}; thêm {add.status_code}, nhận ra {hit}; xoá {dele.status_code}, sau đó {miss}")

    failed = [c for c, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} ca đạt")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
