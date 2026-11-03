"""Kiểm thử trình duyệt tự động cho giao diện (Playwright).

Hai chế độ:
  online : cần stack đang chạy (API + giao diện). Dữ liệu seed sạch trước mỗi lần chạy
           (`python -m seed.load_seed --reset`) vì ứng viên demo chỉ ứng tuyển được một lần mỗi tin.
      python scripts/e2e_ui.py --web http://localhost:8080 --api http://localhost:8000/api
  offline: giao diện build với VITE_OFFLINE_DEMO=true, không cần backend; kiểm 0 lời gọi API.
      python scripts/e2e_ui.py --offline --web http://localhost:4173

Thoát với mã 1 nếu có bước lỗi. Cần: pip install playwright httpx && playwright install chromium
"""
from __future__ import annotations

import argparse
import re
import sys

import httpx
from playwright.sync_api import Page, sync_playwright

PASSWORD = "Demo@12345"
results: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    results.append((name, condition, detail))
    print(f"  {'OK  ' if condition else 'FAIL'} {name}{(' – ' + detail) if detail and not condition else ''}")


def login(page: Page, web: str, email: str, password: str) -> None:
    page.goto(web + "/login")
    page.fill("input[type=email]", email)
    page.fill("input[type=password]", password)
    page.get_by_role("button", name="Đăng nhập", exact=True).click()
    page.wait_for_timeout(2500)


def api_token(api: str, email: str) -> dict[str, str]:
    response = httpx.post(api + "/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def run_online(browser, web: str, api: str) -> None:
    print("== Online")
    errors: list[str] = []
    bad: list[tuple[str, int]] = []

    def watch(page: Page) -> None:
        page.on("pageerror", lambda e: errors.append(str(e)[:120]))
        # guest-token 503 (chưa cấu hình Superset) và 409 khi cố ý nộp trùng là lỗi mong đợi
        page.on("response", lambda r: bad.append((r.url.split("/api")[-1], r.status)) if "/api/" in r.url and r.status >= 400 and "guest-token" not in r.url and not (r.url.endswith("/applications") and r.status == 409) else None)

    page = browser.new_context().new_page()
    watch(page)
    login(page, web, "thanhtung.demo@smartcareer.vn", PASSWORD)
    check("Ứng viên đăng nhập vào Tổng quan", page.url.rstrip("/") == web.rstrip("/"))

    page.goto(web + "/jobs")
    page.wait_for_timeout(3500)
    match = re.search(r"(\d+)\s*kết quả", page.inner_text("body"))
    check("Tìm việc tải đủ tin (> 100)", bool(match) and int(match.group(1)) > 100, match.group(0) if match else "không thấy số kết quả")

    cards = page.locator(".card-hover h3, .card-hover h2")
    title = ""
    for index in range(60):
        cards.nth(index).click()
        page.wait_for_timeout(300)
        dialog = page.get_by_role("dialog")
        if dialog.get_by_role("button", name=re.compile("^Ứng tuyển$")).count():
            title = dialog.locator("h2").first.inner_text()
            break
        page.keyboard.press("Escape")
    check("Modal tin có nút 'Ứng tuyển' (không còn 'Demo')", bool(title))
    dialog = page.get_by_role("dialog")
    dialog.get_by_role("button", name=re.compile("^Ứng tuyển$")).first.click()
    page.get_by_role("button", name=re.compile("^Xác nhận")).first.click()
    page.wait_for_timeout(2000)
    check("Ứng tuyển thành công", page.get_by_text(re.compile("Ứng tuyển thành công")).count() > 0)

    # Nộp trùng từ nơi khác rồi xác nhận trên giao diện: phải báo lỗi, không báo thành công
    page.keyboard.press("Escape")
    for index in range(1, 80):
        cards.nth(index).click()
        page.wait_for_timeout(300)
        dialog = page.get_by_role("dialog")
        if dialog.get_by_role("button", name=re.compile("^Ứng tuyển$")).count():
            break
        page.keyboard.press("Escape")
    headers = api_token(api, "thanhtung.demo@smartcareer.vn")
    open_title = page.get_by_role("dialog").locator("h2").first.inner_text()
    all_jobs = [job for number in (1, 2) for job in httpx.get(api + "/jobs", params={"page_size": 100, "page": number}, headers=headers).json()["items"]]
    job_id = next(job["id"] for job in all_jobs if job["title"] == open_title)
    page.get_by_role("dialog").get_by_role("button", name=re.compile("^Ứng tuyển$")).first.click()
    httpx.post(api + "/applications", json={"job_id": int(job_id)}, headers=headers)
    page.get_by_role("button", name=re.compile("^Xác nhận")).first.click()
    page.wait_for_timeout(2000)
    check("Nộp trùng hiện lỗi, không báo thành công", page.get_by_role("alert").count() > 0 and page.get_by_text(re.compile("Ứng tuyển thành công")).count() == 0)

    # Trạng thái backend 'interview' / 'offer' phải hiển thị đúng ở phía ứng viên
    apps = httpx.get(api + "/applications/me", headers=headers).json()["items"]
    target = apps[0]
    owner = None
    for number in range(1, 31):
        candidate_headers = api_token(api, f"hr{number}@smartcareer.vn")
        if httpx.get(api + f"/jobs/{target['job_id']}/applications", headers=candidate_headers).status_code == 200:
            owner = candidate_headers
            break
    assert owner is not None
    for status in ("screening", "interview", "offer"):
        httpx.patch(api + f"/applications/{target['id']}/status", headers=owner, json={"status": status})
    page.goto(web + "/applications")
    page.wait_for_timeout(2500)
    page.get_by_role("button", name=re.compile("Đang theo dõi")).first.click()
    page.wait_for_timeout(600)
    check("Đơn ở bước 'offer' hiển thị 'Đề nghị nhận việc' trong Đang theo dõi", "Đề nghị nhận việc" in page.inner_text("body"))

    page.goto(web + "/skill-gap")
    page.wait_for_timeout(3000)
    check("Skill Gap có lộ trình học từ API", page.get_by_label(re.compile("Xem lộ trình học")).count() > 0)
    check("Ứng viên không gọi lỗi 4xx/5xx", not bad, str(bad[:3]))

    recruiter = browser.new_context().new_page()
    recruiter_bad: list[tuple[str, int]] = []
    recruiter.on("response", lambda r: recruiter_bad.append((r.url.split("/api")[-1], r.status)) if "/api/" in r.url and r.status >= 400 and "guest-token" not in r.url else None)
    login(recruiter, web, "hr1@smartcareer.vn", PASSWORD)
    check("Nhà tuyển dụng vào /employer/candidates", "/employer/candidates" in recruiter.url)
    recruiter.goto(web + "/employer/dashboard")
    recruiter.wait_for_timeout(4000)
    body = recruiter.inner_text("body")
    check("Dashboard có 3 biểu đồ dự phòng + phễu, không lộ mã lỗi", recruiter.locator(".recharts-wrapper").count() >= 3 and "superset_not_configured" not in body and "Phễu tuyển dụng" in body)
    check("Nhà tuyển dụng không còn gọi API ứng viên (403)", not recruiter_bad, str(recruiter_bad[:3]))
    check("Nhà tuyển dụng không thấy nút Đặt lại demo", recruiter.get_by_text("Đặt lại dữ liệu demo").count() == 0)
    recruiter.goto(web + "/employer/jobs/new")
    recruiter.wait_for_timeout(1200)
    check("Form đăng tin có ô gợi ý kỹ năng", recruiter.get_by_role("button", name=re.compile("Gợi ý kỹ năng")).count() == 1)

    admin = browser.new_context().new_page()
    login(admin, web, "admin@smartcareer.vn", PASSWORD)
    check("Admin vào Quản lý kỹ năng", "/admin/skills" in admin.url)
    admin.goto(web + "/employer/candidates")
    admin.wait_for_timeout(800)
    check("Admin bị chặn ở trang nhà tuyển dụng", "không có quyền" in admin.inner_text("body"))
    check("Không có lỗi JS", not errors, str(errors[:2]))


def run_offline(browser, web: str) -> None:
    print("== Offline (không backend)")
    requests: list[str] = []
    for email, paths in (
        ("sv@demo.vn", ["/", "/jobs", "/match", "/skill-gap", "/applications", "/profile"]),
        ("hr1@demo.vn", ["/employer/jobs", "/employer/candidates", "/employer/kanban", "/employer/dashboard", "/employer/jobs/new"]),
        ("admin@demo.vn", ["/admin/skills"]),
    ):
        page = browser.new_context().new_page()
        page.on("request", lambda r: requests.append(r.url) if "/api" in r.url else None)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:100]))
        login(page, web, email, "12345678")
        for path in paths:
            page.goto(web + path)
            page.wait_for_timeout(800)
            check(f"{email} mở {path}", len(page.inner_text("body")) > 300 and "không có quyền" not in page.inner_text("body"))
        check(f"{email}: không lỗi JS", not errors, str(errors[:2]))
        if email.startswith("hr1"):
            page.goto(web + "/employer/kanban")
            page.wait_for_timeout(1000)
            cards = page.locator("article")
            check("Kanban demo có thẻ ứng viên", cards.count() > 0)
            before = page.locator("section").nth(1).locator("article").count()
            first_move = page.get_by_role("button", name=re.compile("→ Đang xem xét")).first
            if first_move.count():
                first_move.click()
                page.wait_for_timeout(500)
                check("Kanban demo chuyển được trạng thái", page.locator("section").nth(1).locator("article").count() == before + 1)
            page.goto(web + "/employer/dashboard")
            page.wait_for_timeout(800)
            check("Dashboard demo có biểu đồ", page.locator(".recharts-wrapper").count() >= 2)
    check("Demo không gọi API nào", not requests, str(requests[:3]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--web", default="http://localhost:8080")
    parser.add_argument("--api", default="http://localhost:8000/api")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        if args.offline:
            run_offline(browser, args.web)
        else:
            run_online(browser, args.web, args.api)
        browser.close()
    failed = [name for name, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} bước đạt")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
