# Chạy thử end-to-end, đo hiệu năng và việc cần làm trên máy có Docker

## 1. E2E trình duyệt (Playwright, đã chạy được trên máy dựng)

Cài một lần: `pip install playwright && playwright install chromium`.

```bash
# 1) backend với DB đã seed (SQLite cho nhanh) và CORS cho cổng của preview
cd backend
export EMBEDDER=hash BCRYPT_ROUNDS=4 DATABASE_URL=sqlite:///./e2e.db CORS_ORIGINS=http://localhost:4173
python -m seed.load_seed --reset
uvicorn app.main:app --port 8000 &

# 2) frontend build trỏ vào API rồi preview
cd .. && VITE_API_URL=http://localhost:8000/api npx vite build --outDir /tmp/e2e-dist
npx vite preview --outDir /tmp/e2e-dist --port 4173 &

# 3) chạy kịch bản (nạp lại DB bằng --reset trước mỗi lần chạy vì kịch bản ứng tuyển và đăng tin)
python scripts/e2e_smoke.py --web http://localhost:4173 --shots /tmp/shots
```

Kịch bản gồm 10 bước: ứng viên đăng nhập → tìm việc có điểm khớp → tải `public/cv-mau.pdf` có đồng ý → xác nhận kỹ năng → Phân tích CV–JD (chọn M3, M4 báo chưa huấn luyện, đổi lại M0) → Skill Gap → ứng tuyển → nhà tuyển dụng đăng nhập → dashboard 3 biểu đồ → đăng tin có gợi ý kỹ năng → Kanban chuyển trạng thái.

Chế độ demo: build với `VITE_OFFLINE_DEMO=true`, preview cổng 4174 rồi `python scripts/e2e_offline.py`.

## 2. Việc cần làm trên máy có Docker (chưa kiểm chứng được ở máy dựng)

1. `cp .env.example .env && docker compose up --build`; kiểm tra 4 dịch vụ lên, đăng nhập ở http://localhost:8080 bằng tài khoản trong README.
2. Xác nhận log `api` cho thấy `alembic upgrade head` tạo 4 view (`\dv` trong `psql`) và seed xong.
3. Chạy lại view trên PostgreSQL thật: so `SELECT * FROM v_funnel_stages` với `GET /api/bi/funnel` (phải khớp).
4. Dựng và nhúng dashboard Superset theo `bi/README.md`; điền `SUPERSET_DASHBOARD_ID`, `SUPERSET_RLS_DATASET_IDS` rồi đăng nhập HR để thấy dashboard nhúng; thử HR hai công ty để xác nhận RLS.
5. Trong image `api` (có model thật): chạy `EMBEDDER=st python -m pytest tests/api/test_performance.py -s` và ghi lại thời gian; chạy ba notebook với dữ liệu nhãn thật. Chỉ báo cáo số liệu khi notebook in `Embedder: st:...`.
6. Thay mật khẩu/`JWT_SECRET`/`SUPERSET_*` trong `.env` nếu triển khai ngoài máy cá nhân.
