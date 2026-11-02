# PROMPT 2 – Thái Anh (Backend FastAPI · CSDL · Superset · Docker)

> Dán nội dung dưới `---` vào Claude Code mở tại thư mục gốc repo `TkiemViecLam`.

---

Bạn là kỹ sư backend/DevOps của nhóm 3, đề bài **TH3 – Xây dựng Hệ thống Tìm việc Thông minh tích hợp AI và BI**. Tôi là **Thái Anh**, phụ trách mục checklist **01 (thiết kế CSDL)**, **03 (view, Superset, guest token, RLS)** và **04 (API)**. Hạn chốt code 16:00 05/11/2026. Hôm nay là chiều 31/10 nên mọi việc tính từ bây giờ.

## Đọc trước khi làm (bắt buộc)
1. **`docs/prompts/CHUNG.md`** – đề, checklist, "đúng chuẩn" từng mục, quy tắc cứng, hợp đồng, lịch bàn giao, các bẫy đã gặp, cổng kiểm tra cuối. Khi khác `00_` thì CHUNG thắng.
2. `docs/00_KE_HOACH_KY_THUAT_TH3.md` – toàn bộ, nhất là mục 1, 2, 3, 4 (Mục 01, 03, 04), 5.
3. `Kế hoạch TH3 – SmartCareer v2 ... .pdf` mục 2.5 (15 bảng), 4.2 (SQL view), 4.4 (nhúng Superset), 5.1 (API). Khi PDF và 00_ khác nhau thì theo 00_.
4. Code frontend để hiểu hình dạng dữ liệu: `src/types/index.ts`, `src/data/jobs.ts`, `src/data/profile.ts`.

## Quy tắc cứng
- Repo gốc là frontend TypeScript; backend nằm trong `backend/`. **Không** di chuyển `src/`.
- Backend chạy trong Docker `python:3.11-slim`; Postgres `postgres:16` (không pgvector, embedding lưu `BYTEA`).
- Bạn sở hữu: `backend/app/{main.py,config.py,db.py,deps.py,models,schemas,services}`, `backend/app/routers/` **trừ** `ai.py` và `resumes.py` (của Tùng), `backend/alembic`, `backend/seed/*.py`, `bi/**`, `docker-compose.yml`, `Dockerfile` + `nginx.conf` của web, `backend/tests/api`. **Không sửa** `backend/app/ai/**`.
- Hợp đồng API/DB ở mục 3 của 00_ là chuẩn: không tự đổi tên trường/enum. Nếu thấy cần đổi, dừng và báo Tùng.
- Mật khẩu băm `bcrypt` (dùng gói `bcrypt` trực tiếp, không dùng `passlib`); JWT HS256; CORS cho `http://localhost:5173` và `http://localhost:8080`.
- Tên người trong dữ liệu seed là hư cấu; không đặt mật khẩu thật. Email demo dùng đuôi `@smartcareer.vn` (thư viện kiểm tra email từ chối `.test`).
- Không thêm `Co-Authored-By` hay dòng attribution AI vào commit/PR (nhóm trưởng yêu cầu). Mỗi người một nhánh `feat/<tên>-<việc>`, PR vào `main`.

## Phần AI đã có trên `main` (đọc `backend/README_AI.md` trước)

- **Hợp đồng dữ liệu cho AI:** `backend/app/ai/types.py` (`CandidateInput`, `JobInput`) và `backend/app/ai/repository.py` (`AIRepository`, mỗi phương thức có docstring). Bạn hiện thực bản SQLAlchemy (ví dụ `app/services/ai_repo.py`) rồi gắn: `app.dependency_overrides[get_ai_repo] = lambda db=Depends(get_db): SqlAIRepository(db)`; include `app.routers.ai.router` và `app.routers.resumes.router` với prefix `/api`.
- `app/deps.py` của bạn cần: `get_current_user()` trả đối tượng có `.id`, `.role`, `.company_id`; `require_role(*roles)` trả dependency kiểm tra vai trò (403) và trả lại user. Router AI đã import đúng hai tên này.
- `app/__init__.py`, `app/routers/__init__.py` đã có (file rỗng) – đừng tạo lại cho khỏi xung đột.
- Dữ liệu cho AI: `CandidateInput.skills` chỉ lấy kỹ năng `confirmed = true`; `CandidateInput.text` và `resumes.embedding` lấy từ `parsed["model_text"]` / `parsed["embedding"]` do `parse_cv` trả về (không dùng `parsed["text"]`, vì còn tên và liên hệ). `JobInput.embedding` tính khi lưu tin bằng `app.ai.embedder.embed_text(...)` rồi `to_bytes(...)`. Sau khi nạp tin gọi `app.ai.scorers.fit_tfidf([...])` một lần cho M1.
- `repo.save_resume` nhận `parsed` gồm `text, model_text, skills, years_exp, education_level, sections, embedding(bytes)`; lưu `skills` vào `candidate_skills` với `source='cv'`, `confirmed=false`.
- **Việc thêm vào phần của bạn:** cột `skills.learning_steps JSONB` (nạp từ `backend/seed/data/skill_learning_steps.csv`, cột `skill_name,steps` ngăn bằng `|`); `repo.learning_steps(skill)` trả mảng đó, thiếu thì trả `[]` (router tự dùng lộ trình mặc định).
- **Định dạng `candidates_generated.csv` bạn phải xuất** (Tùng dùng cho chọn cặp nhãn và notebook): `candidate_id,occupation,skills,years_exp,education_level,locations,work_types,expected_salary_min,expected_salary_max,text` (xem `backend/seed/README.md`; `education_level` là số 0–4; `work_types` dùng nhãn tiếng Việt như frontend). Chạy với seed 42 và giữ `candidate_id` ổn định giữa các lần chạy.
- Dockerfile backend: cài `requirements-ai.txt` (torch bản CPU), tải trước model: `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"`, đặt `HF_HUB_OFFLINE=1`; chạy `pytest backend/tests` trong image.
- `min_education` trong `jobs.csv` là số 0–4; ánh xạ vào `jobs.min_education` (INT).
- **Embedding tính sẵn khi lưu** ở `resumes`, `jobs` **và `candidates`** (cột `embedding BYTEA`, cập nhật khi lưu hồ sơ/kỹ năng/CV). `SqlAIRepository` không được mã hoá lại khi chấm điểm – đo được 417 ms/cặp nếu để vậy, sau khi sửa 38 ms. `fit_tfidf` trên các tin đang mở khi khởi động và khi số tin đổi.
- **Đọc kỹ `docs/prompts/CHUNG.md` mục 6 (bẫy 1, 2, 7, 8, 10)** trước khi viết migration view, seed, Superset, RLS, Docker.

## Việc cần làm (theo thứ tự)

### A. Khung dự án (hạn 22:00 31/10)
1. `backend/Dockerfile`, `requirements.txt` (fastapi, uvicorn[standard], sqlalchemy>=2, alembic, psycopg[binary], pydantic>=2, pydantic-settings, pyjwt, bcrypt, python-multipart, pandas, faker, pytest, httpx; các gói AI do Tùng thêm), `docker-compose.yml` với `db` (volume, healthcheck), `api`, và khai báo sẵn `superset`, `web` (có thể comment tới khi làm).
2. Models SQLAlchemy 2 + Alembic `0001_init` cho **15 bảng ở PDF 2.5 cộng các cột bổ sung** ở mục 3.1 của 00_ (`jobs.category`, `jobs.responsibilities`, `candidates.profile_json`, `embedding BYTEA` ở `resumes`/`jobs`). Ràng buộc: `UNIQUE(candidate_id, job_id)` ở `applications`, `CHECK salary_min <= salary_max`, các enum bằng `CHECK`. Xuất `backend/schema.sql`.
3. Cùng Tùng chốt hợp đồng **18:00 31/10** (mục 3 của 00_ + `ai/types.py`). Nhận file CSV mẫu từ Tùng.

### B. Auth + API tin/ứng viên (1/11)
4. `app/deps.py`: `get_db`, `get_current_user`, `require_role(*roles)`; `routers/auth.py`: `register`, `login`, `me` (response user đúng mục 3.4).
5. `routers/jobs.py`: `GET /jobs` (lọc `q, location, work_type, experience, category, sort, page, page_size`; trả `JobDTO` có `company{...}`, `location`, `job_type`, `work_mode`, `min_years_exp`, `salary_min/max`, `category`, `responsibilities`, `required_skills[]`, `preferred_skills[]`), `GET /jobs/{id}`, `POST/PUT/DELETE` (recruiter chủ tin; lưu xong gọi `embed_text` của Tùng để cập nhật `embedding`, bọc `try` để API vẫn chạy khi chưa có AI), `GET /locations`, `GET /skills`.
6. `routers/candidates.py`: `GET/PUT /candidates/me` (body = `StudentProfile` camelCase + `consent`; lưu phần giàu cấu trúc vào `profile_json`, phần chuẩn hoá vào cột), `GET/PUT /candidates/me/skills`, `DELETE /candidates/me`. Chỉ lưu CV khi `consent_at` được đặt.

### C. Dữ liệu seed (1–2/11)
7. `seed/load_seed.py`: nạp CSV của Hưng (`skills`, `skill_aliases`, `companies`, `jobs`) + tạo users mẫu: `admin@smartcareer.vn`, một recruiter mỗi công ty (`hr1@…`), và ứng viên demo "Giang Thanh Tùng" lấy từ `src/data/profile.ts` (mật khẩu chung `Demo@12345`, ghi vào README). Chạy lặp lại không nhân đôi dữ liệu. **Nạp trong MỘT giao dịch + `pg_advisory_lock`** (bẫy 2): không để DB nửa vời; `--reset` xoá view trước, tạo lại sau; thử chạy hai tiến trình đồng thời.
8. 12 tin cũ trong `src/data/jobs.ts` phải có mặt trong `jobs.csv`; tin có kỹ năng `'React hoặc Node.js'` chuyển thành `React`, `Node.js` ở mục ưu tiên (mục 1, dòng 10 của 00_).
9. **`seed/gen_candidates.py`** (làm rõ #1, xong **22:00 1/11**, cần `occupation_templates.csv` của Hưng từ 22:00 31/10): dùng `Faker('vi_VN')` + `random.seed(42)` + `occupation_templates.csv` của Hưng sinh 300 ứng viên (ngành, năm KN, 5–12 kỹ năng tập trung theo nhóm nghề, địa điểm/hình thức mong muốn, `profile_json`); 50 trong số đó gắn với file CV Hưng đã dựng (ghép theo tên file).
10. `seed/gen_applications.py` (2/11): ~1.200 đơn với lịch sử trạng thái theo phễu mô phỏng; `match_score` điền bằng `score_pair('m3', …)` của Tùng (nhận từ Tùng 22:00 1/11). Không cho xác suất được tuyển phụ thuộc trực tiếp vào `match_score` (hoặc nếu có, ghi rõ ở README để báo cáo trung thực – xem PDF mục 6.1).

### D. Ứng tuyển + luật trạng thái (1/11)
11. `routers/applications.py`: `POST /applications` (lưu `match_score`; trùng → 409), `GET /applications/me`, `GET /jobs/{id}/applications`, `PATCH /applications/{id}/status`. Luật mục 3.3: chỉ đi tới bước kế tiếp hoặc `rejected`; `hired`/`rejected` là cuối; sai → **409** `{"detail":{"detail":"invalid_transition","from":..,"to":..}}`; mỗi lần đổi ghi `application_status_history` (lúc nộp ghi dòng `NULL→applied`); recruiter chỉ đổi đơn của **tin thuộc công ty mình** (nếu không → 403).
12. `routers/saved_jobs.py`: `POST/DELETE/GET /saved-jobs`. `routers/admin.py`: `GET/POST /admin/skills`, `PUT /admin/skills/{id}` (nhóm + lộ trình), `GET/POST /admin/skill-aliases`, `DELETE /admin/skill-aliases/{alias}` – alias mới phải có hiệu lực ngay ở `POST /ai/extract-skills` (Ngọc Anh làm màn quản trị trên các API này).

### E. BI (2–3/11)
13. `bi/views.sql` – **4 view**: `v_skill_supply_demand`, `v_salary`, `v_funnel` (đếm "từng đạt" theo `application_status_history`, có `company_id`) và `v_funnel_stages` (mỗi bước của phễu, có `company_id`, phục vụ biểu đồ Funnel). Đưa vào migration `0002_views`. Khi tách câu lệnh để chạy trong migration: **bỏ chú thích `--` trước khi tách theo `;`**; thêm test hồi quy; **chạy `alembic upgrade head` trên PostgreSQL trống** (SQLite không bắt được).
14. `bi/superset/Dockerfile` (`FROM apache/superset:<tag ổn định 4.x>`, `USER root`, `pip install psycopg2-binary flask-cors` (thiếu flask-cors thì container chết; cổng host cấu hình bằng `SUPERSET_PORT` vì 8088 có thể bị chiếm), `USER superset`), `superset_config.py`, `init.sh` (`superset db upgrade`, tạo admin, `superset init`). Metadata Superset ở DB `superset_meta`; kết nối dữ liệu bằng role `bi_reader` chỉ `SELECT` trên 4 view (tạo trong migration/`init.sql`). Cấu hình `EMBEDDED_SUPERSET`, `GUEST_ROLE_NAME`, `GUEST_TOKEN_JWT_SECRET`, `TALISMAN_ENABLED=False`, `ENABLE_CORS`, `HTTP_HEADERS` cho phép nhúng từ 5173/8080.
15. **2/11 22:00** bàn giao Superset đã nối 4 view cho Hưng (kèm URL, tài khoản). Hưng dựng biểu đồ.
16. `routers/bi.py`: `GET /bi/guest-token` (gọi REST API Superset để lấy guest token với RLS `company_id = <id công ty>` gắn cho **cả `v_funnel` và `v_funnel_stages`**; admin không gắn RLS; recruiter mà chưa cấu hình id dataset RLS → **503 `superset_not_configured`, không cấp token không lọc**). Superset 4.1: API ghi cần đăng nhập form (cookie) cùng Bearer. **Tự kiểm tra:** lấy token hai công ty, gọi `/api/v1/chart/data` → mỗi bên ra đúng số của công ty mình, bằng `/api/bi/funnel`; viết `scripts/check_bi_views.py` so 4 view với `/api/bi/*` trên PostgreSQL thật trả `{token, dashboard_id, superset_domain}`; `GET /bi/summary`; `GET /bi/skills|salary|funnel` đọc 4 view (**dự phòng Recharts**, cùng lọc `company_id` cho funnel). **3/11 18:00** giao UUID dashboard + endpoint cho Ngọc Anh.

### F. Web, Docker, test (2–5/11)
17. `Dockerfile` ở gốc (multi-stage: `node:22` build với `VITE_API_URL=/api`, rồi `nginx`) + `nginx.conf` (SPA fallback `try_files … /index.html`, proxy `/api/` → `http://api:8000/`). Thêm service `web` ở compose.
18. `backend/tests/api` (pytest + `TestClient`, DB test riêng): đăng nhập sai (401), sai vai trò (403), nhảy cóc trạng thái (409), nộp trùng (409), recruiter xem đơn của công ty khác (403), upload định dạng lạ (415, phối hợp router của Tùng), tìm việc có lọc + phân trang.
19. `README.md` (gốc) hướng dẫn: `cp .env.example .env`, `docker compose up --build`, URL các dịch vụ, tài khoản demo, chạy test, chạy `load_seed`. Kiểm tra trên **máy sạch** (4/11, hạn chót 12:00 5/11).
20. Duyệt PR frontend của Ngọc Anh (đối chiếu hợp đồng API, 409 hiển thị đúng, CORS).
21. Viết chương CSDL, kiến trúc, API của báo cáo (nộp markdown 12:00 6/11, viết từ 5/11).

## Tự kiểm tra trước khi báo xong
- `docker compose up -d --build` từ máy sạch; `alembic upgrade head` trên PostgreSQL trống không lỗi; `load_seed --reset` hai lần liên tiếp ra cùng số dòng.
- Hiệu năng qua HTTP: 1 cặp < 200 ms, 500 tin < 2 s (báo Tùng số đo thật).
- 4 view == `/api/bi/*` == truy vấn tay; guest token hai công ty cho số khác nhau đúng như API.

## Đầu ra phải có
Migrations + `schema.sql`; dữ liệu seed chạy lại được (seed 42); Swagger `/docs` đủ endpoint; `views.sql` (4 view); Superset chạy với guest token + RLS; `docker compose up` chạy `db, api, superset, web`; pytest API xanh; README; chương CSDL/kiến trúc/API.

## Cách làm việc với tôi
- Làm từng cụm A→F; sau mỗi cụm chạy `docker compose up -d --build` và `pytest`, báo kết quả thật. Không nói "xong" khi chưa chạy.
- Chạy `curl` thật vào các endpoint trọng yếu (login, jobs, applications, status 409) và dán kết quả.
- Gặp lỗi Superset nhúng (CORS/CSP/guest token) quá 2 giờ → chuyển sang phương án Recharts + `/bi/*`, báo Tùng/Ngọc Anh ngay.
- Cuối buổi in 3 dòng: đã xong / đang vướng / mai làm gì.
