# SmartCareer – Hệ thống Tìm việc Thông minh

SmartCareer là prototype tìm việc tích hợp API FastAPI, PostgreSQL, AI matching, BI và frontend React. Dữ liệu công ty, tin việc, hồ sơ và lịch sử ứng tuyển trong bộ seed là dữ liệu mô phỏng; không thu thập dữ liệu từ TopCV/LinkedIn.

## Chạy toàn hệ thống bằng Docker

Yêu cầu Docker Desktop với Docker Compose v2. Tạo `.env` từ file mẫu, thay secret nếu dùng ngoài máy cá nhân, sau đó chạy:

```powershell
Copy-Item .env.example .env
docker compose up -d --build
docker compose exec api python -m seed.load_seed --reset
```

Image API chạy Python 3.11, cài CPU PyTorch, tải trước model `paraphrase-multilingual-MiniLM-L12-v2`, đặt `HF_HUB_OFFLINE=1`, nâng migration rồi chạy API.

| Dịch vụ | URL | Ghi chú |
|---|---|---|
| Frontend Nginx | http://localhost:8080 | SPA fallback; `/api/` proxy tới FastAPI |
| FastAPI Swagger | http://localhost:8000/docs | Endpoint `/api/*` |
| Superset | http://localhost:8088 | Host port đổi bằng `SUPERSET_PORT` |
| PostgreSQL | localhost:5432 | Postgres 16, volume `postgres_data` |

Demo credentials dùng riêng cho dữ liệu seed: mật khẩu `Demo@12345`; tài khoản admin `admin@smartcareer.vn`, recruiter `hr1@smartcareer.vn` … `hr30@smartcareer.vn`, ứng viên demo `thanhtung.demo@smartcareer.vn`.

Để tắt model thật khi phát triển, đặt `EMBEDDER=hash`; kết quả hashing chỉ dùng kiểm tra luồng, không dùng báo cáo chất lượng ngữ nghĩa. Superset guest token chỉ được cấp cho recruiter khi đã cấu hình `SUPERSET_DASHBOARD_ID`, `SUPERSET_FUNNEL_DATASET_ID`, `SUPERSET_FUNNEL_STAGES_DATASET_ID`; nếu thiếu ID, API trả `503 superset_not_configured`.

## Backend

Migrations chạy tự động khi container API khởi động. Seed loader dùng một giao dịch cùng PostgreSQL advisory lock; `--reset` xóa dữ liệu seed và tạo lại 4 view BI. Các lệnh chạy trong container:

```bash
docker compose exec api alembic upgrade head
docker compose exec api python -m seed.load_seed --reset
docker compose exec api python -m pytest /app/backend/tests -q
```

Kiểm tra đối chiếu SQL view với `/api/bi/*` và lấy guest token sau khi cấu hình Superset:

```bash
python scripts/check_bi_views.py
```

Test API dùng cơ sở dữ liệu PostgreSQL riêng. Đặt `TEST_DATABASE_URL` rồi chạy `python -m pytest backend/tests`; nhóm test API sẽ bỏ qua khi không có URL test để tránh ghi nhầm vào DB dev.

## Frontend

```bash
npm ci
npm run dev
npm run build
npm run lint
```

`VITE_OFFLINE_DEMO=true` giữ chế độ demo frontend không gọi API. Tích hợp online cần frontend dùng API adapter/token của nhánh giao diện tương ứng.

## API chính

- Auth: `/api/auth/register`, `/api/auth/login`, `/api/auth/me`
- Hồ sơ/CV: `/api/candidates/me`, `/api/candidates/me/skills`, `/api/resumes/upload`
- Tin việc: `/api/jobs`, `/api/jobs/{id}`, `/api/locations`, `/api/skills`
- AI: `/api/ai/match`, `/api/candidates/me/recommendations`, `/api/jobs/{id}/ranked-candidates`, `/api/ai/extract-skills`
- Ứng tuyển/lưu tin: `/api/applications`, `/api/saved-jobs`
- BI: `/api/bi/summary`, `/api/bi/skills`, `/api/bi/salary`, `/api/bi/funnel`, `/api/bi/guest-token`
- Admin: `/api/admin/skills`, `/api/admin/skill-aliases`

## Tài liệu và giới hạn dữ liệu

Schema gồm 15 bảng và các migration nằm trong `backend/alembic`; SQL schema được xuất ở `backend/schema.sql`. Bốn view BI ở `bi/views.sql` đếm funnel theo lịch sử từng đạt trạng thái. Hướng dẫn backend/API nằm ở `docs/report/chuong_csdl_kien_truc_api.md`.

Các lần sinh trạng thái ứng tuyển độc lập với điểm match. Biểu đồ funnel chỉ minh họa cách tổng hợp, không chứng minh mô hình dự đoán tuyển dụng tốt. Mọi phép đo hiệu quả phải lấy từ nhãn độc lập được ghi rõ nguồn.
