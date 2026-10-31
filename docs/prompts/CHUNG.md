# Quy chuẩn chung của nhóm 3 – đọc trước khi làm (mọi thành viên)

> Mọi prompt `PROMPT_n_*.md` đều bắt đầu bằng "đọc file này". Khi file này khác `docs/00_KE_HOACH_KY_THUAT_TH3.md` thì **file này thắng**.
> Cập nhật theo trạng thái thật của `main` (đã có tầng AI của Tùng) và theo các lỗi thực tế đã gặp khi chạy hệ thống trên PostgreSQL, Docker, Superset và model embedding thật.

## 1. Đề bài TH3 (nguyên văn) và hạn

**TH3 – Xây dựng Hệ thống Tìm việc Thông minh tích hợp AI và BI.** Sinh viên thiết kế và phát triển một nền tảng kết nối tuyển dụng thông minh, dùng AI để tự động khớp kỹ năng ứng viên với yêu cầu công việc (Matching Score). Hệ thống cần tích hợp công cụ BI để phân tích xu hướng thị trường lao động và cung cấp báo cáo trực quan cho nhà tuyển dụng. Mục tiêu là tối ưu hóa quy trình tìm kiếm việc làm và nâng cao độ chính xác trong tuyển dụng.

Checklist (5 mục, đây là thứ được chấm):
1. Phân tích yêu cầu hệ thống và thiết kế cơ sở dữ liệu cho ứng viên, nhà tuyển dụng và tin tuyển dụng.
2. Xây dựng mô hình AI/Machine Learning để phân tích CV và tính toán điểm tương thích với mô tả công việc (JD).
3. Thiết kế Dashboard BI để trực quan hóa các chỉ số như: số lượng ứng viên theo kỹ năng, xu hướng lương và tỷ lệ chuyển đổi tuyển dụng.
4. Phát triển giao diện người dùng (Frontend) và tích hợp các API xử lý AI/BI vào hệ thống.
5. Kiểm thử hệ thống với tập dữ liệu mẫu và viết báo cáo đánh giá hiệu quả của mô hình gợi ý.

**Hạn nộp 08/11/2026 06:28, chỉ 1 lần, ân hạn 15 phút. Định dạng nộp chỉ là VIDEO (MP4/MOV/MKV/AVI/WEBM), tối đa 101 MB.** Nhóm nộp nội bộ trước 22:00 07/11; chốt code 16:00 05/11. Video phải cho thấy cả 5 mục theo thứ tự 01 → 05 (`docs/video_kich_ban.md` do Tùng soạn).

## 2. "Đúng chuẩn" nghĩa là gì – bằng chứng bắt buộc cho từng mục

| Mục | Phải có (bằng chứng kiểm được) | Người chính |
|---|---|---|
| **01** | Bảng yêu cầu F01–F10 + phi chức năng; Use Case có 4 tác nhân, 10 use case, `<<include>>` đúng, đặc tả 3 ca; ERD đủ 15 bảng và thấy rõ ba đối tượng ứng viên / nhà tuyển dụng / tin tuyển dụng; migration chạy từ **PostgreSQL trống**; seed: ≥ 80 kỹ năng, ≥ 150 alias, 30 công ty, 150 tin rải đều 12 tháng đủ 5 cấp bậc, 300 ứng viên, 50 CV PDF/DOCX, ~1.200 đơn có lịch sử trạng thái | Hoàng Anh, Thái Anh, Hoàng Hưng |
| **02** | Parser đọc PDF/DOCX/TXT, trích kỹ năng 3 tầng, năm kinh nghiệm, học vấn, **đo P/R/F1 từng tầng trên 50 CV có nhãn (agent AI gán)**; 5 model M0–M4 cùng giao diện; M0 Python khớp bản TypeScript 100%; mọi điểm có 6 thành phần + kỹ năng thiếu + câu giải thích; M4 huấn luyện bằng **nhãn đã gán (agent AI)** với GroupKFold theo ứng viên; kiểm tra công bằng (đổi tên/giới tính CV → điểm không đổi); **chấm 1 cặp < 200 ms, gợi ý trên 500 tin < 2 s đo qua HTTP trên PostgreSQL + model thật** | Tùng, Thái Anh |
| **03** | 4 view SQL (`v_skill_supply_demand`, `v_salary`, `v_funnel`, `v_funnel_stages`); dashboard có biểu đồ **2, 4, 6 (bắt buộc)** + ≥ 2 biểu đồ mở rộng; **số trên dashboard = số API = truy vấn tay**; nhúng được trong trang nhà tuyển dụng; mỗi công ty chỉ thấy số của mình (RLS); file xuất `.zip` nhập lại được; ảnh + 3–4 nhận định; nói rõ dữ liệu là mô phỏng | Thái Anh, Hoàng Hưng |
| **04** | Đăng nhập/đăng ký + chặn route theo vai trò; ứng viên: tìm việc có điểm, tải CV → xác nhận kỹ năng, phân tích CV–JD (chọn M0–M4), Skill Gap, ứng tuyển, theo dõi trạng thái (chỉ đọc); nhà tuyển dụng: đăng tin có gợi ý kỹ năng, Kanban 6 cột, dashboard; quản trị: quản lý kỹ năng; mọi trang có trạng thái tải/lỗi/rỗng; `docker compose up` chạy cả hệ thống; chế độ demo không backend vẫn chạy | Ngọc Anh, Thái Anh |
| **05** | 300 cặp CV–JD **hai lượt gán nhãn độc lập (hai phiên agent AI riêng biệt)**, kappa có trọng số bình phương ≥ 0,6; bảng M0–M4 (P@5, nDCG@10, MRR, Spearman, ROC-AUC, ms/cặp); ablation M3; hệ số M4; 5 cặp sai nhiều nhất; ≥ 25 test case thủ công (kết quả thực tế chỉ điền khi đã chạy); pytest; đo hiệu năng; báo cáo 7 chương; video | Tùng, Hoàng Hưng, Hoàng Anh |

## 3. Quy tắc cứng (vi phạm là làm hỏng cả bài)

1. **Không bịa số liệu, không giấu nguồn nhãn.** Nhãn 300 cặp và 50 CV do **agent AI** gán (không cần người gán tay). Quy tắc trung thực: (a) báo cáo và slide ghi rõ "nhãn do agent AI gán", không viết "do thành viên gán"; (b) hai lượt gán là hai phiên agent **riêng biệt**, mỗi phiên chỉ được nhận file mẫu + `huong_dan_gan_nhan.md`, **không** được xem điểm hệ thống, kết quả parser hay nhãn của phiên kia; (c) kappa giữa hai lượt chỉ phản ánh độ nhất quán của agent, không phải độ tin cậy như người gán; (d) kết luận về mô hình ghi kèm hạn chế này. Mọi con số trong báo cáo lấy từ file kết quả do notebook/script sinh; chưa có thì ghi `TODO`.
2. **Dữ liệu là mô phỏng thì nói rõ là mô phỏng.** Đơn ứng tuyển và lịch sử trạng thái sinh ngẫu nhiên không phụ thuộc điểm khớp, nên biểu đồ "tỷ lệ tuyển theo nhóm điểm" chỉ minh hoạ cách tính. Hiệu quả mô hình chỉ kết luận từ nhãn tay. Không thu thập dữ liệu từ TopCV/LinkedIn.
3. **Không tuyên bố "đã chạy" nếu chưa chạy.** Chỉ ghi Đạt vào test case/bảng nghiệm thu khi đã thực sự chạy và thấy kết quả.
4. Git: mỗi người một nhánh `feat/<tên>-<việc>` tách từ `main`, mở Pull Request vào `main`. Tùng duyệt PR AI/backend lõi; Thái Anh duyệt PR frontend. **Không thêm dòng `Co-Authored-By: Claude` (hay bất kỳ attribution AI nào) vào commit và PR** – nhóm trưởng yêu cầu. Không commit `.env`, mật khẩu thật, dữ liệu cá nhân thật.
5. Backend chạy trong Docker `python:3.11-slim` (máy dev Python 3.13 hay lỗi torch/underthesea). Test pytest bằng SQLite **không đủ**: mọi thứ liên quan PostgreSQL, Docker, Superset phải chạy thật trong Docker.
6. Frontend TypeScript: `erasableSyntaxOnly` (cấm `enum`, `namespace`, parameter properties), `verbatimModuleSyntax` (dùng `import type`), `noUnusedLocals`. Mỗi cụm việc phải qua `npm run build` và `npm run lint` (không lỗi).
7. Nếu một mốc trong lịch đã trôi khi bạn đọc: **làm bù ngay và nhắn nhóm** – đừng im lặng. Trễ bàn giao quá 12 giờ thì Tùng chuyển việc hoặc cắt phạm vi.
8. Mỗi tối 22:00 nhắn nhóm 3 dòng: đã xong / đang vướng / mai làm gì.

## 4. Hợp đồng kỹ thuật (tóm tắt; chi tiết ở `docs/00_KE_HOACH_KY_THUAT_TH3.md` mục 3)

**Đã có sẵn trên `main` (Tùng, 167 test xanh – chạy `cd backend && python -m pytest`):** `backend/app/ai/*` (parser, 3 tầng trích kỹ năng, 6 đặc trưng, M0–M4, giải thích, metrics, train, evaluate, `AIRepository`), `backend/app/routers/ai.py` và `resumes.py`, 3 notebook trong `notebooks/`, `backend/seed/make_pair_list.py`, CSV mẫu 3 dòng, `backend/README_AI.md`, `backend/seed/README.md` (định dạng cột và quy ước giá trị – **chuẩn cho mọi file dữ liệu**). **Chưa có:** `app/main.py`, models, auth, các router còn lại, Alembic, seed đầy đủ, BI, docker-compose, giao diện nối API, tài liệu mục 01, nhãn, báo cáo.

**CSDL – 15 bảng:** `users, locations, skills, skill_aliases, companies, candidates, resumes, candidate_skills, recruiters, jobs, job_skills, applications, application_status_history, match_results, saved_jobs`. Bổ sung so với kế hoạch gốc: `jobs.category`, `jobs.responsibilities` (JSON), `candidates.profile_json` (JSON), `skills.learning_steps` (JSON), `application_status_history.note`, và cột `embedding` (BYTEA, float32×384) ở **`resumes`, `jobs`, `candidates`** (lý do ở mục 6, bẫy 3). Lương lưu số (triệu VNĐ/tháng), `NULL` = thoả thuận. Giờ lưu UTC không múi giờ.

**Trạng thái đơn (6 giá trị):** `applied → screening → interview → offer → hired`; từ bất kỳ trạng thái chưa kết thúc sang `rejected`; `hired`/`rejected` là cuối. Sai luật → HTTP **409** `{"detail":{"detail":"invalid_transition","from":..,"to":..}}`. Nhãn tiếng Việt ở frontend: Đã ứng tuyển / Đang xem xét / Phỏng vấn / Đề nghị / Đã tuyển / Từ chối. Mỗi lần đổi ghi 1 dòng lịch sử; lúc nộp ghi dòng `NULL → applied`.

**API (tiền tố `/api`):**

| Nhóm | Endpoint | Vai trò |
|---|---|---|
| Auth | `POST /auth/register` (role candidate/recruiter; recruiter bắt buộc `company_name`; không tự đăng ký admin), `POST /auth/login`, `GET /auth/me` | công khai / mọi vai trò |
| Hồ sơ | `GET/PUT/DELETE /candidates/me` (camelCase như `StudentProfile` + `consent`), `GET/PUT /candidates/me/skills` (PUT = toàn bộ tập kỹ năng đã xác nhận, trả `unresolved`) | candidate |
| CV | `POST /resumes/upload` (multipart `file`, `consent`); lỗi: 400 `consent_required`, 415 `unsupported_type`, 413 `too_large` (> 5 MB), 422 `no_text`/`corrupt` | candidate |
| Tin | `GET /jobs` (lọc `q, location, work_type, experience, category, sort, mine, page, page_size`; candidate nhận thêm `match`), `GET /jobs/{id}`, `POST/PUT/DELETE /jobs` (DELETE = đóng tin), `GET /locations`, `GET /skills` | mọi / recruiter chủ tin |
| AI | `POST /ai/match` `{job_id, model, candidate_id?}`, `GET /candidates/me/matches`, `/recommendations`, `/skill-gap`, `GET /jobs/{id}/ranked-candidates`, `POST /ai/extract-skills` | đã có ở `routers/ai.py` |
| Ứng tuyển | `POST /applications` (lưu `match_score`; trùng 409 `already_applied`; tin đóng 409 `job_closed`), `GET /applications/me`, `GET /jobs/{id}/applications`, `PATCH /applications/{id}/status` (403 nếu khác công ty), `POST/DELETE/GET /saved-jobs` | candidate / recruiter |
| BI | `GET /bi/summary`, `/bi/skills`, `/bi/salary`, `/bi/funnel` (recruiter chỉ thấy công ty mình), `GET /bi/guest-token` | recruiter, admin |
| Quản trị | `GET/POST /admin/skills`, `PUT /admin/skills/{id}` (nhóm + lộ trình), `GET/POST /admin/skill-aliases`, `DELETE /admin/skill-aliases/{alias}` | admin |

**`MatchDTO`** (một dạng cho mọi model): `{model, model_version, total_score (int 0–100), components{skill_req, skill_pref, semantic, exp, edu, pref} (M0: semantic/exp/edu = null), matched_required, missing_required, matched_preferred, missing_preferred, location_match, work_type_match, explanation}`. `m4` chưa có `models_store/m4.joblib` → **503 `model_not_trained`**; giao diện phải báo lỗi tại chỗ, không được làm mất cả trang.

**Dữ liệu và nhãn:** định dạng cột, enum, thang học vấn 0–4, mã ngoài của file nhãn nằm ở `backend/seed/README.md`. Kỹ năng trong CSV phải trùng đúng tên chuẩn trong `skills.csv` và chỉ là kỹ năng đơn (không `A hoặc B`). Danh mục khởi tạo: tên kỹ năng đang dùng ở `src/data/` (75 kỹ năng) là bắt buộc phải có trong `skills.csv`.

## 5. Lịch và bàn giao (từ `00_KE_HOACH_KY_THUAT_TH3.md` mục 5)

Chốt code **16:00 05/11**; viết xong phần báo cáo 12:00 06/11 (Tùng 18:00); video dựng xong 22:00 06/11; nộp nội bộ 22:00 07/11. Các điểm bàn giao then chốt (ai chờ ai):

| Hạn | Giao → nhận | Bàn giao |
|---|---|---|
| 31/10 22:00 | Hưng → Thái Anh, Tùng | `skills.csv`, `skill_aliases.csv`, `occupation_templates.csv` |
| 01/11 18:00 | Hưng → Thái Anh | `companies.csv`, `jobs.csv` (150 tin) |
| 01/11 22:00 | Thái Anh → Tùng | 300 ứng viên trong DB + `candidates_generated.csv`; `SqlAIRepository` chạy được |
| 02/11 12:00 | Tùng → Hưng, Hoàng Anh | `labels_pairs_template.csv` (300 cặp) |
| 02/11 12:00 | Hưng → Hoàng Anh, Thái Anh | 50 file CV + `cv_manifest.csv` |
| 02/11 18:00 | Tùng → Ngọc Anh | API AI chạy trên Swagger |
| 02/11 22:00 | Thái Anh → Hưng | Superset chạy, nối 3–4 view |
| 03/11 12:00 | Hoàng Anh → Tùng | `labels_cv_skills.csv` |
| 03/11 18:00 | Thái Anh → Ngọc Anh | guest token + UUID dashboard |
| 03/11 22:00 | Hưng, Hoàng Anh → Tùng | hai file nhãn cặp (hai phiên agent AI độc lập) |
| 04/11 22:00 | Tùng | `m4.joblib` (nhãn do agent AI gán), bảng M0–M4, ablation |
| 05/11 16:00 | cả nhóm → Tùng | `main` chạy bằng `docker compose up` |

## 6. Bẫy kỹ thuật đã gặp khi chạy thật – đừng đạp lại

1. **SQL view trong migration:** nếu tách `bi/views.sql` theo `;` thì phải **bỏ chú thích `--` trước khi tách** (chú thích có thể chứa `;` làm hỏng câu lệnh). Khối `DO $$ … $$` chạy riêng. Test bằng SQLite không bắt được lỗi này: chạy `alembic upgrade head` trên PostgreSQL thật.
2. **Nạp seed:** làm trong **một giao dịch** (không `commit` giữa chừng) và dùng `pg_advisory_lock`; nếu không, hai tiến trình nạp cùng lúc (entrypoint và lệnh chạy tay) hoặc lỗi giữa chừng để lại DB "có tin, không có đơn" và lần sau tưởng đã nạp xong. `--reset` phải xoá view trước rồi tạo lại sau.
3. **Embedding phải tính sẵn khi lưu** (CV, tin, và hồ sơ ứng viên chưa có CV → cột `candidates.embedding`, cập nhật khi lưu hồ sơ/kỹ năng). Nếu để lúc chấm mới mã hoá thì 1 cặp tốn ~400 ms (đã đo), vượt yêu cầu 200 ms. Sau khi sửa: 38 ms/cặp, 70–77 ms cho 500 tin.
4. **M1 (TF-IDF) phải fit trên kho tin đang mở** (`scorers.fit_tfidf([j.text …])`); fit trên đúng hai văn bản của một cặp cho điểm vô nghĩa. Fit lại khi số tin đổi.
5. **Văn bản dùng chấm điểm = `parsed["model_text"]`** (đã bỏ phần đầu CV có tên, tuổi, liên hệ), không phải `parsed["text"]`; chỉ kỹ năng `confirmed = true` được tính vào hồ sơ.
6. **Phễu đếm "từng đạt"** từ `application_status_history`, không đếm theo trạng thái hiện tại (hồ sơ đã `hired` vẫn phải được đếm ở `interview`, `offer`).
7. **Superset 4.1.x:** image tự build cần `psycopg2-binary` **và `flask-cors`** (thiếu thì container chết khi bật CORS); DB metadata riêng `superset_meta`; kết nối dữ liệu bằng role `bi_reader` chỉ `SELECT` trên view; bật `EMBEDDED_SUPERSET`, `GUEST_TOKEN_JWT_SECRET`, `TALISMAN_ENABLED=False`, `HTTP_HEADERS={"X-Frame-Options":"ALLOWALL"}`; khai báo `allowed_domains` của dashboard nhúng (`http://localhost:8080`, `:5173`). Một số API ghi (tạo dashboard/chart) cần **đăng nhập form (cookie) cùng Bearer**; chỉ Bearer thì lỗi 500 `AnonymousUserMixin`. Cổng 8088 trên máy dev có thể đã bị dự án khác chiếm: cho cổng cấu hình được (`SUPERSET_PORT`), đừng dừng container của người khác.
8. **Guest token + RLS:** RLS áp **trên từng dataset có cột `company_id`** (`v_funnel` **và** `v_funnel_stages`). Recruiter mà chưa cấu hình id dataset RLS thì backend **từ chối cấp token (503)**, không cấp token không lọc. Kiểm bằng cách lấy token của hai công ty và gọi `/api/v1/chart/data`: mỗi bên phải ra đúng số của công ty mình, bằng `/api/bi/funnel`.
9. **Email demo:** thư viện kiểm tra email từ chối đuôi `.test`, `.example`; dùng `smartcareer.vn`, `example.edu.vn`.
10. **Docker Compose:** `docker compose up --build web` cũng build lại `api`; giữ `WITH_ST=1` trong `.env` kẻo image mất model embedding thật và âm thầm chạy bằng embedder thay thế (kết quả khác). Máy Windows: giữ LF cho file `.sh` (đã có `.gitattributes`).
11. **Giao diện:** modal có `role="dialog"`, nút đóng có tên truy cập ("Đóng") và đóng bằng Esc; chế độ online không được ghi "Demo/không gửi dữ liệu thật"; chọn M4 chưa huấn luyện hiện lỗi **tại chỗ**; ứng viên chỉ **xem** trạng thái đơn ở chế độ online; giờ API không có múi giờ → thêm `Z` trước khi hiển thị; lưu hồ sơ thất bại thì tải lại dữ liệu thật thay vì giữ giá trị chưa lưu.
12. **Chế độ demo** (`VITE_OFFLINE_DEMO=true`) phải chạy trọn mọi trang và **không gọi API nào**.
13. **M0 phải khớp 100% `calculateSkillMatch` của TypeScript** (xem `backend/tests/golden`); đừng "cải tiến" `hasSkill` ở một phía.
14. `cv_manifest.csv` (nếu có) là đáp án do trình sinh tạo, **không phải nhãn gán độc lập**; bảng P/R/F1 dùng `labels_cv_skills.csv` do agent AI gán từ việc đọc CV, ghi rõ nguồn nhãn.

## 7. Cổng kiểm tra cuối (cả nhóm cùng chạy trước 16:00 05/11)

```bash
cp .env.example .env        # WITH_ST=1
docker compose up -d --build
docker compose exec api python -m seed.load_seed --reset
cd backend && python -m pytest                      # xanh
cd .. && npm run build && npm run lint              # không lỗi
```

Kịch bản duyệt tay (mỗi bước phải qua, đây cũng là nội dung quay video):
1. Ứng viên đăng nhập → Tìm việc thấy điểm khớp và giải thích. 2. Hồ sơ → tải CV mẫu (tích đồng ý) → xác nhận kỹ năng. 3. Phân tích CV–JD: đổi M0/M3, thấy 6 thành phần; chọn M4 khi chưa huấn luyện → báo lỗi tại chỗ. 4. Skill Gap có lộ trình. 5. Ứng tuyển → thấy trạng thái (chỉ đọc). 6. Nhà tuyển dụng đăng nhập → Dashboard (nhúng Superset hoặc 3 biểu đồ dự phòng) đúng số của công ty. 7. Đăng tin có "Gợi ý kỹ năng". 8. Kanban: chuyển bước đúng luật; thử nhảy cóc để thấy lỗi 409. 9. Quản trị: thêm kỹ năng + alias → alias có hiệu lực ở "Gợi ý kỹ năng". 10. `VITE_OFFLINE_DEMO=true`: mọi trang chạy, không có lời gọi API.
