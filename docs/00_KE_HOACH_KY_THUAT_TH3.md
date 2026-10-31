# TH3 – SmartCareer v2: Kế hoạch kỹ thuật (bản chỉnh theo repo hiện tại)

> Nguồn sự thật chung cho cả nhóm. Mọi prompt trong `docs/prompts/` đều tham chiếu file này.
> Phân công và khối lượng việc **giữ nguyên** như "Kế hoạch TH3 – SmartCareer v2.pdf". File này chỉ sửa cho khớp kỹ thuật với repo và bổ sung các chỗ thiếu để đủ checklist.

Hạn nộp chính thức: **08/11/2026 06:28** (chỉ 1 lần, định dạng video MP4/MOV/MKV/AVI/WEBM, ≤ 101 MB). Nhóm nộp nội bộ trước **22:00 07/11**. Chốt code **16:00 05/11** (đã dời từ 04/11 vì lịch bắt đầu lại từ chiều 31/10).

---

## 1. Những điểm plan PDF phải sửa cho đúng repo

| # | Plan PDF ghi | Thực tế repo | Quyết định chốt |
|---|---|---|---|
| 1 | Repo `smartcareer/` có thư mục `frontend/` | Frontend nằm ở **thư mục gốc** (`src/`, `package.json`, `vite.config.ts`). Thư mục này **chưa phải git repo** | **Không di chuyển frontend.** Thêm các thư mục anh em: `backend/`, `bi/`, `notebooks/`, `docs/`. Tùng chạy `git init`, đẩy lên GitHub trước 18:00 31/10 rồi mới dùng nhánh/PR |
| 2 | `src/api/client.js`, `src/api/*.js` | Dự án là **TypeScript**: `erasableSyntaxOnly`, `verbatimModuleSyntax`, `noUnusedLocals`, build bằng `tsc -b` | Dùng `src/api/client.ts`, `*.ts`. Không dùng `enum`/`namespace`/parameter properties. Import kiểu dùng `import type`. Phải qua `npm run build` và `npm run lint` |
| 3 | Python 3.11 | Máy dev có Python **3.13.9**; `torch`, `underthesea`, `sentence-transformers` hay lỗi wheel trên 3.13 | Backend chạy trong Docker `python:3.11-slim`. Dev/test cũng chạy trong container (hoặc venv 3.11). Torch dùng bản CPU |
| 4 | `pgvector` (tùy chọn), cột `vector(384)` | Không cần cho 150–500 tin | **Bỏ pgvector.** Image `postgres:16`. Embedding lưu `BYTEA` (numpy float32, 384×4 byte); nạp ma trận vào RAM khi khởi động, cosine bằng numpy |
| 5 | Xoá code đọc CV trên trình duyệt sau khi API upload ổn | Chế độ offline demo cần chính code đó (`src/utils/cvParser.ts`, `CvImport.tsx`, `pdfjs-dist`, `fflate`) | **Giữ cvParser.ts chỉ cho offline demo.** Chế độ online (mặc định) gọi API. Không để hai bộ parser cùng chạy trong một chế độ |
| 6 | Bảng `jobs` | Frontend `Job` có thêm `category` (10 giá trị), `responsibilities[]`, `companySize`, `companyIndustry`. Bảng 15 cột trong plan **không có** `category`, `responsibilities` | Thêm vào `jobs`: `category VARCHAR`, `responsibilities JSONB`. `companySize/Industry` lấy từ `companies.size_range/industry` |
| 7 | Bảng `candidates` | `StudentProfile` có `university, year, careerGoal, languages, projects[], experience[], certificates[], githubUrl, linkedinUrl, preferredLocations[], preferredWorkTypes[]` | Thêm `candidates.profile_json JSONB` giữ các trường giàu cấu trúc này. Giữ các cột chuẩn hoá (`years_exp, education_level, major, expected_salary_*, location_id`) để phân tích BI |
| 8 | `applications.status` 6 giá trị | Frontend `ApplicationStatus` chỉ 4 giá trị: `Đã ứng tuyển / Đang xem xét / Phỏng vấn / Đã kết thúc` | **Mở rộng frontend sang 6 giá trị** (xem 3.3). Sửa `types/index.ts`, `ApplicationsPage.tsx` (dòng 15, 22, 53, 181), `EmployerPage.tsx` (dòng 15, 168). Select trạng thái chỉ cho phép bước hợp lệ |
| 9 | Lương "triệu VNĐ/tháng" | Frontend `salary` là chuỗi `"3,000,000 – 5,000,000 VNĐ/tháng"` | DB lưu số (triệu VNĐ/tháng, ví dụ `3.0`). Adapter ở frontend dựng lại chuỗi đúng định dạng cũ |
| 10 | Kỹ năng ghi là chuỗi "A hoặc B" | Dữ liệu cũ có `'React hoặc Node.js'` (job tin thứ 6/7) và hậu tố `cơ bản` (ví dụ `Python cơ bản`) | DB chỉ lưu kỹ năng **đơn**. Tin cũ: chuyển `React`, `Node.js` thành kỹ năng ưu tiên. Python M0 phải **port đúng** `hasSkill` của TS (xem 4.2) |
| 11 | `location` là bảng chuẩn | Dữ liệu cũ có `location: 'Remote'` (ngoài Hà Nội/Hồ Chí Minh/Đà Nẵng) và `workType: 'Remote'` | `locations` có bản ghi `Remote` (region `Remote`). Giữ nguyên chuỗi địa điểm đúng như hiện tại |
| 12 | Nhánh/PR | Chưa có git | Xem mục 7 |
| 13 | `docker compose` chạy `web` | Chưa có Dockerfile cho frontend | Thêm `Dockerfile` (multi-stage node:22 build → nginx) và `nginx.conf` proxy `/api` → `api:8000` |
| 14 | Plan viết "Dữ liệu & ETL, Sơ đồ luồng dữ liệu, Giới thiệu giữ làm trang thuyết minh" | `ETLPage` dùng `sampleJobs` trực tiếp | Các trang này **được phép tiếp tục đọc dữ liệu mẫu** (`src/data/*`), chỉ cập nhật text/sơ đồ. Không bắt buộc nối API |

---

## 2. Cấu trúc repo (đích)

```
TkiemViecLam/                    # = gốc git repo, cũng là frontend
├─ src/ public/ index.html package.json vite.config.ts ...   # frontend hiện có
│  ├─ api/                       # MỚI: client.ts, adapters.ts, jobs.ts, auth.ts, ai.ts, applications.ts, bi.ts
│  ├─ context/                   # MỚI: AuthContext, JobsContext
│  └─ pages/ (Login, Register, EmployerJobs, EmployerCandidates, EmployerDashboard, PostJob ...)
├─ Dockerfile  nginx.conf        # web
├─ docker-compose.yml            # db, api, superset, web
├─ .env.example
├─ backend/
│  ├─ Dockerfile  requirements.txt  alembic.ini
│  ├─ app/{main.py, config.py, db.py, deps.py, models/, schemas/, routers/, services/}
│  ├─ app/ai/{types.py, skills.py, parser.py, embedder.py, features.py, scorers.py, explain.py}
│  ├─ alembic/versions/
│  ├─ seed/{data/*.csv, labels/*.csv, load_seed.py, gen_candidates.py, gen_applications.py}
│  ├─ models_store/              # m4.joblib, m3_weights.json
│  └─ tests/{ai/, api/, golden/}
├─ bi/
│  ├─ views.sql
│  ├─ superset/{Dockerfile, superset_config.py, init.sh, dashboard_export.zip}
│  └─ screenshots/
├─ notebooks/{01_parser_eval.ipynb, 02_train_m4.ipynb, 03_ranking_eval.ipynb}
├─ scripts/export-golden.ts      # xuất fixture để so khớp M0 Python với TS
└─ docs/{00_KE_HOACH_KY_THUAT_TH3.md, prompts/, usecase/, erd/, testcases.xlsx, report/}
```

Cổng: web dev `5173`, web nginx `8080`, api `8000` (Swagger `/docs`), superset `8088`, db `5432`.
Biến môi trường (`.env.example`): `DATABASE_URL`, `JWT_SECRET`, `DEFAULT_MODEL=m3`, `SUPERSET_URL`, `SUPERSET_ADMIN_USER/PASSWORD`, `GUEST_TOKEN_JWT_SECRET`, `VITE_API_URL=/api`, `VITE_OFFLINE_DEMO=false`.

Thêm `.gitattributes` với `* text=auto eol=lf` (script `.sh` trong container hỏng nếu bị CRLF trên Windows). Thêm vào `.gitignore`: `.env`, `__pycache__/`, `.venv/`, `.pytest_cache/`, `backend/models_store/*.pt`, `*.ipynb_checkpoints`.

---

## 3. Hợp đồng dữ liệu và API (chốt 18:00 31/10, chỉ đổi khi cả nhóm đồng ý)

### 3.1. Bổ sung/ràng buộc CSDL (so với 15 bảng trong plan PDF)
- Giữ nguyên 15 bảng và tên cột trong plan, **cộng**: `jobs.category`, `jobs.responsibilities`, `candidates.profile_json`, `resumes.embedding BYTEA`, `jobs.embedding BYTEA`.
- `jobs.status ∈ {open, closed}`, `jobs.level ∈ {intern, fresher, junior, middle, senior}`, `jobs.job_type ∈ {full_time, part_time, internship}`, `jobs.work_mode ∈ {onsite, hybrid, remote}`.
- `applications.status ∈ {applied, screening, interview, offer, hired, rejected}`.
- Thêm `skills.learning_steps JSONB` (lộ trình học cho Skill Gap, nạp từ `skill_learning_steps.csv`; thiếu thì API dùng lộ trình mặc định 3 bước).
- `skills.name` là tên chuẩn đúng chính tả đang dùng ở frontend (ví dụ `Thống kê cơ bản`, `REST API`, `Power BI`).
- Mọi bảng dùng khóa `INTEGER`/`BIGINT` tự tăng; **frontend dùng `String(id)`** (type `Job.id: string` không đổi).

### 3.2. Chuyển đổi giữa DB và kiểu frontend (adapter nằm ở `src/api/adapters.ts`)

| Frontend (`src/types`) | Backend (JSON) |
|---|---|
| `Job.workType: WorkType` | `work_mode == 'remote'` → `'Remote'`; ngược lại `job_type`: `full_time`→`Toàn thời gian`, `part_time`→`Bán thời gian`, `internship`→`Thực tập` |
| Ngược lại (đăng tin) | `'Remote'`→ `{job_type:'full_time', work_mode:'remote'}`; còn lại `work_mode:'onsite'` |
| `Job.experienceLevel` | theo `min_years_exp`: `0`→`Chưa có kinh nghiệm`; `(0,1)`→`Dưới 1 năm`; `[1,2)`→`1-2 năm`; `[2,3)`→`2-3 năm`; `≥3`→`3+ năm` (khi đăng tin gửi `0, 0.5, 1, 2, 3`) |
| `Job.salary: string` | dựng từ `salary_min/max` (triệu): `"3,000,000 – 5,000,000 VNĐ/tháng"`; NULL → `"Thỏa thuận"` |
| `Job.location` | `location` (tên chuỗi) |
| `Job.companySize/Industry` | `company.size_range / company.industry` |
| `Job.category` | `category` (đúng 10 giá trị của `JobCategory`) |
| `Application.status` | xem 3.3 |
| `Application.id/jobId` | `String(id)`, `String(job_id)` |

### 3.3. Trạng thái ứng tuyển (6 giá trị) – phải đồng nhất ở DB, API, UI

| `status` (DB/API) | Nhãn frontend (`ApplicationStatus`) | Badge gợi ý |
|---|---|---|
| `applied` | `Đã ứng tuyển` | xanh dương |
| `screening` | `Đang xem xét` | vàng |
| `interview` | `Phỏng vấn` | tím |
| `offer` | `Đề nghị` | xanh lá nhạt |
| `hired` | `Đã tuyển` | xanh lá |
| `rejected` | `Từ chối` | xám |

Luật chuyển (backend chặn, frontend chỉ hiển thị bước hợp lệ):
`applied → screening → interview → offer → hired`; từ bất kỳ trạng thái **chưa cuối** → `rejected`; `hired`, `rejected` là cuối. Sai luật → HTTP **409** `{"detail":"invalid_transition","from":"...","to":"..."}`. Mỗi lần đổi ghi 1 dòng `application_status_history`; lúc nộp ghi dòng đầu `from_status=NULL, to_status='applied'`.

### 3.4. Danh sách API (tiền tố `/api`, JSON, lỗi theo FastAPI `{"detail": ...}`)

| Nhóm | Endpoint | Vai trò | Ghi chú |
|---|---|---|---|
| Auth | `POST /auth/register` `{email,password,role,full_name,company_name?}` | công khai | `role ∈ candidate/recruiter`; admin chỉ seed |
| | `POST /auth/login` → `{access_token, token_type:"bearer", user:{id,email,role,full_name,company_id?}}` | công khai | sai mật khẩu 401 |
| | `GET /auth/me` | mọi vai trò | |
| Hồ sơ | `GET/PUT /candidates/me` | candidate | body = `StudentProfile` (đúng tên trường frontend, camelCase) + `consent: boolean` |
| | `GET/PUT /candidates/me/skills` `{skills: string[]}` | candidate | PUT = xác nhận → `confirmed=true, source` giữ nguyên |
| | `DELETE /candidates/me` | candidate | xóa hồ sơ + CV (đáp ứng yêu cầu dữ liệu cá nhân) |
| CV | `POST /resumes/upload` multipart `file`, `consent=true` | candidate | PDF/DOCX/TXT ≤ 5 MB; 415 sai định dạng, 413 quá lớn, 422 không trích được chữ (ảnh scan) |
| Tin | `GET /jobs?q=&location=&work_type=&experience=&category=&sort=relevance|newest&page=&page_size=` | mọi | trả `{items:[JobDTO], total, page, page_size}`; nếu người gọi là candidate, mỗi item có `match` (MatchDTO) |
| | `GET /jobs/{id}` | mọi | |
| | `POST/PUT/DELETE /jobs` | recruiter (chủ tin) | lưu xong tính embedding; DELETE = đóng tin |
| | `GET /locations`, `GET /skills` | mọi | cho ô lọc/gợi ý |
| AI | `POST /ai/match` `{job_id, model?: "m0".."m4", candidate_id?}` → MatchDTO | candidate (mình) / recruiter (ứng viên đã nộp vào tin của mình) | |
| | `GET /candidates/me/matches?model=` → `{items:[{job_id, match}]}` cho **mọi tin đang mở** | candidate | thay `getAllMatchScores` ở frontend |
| | `GET /candidates/me/recommendations?top=10` | candidate | |
| | `GET /candidates/me/skill-gap?job_id=` → `{job_id, missing:[{skill,required,jobs_demanding,learning_steps[]}] }` | candidate | |
| | `POST /ai/extract-skills` `{text}` → `{skills:[{name,source,confidence}]}` | recruiter | gợi ý kỹ năng từ JD |
| | `GET /jobs/{id}/ranked-candidates?top=20` | recruiter chủ tin | chỉ ứng viên **đã nộp** vào tin đó |
| Ứng tuyển | `POST /applications` `{job_id, resume_id?}` | candidate | lưu `match_score`; trùng → 409 |
| | `GET /applications/me` | candidate | kèm `history[]` |
| | `GET /jobs/{id}/applications` | recruiter chủ tin | |
| | `PATCH /applications/{id}/status` `{status, note?}` | recruiter chủ tin | luật 3.3 |
| | `POST /saved-jobs/{job_id}`, `DELETE /saved-jobs/{job_id}`, `GET /saved-jobs` | candidate | |
| BI | `GET /bi/guest-token` → `{token, dashboard_id, superset_domain}` | recruiter, admin | RLS: `company_id = <công ty người gọi>`; admin không gắn RLS |
| | `GET /bi/summary` → `{candidates, open_jobs, applications, hire_rate}` | mọi | thẻ KPI trang Tổng quan |
| | `GET /bi/skills`, `/bi/salary`, `/bi/funnel` | recruiter, admin | **dự phòng Recharts** nếu nhúng Superset lỗi; đọc đúng 3 view |
| Admin | `GET/POST /admin/skills`, `/admin/skill-aliases` | admin | |

**MatchDTO** (một dạng duy nhất cho mọi model):
```json
{
  "model": "m3", "model_version": "m3-2026-11-02",
  "total_score": 72,
  "components": {"skill_req": 80, "skill_pref": 66, "semantic": 71, "exp": 100, "edu": 100, "pref": 50},
  "matched_required": ["HTML","CSS"], "missing_required": ["TypeScript"],
  "matched_preferred": ["Git"], "missing_preferred": ["REST API"],
  "location_match": true, "work_type_match": false,
  "explanation": "Khớp 72/100. Đã có HTML, CSS. Thiếu TypeScript (bắt buộc) và REST API (ưu tiên)."
}
```
Điểm là số nguyên 0–100. Ánh xạ sang `SkillMatchResult` hiện có: `matchScore=total_score`, `requiredScore=components.skill_req`, `preferredScore=components.skill_pref`, `preferenceScore=components.pref`, `matchedSkills=matched_required`, `missingSkills=missing_required`, `matchedPreferred/missingPreferred` như tên, `totalRequired=matched_required.length+missing_required.length`, `locationMatch/workTypeMatch` như tên. Thêm 4 trường **tùy chọn** vào `SkillMatchResult`: `semanticScore?`, `expScore?`, `eduScore?`, `explanation?`, `model?` (Ngọc Anh thêm).
Với `m0`: `components.semantic/exp/edu` bằng `null`, và `pref` = 50/50 địa điểm + hình thức như `calculateSkillMatch`.

### 3.5. Ranh giới code giữa Tùng và Thái Anh (chốt 18:00 31/10)
Tùng sở hữu `backend/app/ai/**`, Thái Anh sở hữu phần còn lại của `backend/app/**`. AI không import SQLAlchemy; Thái Anh gọi AI qua các hàm thuần trong `backend/app/ai/types.py`:
```python
@dataclass class JobInput: id:int; required:list[str]; preferred:list[str]; min_years:float; min_edu:int; location:str; work_type_label:str; salary_min:float|None; salary_max:float|None; text:str; embedding:np.ndarray|None
@dataclass class CandidateInput: id:int; skills:list[str]; years_exp:float; edu:int; locations:list[str]; work_types:list[str]; sal_min:float|None; sal_max:float|None; text:str; embedding:np.ndarray|None
def score_pair(model:str, cand:CandidateInput, job:JobInput) -> dict   # = MatchDTO
def parse_cv(data:bytes, filename:str) -> dict    # ParsedCV: skills[], years_exp, education_level, sections, text, embedding(bytes)
def suggest_skills(text:str) -> list[dict]
def embed_text(text:str) -> np.ndarray
```
Router `ai.py`, `resumes.py` (phần xử lý) do Tùng viết; Thái Anh viết `main.py` gắn router, models, dependency auth (`get_current_user`, `require_role`). Tùng tạo router gọi `Depends` từ `app/deps.py` của Thái Anh.

---

## 4. Việc kỹ thuật theo 5 mục checklist

### Mục 01 – Phân tích yêu cầu & thiết kế CSDL
**Người:** Hoàng Anh (phân tích, Use Case, ERD), Thái Anh (schema/migration/seed loader), Hoàng Hưng (dữ liệu).
- Bảng yêu cầu F01–F10 (đã có ở PDF mục 2.2) + phi chức năng (2.3) → `docs/report/01_phan_tich_yeu_cau.md`.
- Use Case: PlantUML/draw.io, 4 tác nhân, 10 use case, 3 `<<include>>`; đặc tả chi tiết 3 use case: *Tải CV*, *Xem việc gợi ý*, *Đổi trạng thái ứng tuyển*.
- ERD đủ 15 bảng + các cột bổ sung ở 3.1, xuất `docs/erd/erd.png` + `.dbml`.
- `backend/alembic/versions/0001_init.py` + `schema.sql` xuất từ migration (`pg_dump --schema-only`).
- Seed: `skills.csv ≥ 80`, `skill_aliases.csv ≥ 150`, 30 công ty, 150 tin (gồm 12 tin cũ), 300 ứng viên, ~1.200 đơn.
**Xong khi:** `docker compose up db api` chạy migration và `python -m seed.load_seed` không lỗi; `SELECT COUNT(*)` khớp số lượng trên; ERD khớp schema.

### Mục 02 – Mô hình AI/ML
**Người:** Tùng.
- **Module A (CV Parser)** `ai/parser.py`, `ai/skills.py`: pdfplumber/python-docx/TXT → chuẩn hoá NFC → tách mục → trích kỹ năng 3 tầng (n-gram tra `skills`+`skill_aliases`; rapidfuzz ≥ 90; embedding cosine ≥ 0,8 chỉ **đề xuất**) → số năm kinh nghiệm (gộp khoảng thời gian không chồng) → học vấn thang 1–4. Đánh giá P/R/F1 từng tầng trên 50 CV nhãn tay.
- **Module B** `ai/features.py`, `ai/scorers.py`: 6 đặc trưng (`skill_req, skill_pref, semantic, exp, edu, pref`), M0–M4 cùng giao diện `score_pair`; M3 có luật chặn ≤ 50 khi thiếu > 1/2 kỹ năng bắt buộc; M4 = LogisticRegression trên 6 đặc trưng, GroupKFold 5 theo `candidate_id`, lưu `joblib` + `model_version`.
- **Điều kiện đúng với repo:** M0 Python phải cho **cùng điểm** với `calculateSkillMatch` của `src/utils/index.ts` trên 12 tin × 6 ứng viên mẫu (`candidates.ts`) + hồ sơ `defaultStudentProfile`. Làm bằng `scripts/export-golden.ts` (chạy `npx tsx`) → `backend/tests/golden/m0_golden.json` → `tests/golden/test_m0_parity.py`.
**Xong khi:** bảng P/R/F1; bảng M0–M4; `m4.joblib`; `POST /ai/match` trả MatchDTO cho cả 5 model; `pytest backend/tests/ai backend/tests/golden` xanh.

### Mục 03 – Dashboard BI
**Người:** Thái Anh (views, Superset, guest token, RLS), Hoàng Hưng (biểu đồ, nhận định).
- `bi/views.sql`: `v_skill_supply_demand`, `v_salary`, `v_funnel` (SQL mẫu ở PDF mục 4.2; nhớ `v_funnel` đếm "từng đạt" từ `application_status_history` và có cột `company_id`).
- Superset: image tùy chỉnh `bi/superset/Dockerfile` (`FROM apache/superset:<tag>`, `USER root`, `pip install psycopg2-binary`, `USER superset`). Metadata Superset dùng DB riêng `superset_meta`; kết nối dữ liệu bằng role Postgres `bi_reader` chỉ có `SELECT` trên 3 view.
- `superset_config.py`: `FEATURE_FLAGS={"EMBEDDED_SUPERSET": True}`, `GUEST_ROLE_NAME`, `GUEST_TOKEN_JWT_SECRET`, `TALISMAN_ENABLED=False` (dev), `ENABLE_CORS=True` + `CORS_OPTIONS` cho origin `5173` và `8080`, `HTTP_HEADERS={"X-Frame-Options": "ALLOWALL"}`.
- Bắt buộc biểu đồ **2, 4, 6**; mở rộng ≥ 2 trong **1, 3, 5, 7, 8**. Bộ lọc chung: thời gian, địa điểm, cấp bậc, nhóm kỹ năng.
- RLS: `v_funnel` lọc `company_id`; dữ liệu thị trường (kỹ năng, lương) chung.
- Xuất `bi/superset/dashboard_export.zip`, ảnh `bi/screenshots/*.png`, 3–4 nhận định.
**Xong khi:** 3 số bắt buộc trên dashboard khớp truy vấn SQL tay; recruiter công ty A không thấy `v_funnel` công ty B.

### Mục 04 – Frontend & tích hợp API
**Người:** Ngọc Anh (giao diện), Thái Anh (API).
- `src/api/client.ts` (axios, `baseURL = import.meta.env.VITE_API_URL`, gắn JWT từ `localStorage['smartcareer_token']`, 401 → `/login`).
- `src/api/adapters.ts` (xem 3.2, 3.4), `src/context/AuthContext.tsx`, `src/context/JobsContext.tsx` cung cấp `jobs`, `matchScores: Map<string, SkillMatchResult>`.
- **Gỡ phụ thuộc cứng `sampleJobs`:** các file import trực tiếp `sampleJobs` ở chế độ online phải lấy từ `useJobs()` – `DashboardPage`, `JobsPage`, `MatchPage`, `SkillGapPage`, `ApplicationsPage`, `EmployerPage`, `Sidebar` (qua `countSuitableJobs`), và `src/utils/index.ts` (`countSuitableJobs`, `countJobsWithSkill`, `getAllMatchScores` nhận `jobs` làm tham số thay vì đọc `sampleJobs`). `ETLPage`, `DFDPage`, `AboutPage` được giữ nguyên.
- `useAppState`: giữ nguyên chữ ký trả về `UseAppState`; thêm hai cách cài (offline = như cũ dùng `localStorage`; online = gọi API `saved-jobs`, `applications`, `candidates/me`). Nhờ vậy các trang gọi `applyToJob(jobId)`, `saveJob`, `updateProfile` không phải đổi.
- Biến `VITE_OFFLINE_DEMO=true` → toàn bộ chạy như bản hiện tại (không cần backend).
- Màn mới: `/login`, `/register` (chọn vai trò), `/employer/jobs` (quản lý tin), `/employer/jobs/new` (đăng tin + nút "Gợi ý kỹ năng từ mô tả" + tick bắt buộc/ưu tiên), `/employer/candidates` (Kanban 6 cột theo 3.3 + xếp hạng điểm), `/employer/dashboard` (nhúng Superset, bọc `try/catch` → fallback Recharts đọc `/bi/*`). `/employer` cũ redirect sang `/employer/candidates`.
- Hồ sơ: `ProfilePage` + `CvImport.tsx` gọi `POST /resumes/upload`, hiện màn xác nhận kỹ năng (giữ UX cũ) + ô đồng ý xử lý dữ liệu (`consent`); `MatchPage` thêm ô chọn model M0–M4 + hiện 6 thành phần + `explanation`.
- Mọi trang có 3 trạng thái tải / lỗi / rỗng (tạo `components/ui/ErrorBlock.tsx`, `EmptyBlock.tsx` cạnh `LoadingBlock.tsx`).
**Xong khi:** `npm run build` + `npm run lint` sạch; 2 luồng end-to-end chạy thật (xem 6); `VITE_OFFLINE_DEMO=true` vẫn chạy trọn.

### Mục 05 – Kiểm thử & báo cáo đánh giá mô hình
**Người:** Tùng (đánh giá mô hình), Hoàng Hưng + Hoàng Anh (nhãn, test, báo cáo).
- Dữ liệu: seed cố định `random_seed=42`. `gen_candidates.py` sinh 300 hồ sơ từ `occupation_templates.csv` (Hưng cung cấp); `gen_cv_files.py`/Hưng tạo 50 file CV PDF/DOCX (có thể dùng `public/cv-mau.pdf` làm mẫu bố cục).
- Nhãn: 30 ứng viên × 10 tin = 300 cặp → `labels_pairs_<tên>.csv` (cột `candidate_id,job_id,label`); hai người gán độc lập, kappa quadratic ≥ 0,6; 50 CV → `labels_cv_skills.csv` (`cv_file,skills` ngăn bởi `|`).
- Đánh giá: Precision@5, nDCG@10, MRR, Spearman, ROC-AUC, thời gian/cặp; ablation M3; hệ số M4; 5 cặp sai nhiều nhất; công bằng (đổi tên/giới tính CV → điểm không đổi).
- Kiểm thử: pytest AI + API (đủ 403/409/415/401); ≥ 25 test case thủ công theo F01–F10; hiệu năng `/candidates/me/matches` với 150 và 500 tin (< 2 s); đối chiếu SQL cho 3 chỉ số BI.
- Báo cáo theo dàn ý PDF 6.5. Lưu ý trung thực: dữ liệu ứng tuyển là mô phỏng → biểu đồ 8 không chứng minh mô hình tốt; chỉ kết luận từ 300 cặp nhãn tay.
**Xong khi:** đủ sản phẩm ở PDF 6.6.

---

## 5. Phân công (giữ nguyên) và hai điểm làm rõ

| Người | Việc chính |
|---|---|
| **Tùng** (nhóm trưởng) | Git repo + chốt hợp đồng (mục 3); `backend/app/ai/**`; M0–M4; API AI; chọn 300 cặp; huấn luyện M4; notebook đánh giá; duyệt PR AI; tích hợp cuối; quay video |
| **Thái Anh** | Models + Alembic; JWT/auth deps; API tin/ứng viên/ứng tuyển/saved; luật trạng thái; load CSV; **`gen_candidates.py`** (làm rõ #1); `gen_applications.py`; `views.sql`; Superset + guest token + RLS; Docker Compose + Dockerfile web; pytest API; duyệt PR frontend |
| **Ngọc Anh** | Toàn bộ mục "Frontend" ở 4 – Mục 04 |
| **Hoàng Hưng** | `skills.csv`, `skill_aliases.csv`, **`occupation_templates.csv`** (làm rõ #2: nhóm nghề → kỹ năng cốt lõi, ~8 nhóm), `companies.csv`, `jobs.csv`; 50 file CV; gán nhãn người 1; biểu đồ Superset; chương BI |
| **Hoàng Anh** | Yêu cầu, Use Case, ERD; gán nhãn kỹ năng 50 CV; gán nhãn người 2; ≥ 25 test case; ghép báo cáo, slide |

Hai điểm làm rõ chỉ là chỉ định lại nơi chịu trách nhiệm cho việc đã có trong PDF 6.1 mà trước đó không có tên người; không đổi khối lượng đáng kể.

### 5.1. Lịch theo ngày (cập nhật chiều 31/10 – bắt đầu lại từ bây giờ)

Còn khoảng 3,5 ngày làm việc tới chốt code, nên mọi việc của 29–30/10 coi như **chưa làm** và nén vào lịch dưới. **Chốt code dời từ 16:00 04/11 sang 16:00 05/11.** Mốc nộp nội bộ 22:00 07/11 và hạn chính thức 06:28 08/11 không đổi. Cả 5 người làm song song ngay từ chiều nay.

| Ngày | Tùng | Thái Anh | Ngọc Anh | Hoàng Hưng | Hoàng Anh |
|---|---|---|---|---|---|
| **T7 31/10 chiều–tối** | `git init`; **18:00** chốt hợp đồng (`ai/types.py`, CSV mẫu) và gửi nhóm; **20:00** gửi mẫu JSON MatchDTO cho Ngọc Anh; parser tầng 1; bắt đầu `features.py` + M0 + golden parity | khung backend; compose `db`,`api`; models + migration `0001`; **22:00** `docker compose up db api` chạy được | `client.ts`; adapters; `AuthContext`; trang login/register (dùng mock) | **22:00** `skills.csv`, `skill_aliases.csv`, `occupation_templates.csv`; bắt đầu `companies.csv` + `jobs.csv` | yêu cầu F01–F10 + phi chức năng; Use Case |
| **CN 1/11** | parser tầng 2–3, năm KN, học vấn; `features.py`, M0–M3; **22:00** giao `score_pair('m3')` cho Thái Anh | JWT, API tin + ứng viên; API ứng tuyển + luật trạng thái + lịch sử + saved; nạp CSV; **22:00** `gen_candidates.py` xong | chặn route theo vai trò; Tìm việc + Hồ sơ nối API; upload CV + màn xác nhận kỹ năng; trang Đăng tin | **18:00** `companies.csv` + `jobs.csv` (150 tin); bắt đầu 50 file CV | ERD (xong 22:00); bắt đầu soạn test case từ F01–F10 |
| **T2 2/11** | **12:00** giao 300 cặp + hướng dẫn nhãn; API `/ai/*`, recommendations, ranked, skill-gap, **18:00** chạy trên Swagger | `gen_applications`; `views.sql`; dựng Superset, **22:00** giao Hưng; pytest API | Phân tích CV–JD, Skill Gap, Việc đã lưu & Ứng tuyển, Kanban | **12:00** xong 50 file CV; từ 12:00 gán nhãn cặp | **12:00** nhận 50 CV, gán nhãn kỹ năng; sau đó gán nhãn cặp; viết 25 test case |
| **T3 3/11** | **12:00** nhận nhãn CV, chạy P/R/F1 parser; hỗ trợ tích hợp; viết kappa script | guest token + RLS, **18:00** giao UUID; sửa lỗi tích hợp; README | Tổng quan `/bi/summary`; nhúng dashboard khi có token; 3 trạng thái tải/lỗi/rỗng | biểu đồ 2, 4, 6; **22:00 xong nhãn cặp** | **12:00 xong nhãn kỹ năng 50 CV**; **22:00 xong nhãn cặp**; chạy thử test case |
| **T4 4/11** | kappa; huấn luyện M4; bảng M0–M4; ablation; **22:00** có `m4.joblib` | `docker compose up` trên máy sạch; sửa lỗi API | offline demo; sửa lỗi giao diện; ảnh màn hình | biểu đồ mở rộng + bộ lọc; export dashboard | ghi kết quả test case |
| **T5 5/11** | **12:00** nối M4 vào API, chạy lại end-to-end; **16:00 CHỐT CODE** (chỉ sửa lỗi chặn, Tùng duyệt); tối quay video | viết chương CSDL, kiến trúc, API | viết chương giao diện + ảnh | ảnh dashboard + 3–4 nhận định (12:00); viết chương BI | viết chương giới thiệu, yêu cầu, kiểm thử |
| **T6 6/11** | **18:00** viết xong chương AI + đánh giá; **22:00** dựng xong video | nộp bản viết **12:00** | nộp bản viết **12:00** | nộp bản viết **12:00** | ghép báo cáo; slide |
| **T7 7/11** | duyệt bản cuối; **nộp trước 22:00** | sẵn sàng sửa | sẵn sàng sửa | sẵn sàng sửa | sửa định dạng |

Nếu trễ, cắt theo thứ tự: biểu đồ mở rộng (còn tối thiểu 2) → M1 TF-IDF → LightGBM/ablation → nhãn xuống 200 cặp (chỉ 20 ứng viên).

### 5.2. Bàn giao (ai chờ ai)

| Hạn | Giao | Nhận | Bàn giao |
|---|---|---|---|
| **31/10 18:00** | Tùng + Thái Anh | cả nhóm | file này + `ai/types.py` + schema + file mẫu CSV |
| **31/10 20:00** | Tùng | Ngọc Anh | mẫu JSON MatchDTO + fixture mock để làm UI trước khi API xong |
| **31/10 22:00** | Hưng | Thái Anh, Tùng | `skills.csv`, `skill_aliases.csv`, `occupation_templates.csv` |
| **1/11 18:00** | Hưng | Thái Anh | `companies.csv`, `jobs.csv` |
| **1/11 22:00** | Thái Anh | Tùng | `gen_candidates.py` chạy xong, có 300 ứng viên trong DB |
| **1/11 22:00** | Tùng | Thái Anh | `score_pair('m3', ...)` chạy được để `gen_applications` điền `match_score` |
| **2/11 12:00** | Tùng | Hưng, Hoàng Anh | 300 cặp cần gán nhãn + hướng dẫn gán nhãn |
| **2/11 12:00** | Hưng | Hoàng Anh, Thái Anh | 50 file CV + `cv_manifest.csv` |
| **2/11 18:00** | Tùng | Ngọc Anh | API AI chạy trên Swagger |
| **2/11 22:00** | Thái Anh | Hưng | Superset chạy, nối 3 view |
| **3/11 12:00** | Hoàng Anh | Tùng | `labels_cv_skills.csv` |
| **3/11 18:00** | Thái Anh | Ngọc Anh | API guest token + UUID dashboard |
| **3/11 22:00** | Hưng, Hoàng Anh | Tùng | hai file nhãn cặp độc lập |
| **5/11 16:00** | cả nhóm | Tùng | `main` chạy bằng `docker compose up` |
| **6/11 12:00** | Thái Anh, Ngọc Anh, Hưng | Hoàng Anh | phần viết báo cáo |
| **6/11 18:00** | Tùng | Hoàng Anh | chương AI + đánh giá |

---

## 6. Định nghĩa "xong" chung (Definition of Done)

1. Frontend: `npm run build` và `npm run lint` không lỗi; không có `any` mới; không import `sampleJobs` trong trang chạy online.
2. Backend: `pytest backend/tests` xanh trong container; Swagger `/docs` hiển thị đúng endpoint ở 3.4.
3. Hai luồng end-to-end chạy bằng `docker compose up` trên máy sạch:
   - **Ứng viên:** đăng ký → tải CV (`public/cv-mau.pdf`) → xác nhận kỹ năng → xem việc gợi ý + điểm + giải thích → ứng tuyển → thấy trạng thái.
   - **Nhà tuyển dụng:** đăng nhập → đăng tin (gợi ý kỹ năng) → xem ứng viên xếp hạng → đổi trạng thái (thử nhảy cóc để thấy 409) → dashboard cập nhật số phễu.
4. `VITE_OFFLINE_DEMO=true npm run dev` vẫn chạy toàn bộ bản demo cũ.
5. Không commit mật khẩu, `.env`, dữ liệu cá nhân thật. Tên trong dữ liệu seed là hư cấu.

## 7. Quy tắc làm việc

- Tùng chạy `git init` + tạo repo GitHub; nhánh `main` bảo vệ; mỗi người một nhánh `feat/<tên>-<việc>`; PR vào `main`. Tùng duyệt PR AI/backend lõi; Thái Anh duyệt PR frontend.
- 22:00 mỗi tối nhắn nhóm 3 dòng: đã xong / đang vướng / mai làm gì.
- Trễ bàn giao quá 12 giờ → Tùng chuyển việc hoặc cắt phạm vi theo bảng rủi ro.
- Sau 16:00 05/11 không thêm tính năng.

## 8. Rủi ro và phương án (cập nhật theo repo)

| Rủi ro | Phương án |
|---|---|
| Nhúng Superset lỗi CORS/iframe/guest token | Dùng 3 biểu đồ Recharts (đã có `recharts` trong `package.json`) đọc `/api/bi/*`; vẫn nộp `dashboard_export.zip` |
| Cài `torch`/`sentence-transformers` chậm hoặc nặng | Dùng wheel CPU; tải model ở bước build image; `HF_HUB_OFFLINE=1` khi chạy |
| Python 3.13 trên máy cá nhân gây lỗi wheel | Chỉ chạy backend/test trong Docker 3.11 |
| Thiếu thời gian gán nhãn | Giảm còn 20 ứng viên × 10 tin = 200 cặp, ghi rõ trong báo cáo |
| M4 không hơn M3 | Vẫn báo cáo trung thực; giữ M3 làm `DEFAULT_MODEL` |
| Backend không chạy được ở buổi demo | `VITE_OFFLINE_DEMO=true` + video quay sẵn |
| CRLF làm hỏng script trong container | `.gitattributes` `eol=lf`; chạy `git add --renormalize .` |
| Tin cũ có kỹ năng "A hoặc B" | Chuyển thành hai kỹ năng ưu tiên ở dữ liệu seed; M0 Python vẫn port `hasSkill` để test song song với TS |

## 9. Video nộp bài (đề chỉ nhận video)

- Kịch bản 6–8 phút theo thứ tự 01 → 05: ERD + seed → parser/bảng so sánh M0–M4 → dashboard → 2 luồng end-to-end → bảng kiểm thử + kết luận.
- Quay 1080p, xuất MP4 (H.264), nén bằng HandBrake/ffmpeg: `ffmpeg -i in.mp4 -vcodec libx264 -crf 28 -b:a 96k out.mp4` cho tới khi **< 100 MB**.
- Đặt link repo và báo cáo ở mô tả/cuối video và hỏi giảng viên có kênh nộp thêm tài liệu không.
