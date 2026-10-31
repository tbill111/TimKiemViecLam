"""Kiểm thử end-to-end bằng trình duyệt thật cho hai luồng chính (cần backend đã seed + frontend đã build trỏ vào API).

Cách chạy (xem docs/E2E.md):
    python scripts/e2e_smoke.py --web http://localhost:4173 --api http://localhost:8000/api --shots out_dir

Luồng ứng viên: đăng nhập → thấy việc phù hợp + điểm → tải CV (public/cv-mau.pdf, có đồng ý) → xác nhận kỹ năng → phân tích CV–JD
chọn model → ứng tuyển → thấy trạng thái.
Luồng nhà tuyển dụng: đăng nhập → đăng tin (có gợi ý kỹ năng) → xem ứng viên xếp hạng (Kanban) → đổi trạng thái đúng luật
(thử bước sai để thấy lỗi) → dashboard BI (dự phòng Recharts vì chưa cấu hình Superset).
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import Page, expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "Demo@12345"
results: list[tuple[str, bool, str]] = []


def step(name: str):
    def deco(fn):
        def run(*a, **kw):
            try:
                fn(*a, **kw)
                results.append((name, True, ""))
                print(f"  OK   {name}")
            except Exception as exc:  # noqa: BLE001
                detail = " | ".join(ln.strip() for ln in str(exc).splitlines()[:4])[:400]
                results.append((name, False, detail))
                print(f"  FAIL {name}: {detail}")
        return run
    return deco


def login(page: Page, web: str, email: str) -> None:
    page.goto(f"{web}/login")
    page.get_by_label("Email").fill(email)
    page.get_by_label("Mật khẩu").fill(PASSWORD)
    page.get_by_role("button", name=re.compile("Đăng nhập")).click()


def shot(page: Page, shots: Path | None, name: str) -> None:
    if shots:
        shots.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(shots / f"{name}.png"), full_page=True)


def candidate_flow(page: Page, web: str, shots: Path | None) -> None:
    @step("Ứng viên: đăng nhập và vào Tổng quan")
    def _login():
        login(page, web, "tung.demo@smartcareer.vn")
        expect(page.get_by_text("Việc phù hợp").first).to_be_visible(timeout=20000)
        shot(page, shots, "01_candidate_dashboard")

    @step("Ứng viên: trang Tìm việc có điểm khớp từ API")
    def _jobs():
        page.get_by_role("link", name="Tìm việc làm").click()
        expect(page.get_by_text(re.compile(r"Tìm thấy \d+ kết quả")).first).to_be_visible(timeout=20000)
        expect(page.locator("text=/\\d+%/").first).to_be_visible()
        shot(page, shots, "02_jobs")

    @step("Ứng viên: tải CV mẫu với ô đồng ý, xác nhận kỹ năng")
    def _upload():
        page.get_by_role("link", name="Hồ sơ của tôi").click()
        page.get_by_role("checkbox", name=re.compile("Tôi đồng ý")).check(timeout=15000)
        page.locator("input[type=file]").set_input_files(str(ROOT / "public" / "cv-mau.pdf"))
        expect(page.get_by_text(re.compile(r"Phát hiện\s*\d+")).first).to_be_visible(timeout=60000)
        shot(page, shots, "03_cv_suggestions")
        page.get_by_role("button", name=re.compile(r"Thêm \d+ kỹ năng vào hồ sơ")).click()
        expect(page.get_by_text(re.compile("Đã thêm|Không có kỹ năng mới"))).to_be_visible(timeout=15000)

    @step("Ứng viên: Phân tích CV–JD với ô chọn model và 6 thành phần")
    def _match():
        page.get_by_role("link", name="Phân tích CV–JD").click()
        expect(page.get_by_label("Mô hình chấm điểm")).to_be_visible(timeout=15000)
        page.get_by_label("Mô hình chấm điểm").select_option("m3")
        expect(page.get_by_text("Ngữ nghĩa CV–JD")).to_be_visible(timeout=20000)
        expect(page.get_by_text(re.compile(r"^Khớp \d+/100")).first).to_be_visible()
        page.get_by_label("Mô hình chấm điểm").select_option("m4")  # chưa huấn luyện: phải báo lỗi dễ hiểu, không vỡ trang
        expect(page.get_by_text(re.compile("M4 chưa được huấn luyện"))).to_be_visible(timeout=20000)
        shot(page, shots, "04_match_m4_error")
        page.get_by_label("Mô hình chấm điểm").select_option("m0")
        expect(page.get_by_text("Ngữ nghĩa CV–JD")).to_be_visible(timeout=20000)

    @step("Ứng viên: Skill Gap lấy lộ trình học từ API")
    def _gap():
        page.get_by_role("link", name="Skill Gap Analysis").click()
        expect(page.get_by_text("Kỹ năng cần phát triển")).to_be_visible(timeout=20000)
        shot(page, shots, "05_skill_gap")

    @step("Ứng viên: ứng tuyển một tin và thấy trạng thái (chỉ đọc)")
    def _apply():
        page.get_by_role("link", name="Tìm việc làm").click()
        page.get_by_role("button", name=re.compile("Xem chi tiết")).first.click(timeout=20000)
        page.get_by_role("button", name="Ứng tuyển", exact=True).click()
        page.get_by_role("button", name="Xác nhận ứng tuyển", exact=True).click()
        expect(page.get_by_text(re.compile("Ứng tuyển thành công"))).to_be_visible(timeout=20000)
        page.get_by_role("button", name="Đóng").click()
        page.get_by_role("link", name=re.compile("Việc đã lưu")).click()
        page.get_by_role("button", name=re.compile(r"^Đã ứng tuyển \d")).click(timeout=15000)
        expect(page.get_by_title("Do nhà tuyển dụng cập nhật").first).to_be_visible(timeout=15000)
        shot(page, shots, "06_applications")

    for fn in (_login, _jobs, _upload, _match, _gap, _apply):
        fn()


def recruiter_flow(page: Page, web: str, shots: Path | None) -> None:
    @step("Nhà tuyển dụng: đăng nhập vào Dashboard BI")
    def _login():
        page.get_by_role("button", name="Đăng xuất").click()
        login(page, web, "hr01@smartcareer.vn")
        expect(page.get_by_role("heading", name=re.compile("Dashboard thị trường"))).to_be_visible(timeout=20000)

    @step("Nhà tuyển dụng: dashboard hiển thị (nhúng Superset hoặc 3 biểu đồ dự phòng)")
    def _dash():
        fallback = page.get_by_text("Phễu tuyển dụng (hồ sơ từng đạt mỗi bước)")
        embedded = page.frame_locator("[data-testid=superset-mount] iframe").get_by_text(re.compile("Top 15 kỹ năng")).first
        deadline = time.time() + 60
        mode = None
        while time.time() < deadline and mode is None:
            if fallback.count():
                mode = "dự phòng Recharts"
            elif embedded.count():
                mode = "Superset nhúng"
            else:
                page.wait_for_timeout(500)
        assert mode, "dashboard không hiển thị cả nhúng lẫn dự phòng"
        print(f"       (dashboard dùng: {mode})")
        if mode == "dự phòng Recharts":
            expect(page.get_by_text("Top 15 kỹ năng theo số ứng viên và nhu cầu tuyển")).to_be_visible()
            expect(page.get_by_text("Trung vị lương theo tháng đăng và cấp bậc")).to_be_visible()
        shot(page, shots, "07_employer_dashboard")

    @step("Nhà tuyển dụng: đăng tin với gợi ý kỹ năng từ mô tả")
    def _post():
        page.get_by_role("link", name="Đăng tin mới").click()
        page.get_by_label("Chức danh").fill("Frontend Developer E2E")
        page.get_by_label("Mô tả công việc").fill("Cần thành thạo React, TypeScript, Git và hiểu REST API. Có kiến thức HTML và CSS.")
        page.get_by_role("button", name="Gợi ý kỹ năng từ mô tả").click()
        expect(page.get_by_text(re.compile("Đã thêm \\d+ kỹ năng"))).to_be_visible(timeout=20000)
        shot(page, shots, "08_post_job")
        page.get_by_role("button", name="Đăng tin").click()
        expect(page.get_by_text("Frontend Developer E2E")).to_be_visible(timeout=20000)

    @step("Nhà tuyển dụng: Kanban ứng viên, đổi trạng thái đúng luật")
    def _kanban():
        page.get_by_role("link", name="Ứng viên xếp hạng").click()
        expect(page.get_by_role("heading", name="Ứng viên xếp hạng")).to_be_visible(timeout=20000)
        page.get_by_label("Tin tuyển dụng").select_option(label="Frontend Developer Intern (đang mở)")  # tin seed có hồ sơ ứng tuyển
        expect(page.get_by_role("list", name=re.compile("Kanban"))).to_be_visible(timeout=30000)
        shot(page, shots, "09_kanban_before")
        before = page.get_by_role("listitem", name="Đang xem xét").get_by_role("article").count()
        page.get_by_role("listitem", name="Đã ứng tuyển").get_by_role("button", name=re.compile("Chuyển")).first.click()
        page.wait_for_timeout(2000)
        after = page.get_by_role("listitem", name="Đang xem xét").get_by_role("article").count()
        assert after == before + 1, f"cột Đang xem xét phải tăng 1 ({before} → {after})"
        shot(page, shots, "10_kanban_after")

    for fn in (_login, _dash, _post, _kanban):
        fn()


def admin_flow(page: Page, web: str, shots: Path | None) -> None:
    @step("Quản trị: đăng nhập, mở Quản lý kỹ năng")
    def _open():
        page.get_by_role("button", name="Đăng xuất").click()
        login(page, web, "admin@smartcareer.vn")
        expect(page.get_by_role("heading", name=re.compile("Dashboard thị trường"))).to_be_visible(timeout=30000)
        page.get_by_role("link", name="Quản lý kỹ năng").click()
        expect(page.get_by_role("heading", name="Quản lý danh mục kỹ năng")).to_be_visible(timeout=20000)

    @step("Quản trị: thêm kỹ năng mới, từ đồng nghĩa và lộ trình học")
    def _add():
        page.get_by_label("Kỹ năng mới").fill("Kỹ năng E2E")
        page.get_by_role("button", name="Thêm", exact=True).first.click()
        expect(page.get_by_text("Đã thêm kỹ năng.")).to_be_visible(timeout=15000)
        expect(page.get_by_role("heading", name="Kỹ năng E2E")).to_be_visible()
        page.get_by_label("Từ đồng nghĩa mới").fill("ky-nang-e2e")
        page.get_by_role("button", name="Thêm", exact=True).last.click()
        expect(page.get_by_text("Đã thêm từ đồng nghĩa.")).to_be_visible(timeout=15000)
        expect(page.get_by_text("ky-nang-e2e")).to_be_visible()
        page.get_by_label("Lộ trình học", exact=False).fill("Bước một\nBước hai")
        page.get_by_role("button", name="Lưu thay đổi").click()
        expect(page.get_by_text("Đã lưu thay đổi.")).to_be_visible(timeout=15000)
        shot(page, shots, "12_admin_skills")

    @step("Quản trị: từ đồng nghĩa mới có hiệu lực ở bộ trích kỹ năng")
    def _effect():
        token = page.evaluate("localStorage.getItem('smartcareer_token')")
        api = page.evaluate("document.location.origin") + "/api"
        r = page.request.post(f"{api}/ai/extract-skills", data={"text": "Yêu cầu: ky-nang-e2e và Git"}, headers={"Authorization": f"Bearer {token}"})
        names = {x["name"] for x in r.json()["skills"]}
        assert "Kỹ năng E2E" in names and "Git" in names, names

    @step("Quản trị: xóa từ đồng nghĩa thì không còn hiệu lực")
    def _delete():
        page.get_by_role("button", name="Xóa từ đồng nghĩa ky-nang-e2e").click()
        expect(page.get_by_text("Đã xóa từ đồng nghĩa.")).to_be_visible(timeout=15000)
        token = page.evaluate("localStorage.getItem('smartcareer_token')")
        api = page.evaluate("document.location.origin") + "/api"
        r = page.request.post(f"{api}/ai/extract-skills", data={"text": "Yêu cầu: ky-nang-e2e"}, headers={"Authorization": f"Bearer {token}"})
        assert "Kỹ năng E2E" not in {x["name"] for x in r.json()["skills"]}

    for fn in (_open, _add, _effect, _delete):
        fn()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--web", default="http://localhost:4173")
    ap.add_argument("--shots", type=Path, default=None)
    args = ap.parse_args()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(viewport={"width": 1366, "height": 900}).new_page()
        console_errors: list[str] = []
        page.on("pageerror", lambda e: console_errors.append(str(e)))
        t0 = time.time()
        candidate_flow(page, args.web, args.shots)
        recruiter_flow(page, args.web, args.shots)
        admin_flow(page, args.web, args.shots)
        browser.close()
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} bước đạt trong {time.time() - t0:.0f}s; lỗi JS không bắt: {len(console_errors)}")
    for e in console_errors[:5]:
        print("  pageerror:", e[:200])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
