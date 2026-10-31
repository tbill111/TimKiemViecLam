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
python scripts/e2e_smoke.py --web http://localhost:4173 --api http://localhost:8000/api --shots /tmp/shots
```

Kịch bản gồm 14 bước (10 bước dưới đây + 4 bước quản trị kỹ năng): ứng viên đăng nhập → tìm việc có điểm khớp → tải `public/cv-mau.pdf` có đồng ý → xác nhận kỹ năng → Phân tích CV–JD (chọn M3, M4 báo chưa huấn luyện, đổi lại M0) → Skill Gap → ứng tuyển → nhà tuyển dụng đăng nhập → dashboard 3 biểu đồ → đăng tin có gợi ý kỹ năng → Kanban chuyển trạng thái.

Chế độ demo: build với `VITE_OFFLINE_DEMO=true`, preview cổng 4174 rồi `python scripts/e2e_offline.py`.

## 2. Chạy cả stack Docker (đã thực hiện trên máy dựng, kết quả 14/14)

```bash
cp .env.example .env                       # WITH_ST=1 để có model embedding thật (image ~1 GB); SUPERSET_PORT nếu 8088 bị chiếm
docker compose up -d --build               # db, api (tự migrate + seed), superset, web
python bi/superset/bootstrap.py --url http://localhost:8088 --write-env .env   # dựng dashboard + bật nhúng
docker compose up -d api                   # nạp UUID dashboard và id dataset RLS vào API
python scripts/check_bi_views.py           # đối chiếu 4 view PostgreSQL với /api/bi/* (phải "TẤT CẢ ĐẠT")
docker compose exec api python -m seed.load_seed --reset    # nạp dữ liệu sạch trước mỗi lần chạy E2E
python scripts/e2e_smoke.py --web http://localhost:8080 --shots out/   # 14 bước: ứng viên, nhà tuyển dụng, quản trị
# Chạy `docker compose exec api python -m seed.load_seed --reset` trước mỗi lần E2E (ứng viên demo chỉ ứng tuyển được một lần).
```

Kết quả đo được (PostgreSQL 16 + model `paraphrase-multilingual-MiniLM-L12-v2`, qua HTTP): chấm 1 cặp 38 ms, 150 tin 38 ms, 500 tin 70–77 ms.

Chạy bộ test trong container với model thật: `docker compose exec api pip install -r requirements-dev.txt` rồi
`docker compose exec -e EMBEDDER=st api python -m pytest -q --ignore tests/ai/test_notebooks_smoke.py --deselect tests/api/test_migrations_sql.py::test_erd_dbml_is_current_and_lists_15_tables_in_five_groups`
(hai test cần file ngoài image nên loại ra).

## 2b. Chạy 3 notebook đánh giá trong container (model thật)

`scripts/run_notebooks.py` có sẵn lệnh `docker run` ở đầu file. Kết quả vào `docs/report/tables/` và `models_store/m4.joblib` (phiên bản `m4-ai-labels`); nhãn đọc từ `backend/seed/labels/` (nguồn: `NGUON_NHAN.md`).
Lưu ý: `docker compose up --build web` cũng build lại `api`; để `WITH_ST=1` trong `.env` kẻo image mất model thật.

## 3. Việc còn lại (cần dữ liệu hoặc người)

1. Nhãn tay: 50 CV (`labels_cv_skills.csv`) và 300 cặp (hai file) → chạy 3 notebook trong container (`EMBEDDER=st`), huấn luyện M4, quyết định `UPDATE_M3`.
2. Thay mật khẩu/`JWT_SECRET`/`SUPERSET_*` trong `.env` nếu triển khai ngoài máy cá nhân (API cảnh báo khi dùng khoá mặc định).
3. Biểu đồ 5, 7 và Native Filters của Superset thêm bằng giao diện nếu muốn đủ bảng 8 biểu đồ; xuất `dashboard_export.zip` và chụp ảnh.
