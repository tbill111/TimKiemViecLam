# SmartCareer v2 – Hệ thống Tìm việc Thông minh tích hợp AI và BI (TH3)

Nền tảng kết nối ứng viên và nhà tuyển dụng: AI trích kỹ năng từ CV, tính **Matching Score có giải thích** giữa hồ sơ và tin tuyển dụng,
và dashboard **BI** cho nhà tuyển dụng (ứng viên theo kỹ năng, xu hướng lương, tỷ lệ chuyển đổi tuyển dụng).

| Thành phần | Công nghệ |
|---|---|
| Frontend | React 19 + Vite + TypeScript + Tailwind 4 + Recharts |
| Backend | FastAPI, SQLAlchemy 2, Alembic, JWT + bcrypt |
| CSDL | PostgreSQL 16 (SQLite khi chạy test) |
| AI | pdfplumber, python-docx, rapidfuzz, scikit-learn, sentence-transformers (`paraphrase-multilingual-MiniLM-L12-v2`) |
| BI | Apache Superset (nhúng bằng guest token) + phương án dự phòng Recharts |
| Triển khai | Docker Compose: `db`, `api`, `superset`, `web` |

## Chạy nhanh

### A. Toàn bộ hệ thống (Docker)

```bash
cp .env.example .env
docker compose up -d --build     # lần đầu build image có model embedding nên lâu; WITH_ST=0 trong .env để bỏ qua (dùng embedder thay thế)
python bi/superset/bootstrap.py --url http://localhost:8088 --write-env .env   # dựng dashboard Superset + bật nhúng
docker compose up -d api         # nạp UUID dashboard vào API
```

| Dịch vụ | Địa chỉ |
|---|---|
| Ứng dụng | http://localhost:8080 |
| Swagger | http://localhost:8000/docs |
| Superset | http://localhost:8088 (đổi `SUPERSET_PORT` trong `.env` nếu cổng bị chiếm; xem `bi/README.md`) |

API tự migrate (`alembic upgrade head`) và nạp dữ liệu demo khi khởi động (`SEED_ON_START=1`).

### B. Chỉ frontend với dữ liệu mẫu (không cần backend)

```bash
npm install
VITE_OFFLINE_DEMO=true npm run dev     # hoặc đặt trong .env.local
```

### C. Phát triển

```bash
# backend
cd backend && python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
DATABASE_URL=sqlite:///./dev.db python -m seed.load_seed --reset
DATABASE_URL=sqlite:///./dev.db uvicorn app.main:app --reload --port 8000
# frontend (terminal khác): cần proxy /api → 8000 hoặc đặt VITE_API_URL=http://localhost:8000/api
VITE_API_URL=http://localhost:8000/api npm run dev
```

## Tài khoản demo (mật khẩu chung `Demo@12345`)

| Vai trò | Email |
|---|---|
| Ứng viên (hồ sơ Giang Thanh Tùng) | `tung.demo@smartcareer.vn` |
| Nhà tuyển dụng (Sao Mai Software) | `hr01@smartcareer.vn` … `hr30@smartcareer.vn` |
| Quản trị | `admin@smartcareer.vn` |
| 300 ứng viên sinh tự động | `cand0001@example.edu.vn` … `cand0300@example.edu.vn` |

## Kiểm thử

```bash
cd backend && python -m pytest                 # 236 test: AI, API, phân quyền, luật trạng thái, phễu BI, seed, hiệu năng, migration
npm run build && npm run lint                  # kiểu TypeScript + oxlint
python scripts/e2e_smoke.py  --web http://localhost:8080     # E2E trình duyệt trên stack Docker: ứng viên, nhà tuyển dụng, quản trị (14 bước)
python scripts/check_bi_views.py                              # đối chiếu 4 view PostgreSQL với /api/bi/*
python scripts/e2e_offline.py --web http://localhost:4174    # E2E chế độ demo, kiểm tra không gọi API
```

Bảng 46 test case: [docs/testcases.md](docs/testcases.md).

## Cấu trúc

```
src/                    frontend (api/, context/, hooks/, pages/, components/, data/ = dữ liệu mẫu chế độ demo)
backend/app/            FastAPI: routers/, models.py, services/, ai/ (parser, scorers M0–M4, metrics, evaluate)
backend/seed/           sinh và nạp dữ liệu hư cấu (108 kỹ năng, 259 alias, 30 công ty, 150 tin, 300 ứng viên, 50 CV, ~1.200 đơn)
backend/alembic/        migration; backend/schema.sql = DDL PostgreSQL sinh từ models
bi/                     views.sql, cấu hình Superset, hướng dẫn dựng dashboard
notebooks/              đánh giá parser, huấn luyện M4, so sánh M0–M4
docs/                   kế hoạch, yêu cầu, Use Case, ERD, test case, hướng dẫn gán nhãn, prompt từng thành viên
scripts/                export dữ liệu chuẩn M0 từ TypeScript, E2E
```

## Điều cần biết (trung thực về trạng thái)

- **Dữ liệu là mô phỏng.** Ứng viên, CV, tin và đơn ứng tuyển đều hư cấu; xác suất đi tiếp mỗi bước phễu không phụ thuộc điểm khớp. Biểu đồ lương và tỷ lệ tuyển chỉ minh hoạ cách tính.
- **Hiệu quả mô hình chỉ kết luận từ nhãn tay** (30 ứng viên × 10 tin, hai người gán độc lập) bằng `notebooks/`. Các file nhãn và model M4 **chưa có**: `m4` trả 503 cho đến khi huấn luyện; số liệu trong notebook chạy trên dữ liệu tổng hợp chỉ để kiểm tra luồng.
- **Đã chạy thật trên Docker:** `docker compose up` (4 dịch vụ), migration và 4 view trên PostgreSQL 16 (khớp API từng số liệu), Superset 4.1.1 nhúng + RLS theo công ty, model embedding thật, E2E 14/14 và đo hiệu năng (xem [docs/E2E.md](docs/E2E.md)).
- **Chưa có:** nhãn tay và kết quả đánh giá trên nhãn tay (hiện chỉ có **nhãn mô phỏng** để chạy trọn quy trình: `backend/seed/labels/README_SYNTHETIC.md`; `models_store/m4.joblib` mang nhãn `SYNTHETIC` và giao diện cảnh báo); biểu đồ 5, 7 và Native Filters của Superset.
- CV dạng ảnh scan không đọc được; hệ thống báo lỗi thay vì đoán.
