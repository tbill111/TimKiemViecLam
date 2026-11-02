# Cơ sở dữ liệu, kiến trúc backend và API

## Kiến trúc triển khai

SmartCareer dùng frontend React/TypeScript ở thư mục gốc, FastAPI chạy trên Python 3.11, PostgreSQL 16 và Apache Superset 4.1.2. Docker Compose chạy bốn dịch vụ `web`, `api`, `db` và `superset`. Nginx phục vụ SPA, chuyển tiếp `/api/` đến FastAPI; API gọi tầng AI thuần qua các kiểu `CandidateInput`, `JobInput` và hàm `score_pair`.

Tầng API không đặt SQLAlchemy trong `backend/app/ai`. `SqlAIRepository` chuyển dữ liệu chuẩn hóa từ PostgreSQL thành kiểu AI. Embedding 384 chiều được tính khi lưu hồ sơ, CV hoặc tin tuyển dụng và lưu ở `BYTEA`; lúc chấm điểm API đọc vector đã lưu. Kỹ năng CV chỉ tham gia khớp sau khi ứng viên xác nhận.

## Thiết kế dữ liệu

Schema chuẩn hóa gồm 15 bảng:

| Bảng | Vai trò |
|---|---|
| `users` | Tài khoản, mật khẩu bcrypt, vai trò và công ty của recruiter |
| `locations` | Danh mục địa điểm, gồm cả `Remote` |
| `skills`, `skill_aliases` | Danh mục kỹ năng chuẩn, alias và lộ trình học JSONB |
| `companies`, `recruiters` | Hồ sơ doanh nghiệp và tài khoản tuyển dụng thuộc doanh nghiệp |
| `candidates`, `resumes`, `candidate_skills` | Hồ sơ chuẩn hóa, cấu trúc frontend, CV và kỹ năng đã xác nhận/chưa xác nhận |
| `jobs`, `job_skills` | Tin tuyển dụng, yêu cầu và kỹ năng ưu tiên |
| `applications`, `application_status_history` | Đơn ứng tuyển, trạng thái hiện tại và mọi lần chuyển trạng thái |
| `match_results`, `saved_jobs` | Kết quả chấm theo phiên bản model và tin đã lưu |

Các cột JSONB giữ phần hồ sơ có cấu trúc và danh sách trách nhiệm; các thuộc tính thường dùng để lọc/BI được chuẩn hóa. `jobs.category`, `jobs.responsibilities`, `candidates.profile_json`, `skills.learning_steps` và embedding ở `candidates`, `jobs`, `resumes` là các phần mở rộng theo hợp đồng nhóm. Lương dùng triệu VND/tháng; học vấn dùng thang 0–4.

Ràng buộc chính: email tài khoản và tên kỹ năng là duy nhất; application có `UNIQUE(candidate_id, job_id)`; lương có `CHECK salary_min <= salary_max`; enum vai trò, loại tin, hình thức làm việc và trạng thái được kiểm bằng `CHECK`; `education_level` và `match_score` nằm trong thang quy định. Khóa ngoại dùng `ON DELETE CASCADE` cho dữ liệu phụ thuộc hồ sơ và tin.

Migration `0001_init` tạo schema 15 bảng, `0002_views` tạo 4 view và cấp cho `bi_reader` quyền `SELECT` trên view. `backend/schema.sql` là bản DDL tham chiếu. Migration và view phải chạy trên PostgreSQL; SQLite không kiểm tra được kiểu JSONB, BYTEA, role hoặc ngữ pháp view PostgreSQL.

## Seed và dữ liệu mô phỏng

Seed cố định `random_seed=42`, dùng 80 kỹ năng, ít nhất 150 alias, 30 công ty, 150 tin và 300 hồ sơ ứng viên. Mười hai tin ban đầu được trích từ `src/data/jobs.ts`; các phần còn lại được đánh dấu là dữ liệu mô phỏng. `gen_applications.py` tạo khoảng 1.200 đơn và lịch sử phễu; xác suất chuyển trạng thái không phụ thuộc `match_score`. Điểm lưu ở đơn được tính bằng M3 để demo, không dùng các đơn mô phỏng để kết luận độ chính xác AI.

`load_seed.py` dùng một transaction với `pg_advisory_xact_lock`. `--reset` xóa view trước, xóa dữ liệu, nạp lại và tạo view trong cùng giao dịch. Vì vậy lỗi giữa quá trình seed không để lại database chỉ có một phần dữ liệu. Chạy lặp lại không nhân bản tài khoản, tin, hồ sơ hay đơn.

## API và xác thực

API dùng bearer JWT HS256. Mật khẩu băm trực tiếp bằng `bcrypt`; CORS cho phép frontend dev `http://localhost:5173` và Nginx `http://localhost:8080`. Không cho tự đăng ký admin; recruiter đăng ký phải cung cấp `company_name`.

| Nhóm | Endpoint | Quyền chính |
|---|---|---|
| Auth | `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me` | Công khai / đã đăng nhập |
| Tin | `GET /api/jobs`, `GET /api/jobs/{id}`, `POST/PUT/DELETE /api/jobs` | Mọi người / recruiter sở hữu tin |
| Hồ sơ | `GET/PUT/DELETE /api/candidates/me`, `GET/PUT /api/candidates/me/skills` | Candidate |
| CV | `POST /api/resumes/upload` | Candidate; yêu cầu consent, PDF/DOCX/TXT tối đa 5 MB |
| AI | `/api/ai/match`, recommendations, skill-gap, extract-skills, ranked-candidates | Candidate / recruiter theo quyền sở hữu tin |
| Ứng tuyển | `POST /api/applications`, `GET /api/applications/me`, `GET /api/jobs/{id}/applications`, `PATCH /api/applications/{id}/status` | Candidate / recruiter của công ty sở hữu tin |
| BI | `GET /api/bi/summary`, `skills`, `salary`, `funnel`, `guest-token` | Recruiter / admin |
| Admin | `/api/admin/skills`, `/api/admin/skill-aliases` | Admin |

Trạng thái ứng tuyển đi theo `applied → screening → interview → offer → hired`; từ trạng thái chưa kết thúc có thể chuyển sang `rejected`. `hired` và `rejected` là cuối. Mọi lần chuyển được ghi trong `application_status_history`; vi phạm trả 409 cùng trạng thái nguồn/đích. Recruiter chỉ xem hoặc sửa dữ liệu tin của công ty mình.

## BI và quyền lọc công ty

`v_skill_supply_demand` đếm ứng viên có kỹ năng đã xác nhận và số tin đang mở yêu cầu kỹ năng. `v_salary` tổng hợp lương theo địa điểm, danh mục, cấp bậc và tháng. `v_funnel` và `v_funnel_stages` đếm số đơn đã từng đạt mỗi trạng thái từ `application_status_history`, nên đơn đã tuyển vẫn được tính ở các giai đoạn trước.

Superset dùng database metadata `superset_meta`; datasource kết nối với `bi_reader`, chỉ có quyền đọc bốn view. Endpoint guest token gắn RLS `company_id` cho cả `v_funnel` và `v_funnel_stages`. Nếu thiếu ID dataset hoặc dashboard, recruiter nhận 503; backend không cấp token không lọc. API BI đọc cùng view làm fallback cho biểu đồ Recharts.

## Kiểm chứng và giới hạn

Migration, Docker, API integration và Superset phải được kiểm chứng trên PostgreSQL thật. `scripts/check_bi_views.py` đối chiếu view SQL với API. Không điền số liệu hiệu năng, P/R/F1, dashboard hay test case thành công cho tới khi có kết quả chạy thật. Ứng tuyển sinh ngẫu nhiên chỉ kiểm tra việc tổng hợp BI; chất lượng mô hình phải được đánh giá bằng nhãn độc lập và nêu rõ nguồn nhãn.
