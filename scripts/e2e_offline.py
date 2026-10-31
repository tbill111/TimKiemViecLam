"""Kiểm tra chế độ demo (VITE_OFFLINE_DEMO=true): chạy trọn các trang mà KHÔNG gọi API nào.

    VITE_OFFLINE_DEMO=true npx vite build --outDir /tmp/off-dist && npx vite preview --outDir /tmp/off-dist --port 4174
    python scripts/e2e_offline.py --web http://localhost:4174
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--web", default="http://localhost:4174")
    args = ap.parse_args()
    api_calls: list[str] = []
    errors: list[str] = []
    ok = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(viewport={"width": 1366, "height": 900}).new_page()
        page.on("request", lambda r: api_calls.append(r.url) if "/api/" in r.url else None)
        page.on("pageerror", lambda e: errors.append(str(e)))

        def check(name: str, fn) -> None:
            nonlocal ok
            try:
                fn()
                ok += 1
                print(f"  OK   {name}")
            except Exception as exc:  # noqa: BLE001
                print(f"  FAIL {name}: {' | '.join(str(exc).splitlines()[:3])[:300]}")

        page.goto(args.web + "/")
        check("Vào thẳng Tổng quan, không cần đăng nhập", lambda: expect(page.get_by_text("Việc phù hợp").first).to_be_visible(timeout=15000))
        check("Nhập /login chuyển về trang chủ", lambda: (page.goto(args.web + "/login"), expect(page).to_have_url(re.compile(r"/$"))))

        def jobs():
            page.get_by_role("link", name="Tìm việc làm").click()
            expect(page.get_by_text(re.compile(r"Tìm thấy 12 kết quả"))).to_be_visible(timeout=15000)

        check("Tìm việc: 12 tin mẫu", jobs)

        def apply():
            page.get_by_role("button", name=re.compile("Xem chi tiết")).first.click()
            expect(page.get_by_role("button", name="Ứng tuyển Demo")).to_be_visible()
            page.get_by_role("button", name="Ứng tuyển Demo").click()
            page.get_by_role("button", name="Xác nhận ứng tuyển", exact=True).click()
            expect(page.get_by_text(re.compile("Ứng tuyển thành công"))).to_be_visible()
            page.get_by_role("button", name="Đóng").click()

        check("Ứng tuyển demo", apply)

        def tracking():
            page.get_by_role("link", name=re.compile("Việc đã lưu")).click()
            page.get_by_role("button", name=re.compile(r"^Đã ứng tuyển \d")).click()
            sel = page.get_by_role("combobox").first
            expect(sel).to_be_visible()
            sel.select_option("Phỏng vấn")  # chế độ demo cho phép tự đổi trạng thái
            expect(sel).to_have_value("Phỏng vấn")
            options = sel.locator("option").all_inner_texts()
            assert options == ["Đã ứng tuyển", "Đang xem xét", "Phỏng vấn", "Đề nghị", "Đã tuyển", "Từ chối"], options

        check("Trạng thái 6 giá trị, tự đổi được", tracking)

        def match():
            page.get_by_role("link", name="Phân tích CV–JD").click()
            expect(page.get_by_text("Mô phỏng ghép nối đa tiêu chí")).to_be_visible(timeout=15000)
            assert page.get_by_label("Mô hình chấm điểm").count() == 0

        check("Phân tích CV–JD (M0, không có ô chọn model)", match)

        def gap():
            page.get_by_role("link", name="Skill Gap Analysis").click()
            expect(page.get_by_text("Kỹ năng cần phát triển")).to_be_visible(timeout=15000)

        check("Skill Gap", gap)

        def profile():
            page.get_by_role("link", name="Hồ sơ của tôi").click()
            expect(page.get_by_text("Nhập kỹ năng từ CV")).to_be_visible(timeout=15000)
            assert page.get_by_role("checkbox", name=re.compile("Tôi đồng ý")).count() == 0  # chế độ demo đọc CV ngay trên trình duyệt

        check("Hồ sơ + nhập CV trên trình duyệt", profile)

        def employer():
            page.get_by_role("link", name="Cổng nhà tuyển dụng").click()
            expect(page.get_by_role("heading", name="Cổng nhà tuyển dụng")).to_be_visible(timeout=15000)
            expect(page.get_by_text("Hồ sơ của bạn").first).to_be_visible()

        check("Cổng nhà tuyển dụng mô phỏng", employer)

        for path, text in (("/etl", "Dữ liệu"), ("/dfd", "Luồng"), ("/about", "SmartCareer")):
            check(f"Trang {path}", lambda path=path, text=text: (page.goto(args.web + path), expect(page.get_by_text(text).first).to_be_visible(timeout=15000)))
        browser.close()
    print(f"\n{ok} bước đạt; lời gọi API: {len(api_calls)}; lỗi JS: {len(errors)}")
    for e in errors[:3]:
        print("  pageerror:", e[:200])
    return 0 if not api_calls and not errors and ok == 12 else 1


if __name__ == "__main__":
    sys.exit(main())
