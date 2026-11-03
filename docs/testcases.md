# Bảng test case (≥ 25) theo F01–F10

**Cách đọc cột "Kết quả thực tế".**
- **Đạt (tự động)**: ca đã được pytest kiểm và xanh. Lần chạy ghi nhận: `cd backend && TEST_DATABASE_URL=postgresql+psycopg://… python -m pytest tests` → **178 passed, 0 skipped** (PostgreSQL 16 tạm trong Docker; không có `TEST_DATABASE_URL` thì 11 test API tự bỏ qua và còn 167 passed, 1 skipped). Embedder dùng bản băm (`EMBEDDER=hash`), không phải model thật.
- **Chưa chạy**: ca cần thao tác trên giao diện hoặc stack Docker; người kiểm điền kết quả thật và ảnh minh chứng vào cột cuối, **không** ghi *Đạt* khi chưa chạy.

| Mã | F | Mô tả / bước | Dữ liệu vào | Kết quả mong đợi | Cách kiểm | Kết quả thực tế |
|---|---|---|---|---|---|---|
| TC01 | F01 | Đăng nhập đúng vai trò ứng viên, nhà tuyển dụng, admin | email + `Demo@12345` | 200, trả `access_token` và `user.role` đúng | Fixture đăng nhập của `tests/api` (mọi test dùng) và đăng nhập tay | Đạt (tự động, gián tiếp) |
| TC02 | F01 | Đăng nhập sai mật khẩu | mật khẩu sai | 401 | `test_login_rejects_wrong_password` | Đạt (tự động) |
| TC03 | F01 | Đăng ký admin; đăng ký recruiter thiếu tên công ty | `role=admin`; `role=recruiter` không `company_name` | 422; 400/422 chứa `company_name_required` | `test_register_blocks_admin_and_requires_company_for_recruiter` | Đạt (tự động) |
| TC04 | F01 | Ứng viên gọi API của admin | token ứng viên → `GET /admin/skills` | 403 | `test_role_guard_returns_403` | Đạt (tự động) |
| TC05 | F01 | Gọi API không token / token rác; mở `/employer/jobs` khi chưa đăng nhập | — | 401; giao diện chuyển về `/login` | Thủ công (Swagger + trình duyệt) | Chưa chạy |
| TC06 | F02 | Ứng viên đăng ký mới rồi lưu hồ sơ (học vấn, địa điểm, lương) | form hồ sơ | 200; tải lại trang vẫn còn dữ liệu | Thủ công trên `/profile` | Chưa chạy |
| TC07 | F02 | Xóa hồ sơ | `DELETE /candidates/me` | 204; đăng nhập lại bằng tài khoản đó thất bại; đơn ứng tuyển bị xóa theo | Thủ công (Swagger) | Chưa chạy |
| TC08 | F03 | Tải CV hợp lệ có đồng ý | `cv.txt` có mục Kỹ năng, Học vấn; `consent=true` | 200; đề xuất React, Git…; `education_level=3`; CV lưu kèm embedding và `consent` | `test_upload_requires_consent_and_maps_errors` (kho giả) | Đạt (tự động, kho giả); chưa chạy trên DB thật |
| TC09 | F03 | Tải CV lỗi | thiếu đồng ý; `.exe`; rỗng; PDF hỏng; > 5 MB; tài khoản recruiter | 400; 415; 422; 422; 413; 403 | `test_upload_requires_consent_and_maps_errors`, `test_resume_rejects_unsupported_extension`, `test_resume_over_5mb_returns_413`, `test_upload_forbidden_for_recruiter` | Đạt (tự động) |
| TC10 | F03 | Xác nhận/sửa kỹ năng sau khi tải CV | bỏ chọn 1 kỹ năng, thêm 1 kỹ năng | `PUT /candidates/me/skills` lưu đúng tập đã chọn; điểm khớp tính lại | Thủ công trên `/profile` | Chưa chạy |
| TC11 | F04 | Nhà tuyển dụng đăng tin hợp lệ | form đầy đủ, chọn kỹ năng bắt buộc/ưu tiên | 201; tin gắn đúng công ty; hiện trong `/employer/jobs` | Thủ công trên `/employer/jobs/new` | Chưa chạy |
| TC12 | F04 | Lọc và phân trang tin | `q=React&location=Hà Nội&category=Frontend Development&page_size=1` | `total=2`, 1 tin trên trang | `test_job_filter_and_pagination` | Đạt (tự động) |
| TC13 | F04 | Sửa tin; đóng tin (`DELETE /jobs/{id}`) | chủ tin / công ty khác | chủ tin: 200/204, tin đóng biến khỏi danh sách công khai; công ty khác 403 | Thủ công (Swagger) | Chưa chạy |
| TC14 | F04 | Gợi ý kỹ năng từ mô tả tin | "cần React và Docker" | `React`, `Docker`; ứng viên gọi → 403 | `test_extract_skills_recruiter_only`, `test_suggest_skills_for_jd` | Đạt (tự động) |
| TC15 | F05 | Chấm một cặp, mặc định M3 | `POST /ai/match {job_id}` | điểm 0–100, `components`, `missing_required`, câu giải thích có "Thiếu"; kết quả lưu `match_results` | `test_match_candidate_default_model_and_saved` | Đạt (tự động, kho giả) |
| TC16 | F05 | Đổi model; M4 khi chưa huấn luyện; model lạ | `model` = m0…m3 / m4 / zzz | 200 cho m0–m3; 503 `model_not_trained`; 422. Giao diện báo lỗi tại chỗ | `test_match_all_available_models`, `test_match_m4_not_trained_returns_503_and_bad_model_422`; giao diện: thủ công | Đạt (tự động); giao diện chưa chạy |
| TC17 | F05 | M0 Python khớp bản TypeScript | 84 ca (7 hồ sơ × 12 tin) | khớp 100% | `tests/golden/test_m0_parity.py` | Đạt (tự động) |
| TC18 | F05 | Công bằng: đổi tên/giới tính/tuổi ở phần đầu CV | hai CV chỉ khác phần đầu | cùng điểm | `test_fairness_header_change_does_not_change_scores` | Đạt (tự động) |
| TC19 | F06 | Gợi ý việc cho ứng viên | `GET /candidates/me/matches`, `/recommendations?top=1` | có điểm cho mọi tin mở; hồ sơ frontend → tin frontend đứng đầu | `test_matches_and_recommendations` | Đạt (tự động, kho giả) |
| TC20 | F06 | Xếp hạng ứng viên của một tin | ứng viên / recruiter công ty A / công ty B / admin | 403 / 200 chỉ ứng viên đã nộp / 403 / 200; chấm ứng viên chưa nộp → 403 | `test_ranked_candidates_permissions`, `test_recruiter_match_rules` | Đạt (tự động, kho giả) |
| TC21 | F07 | Nộp đơn; nộp lại cùng tin; `job_id` dạng chuỗi | `POST /applications` | 201; lần hai 409 `already_applied`; chuỗi `"<id>"` vẫn nhận | `test_application_duplicate_returns_409`, `test_apply_accepts_string_job_id` | Đạt (tự động) |
| TC22 | F07 | Đổi trạng thái nhảy cóc | `applied` → `interview` | 409 `{"detail":{"detail":"invalid_transition","from":"applied","to":"interview"}}` | `test_status_skip_returns_contract_409` | Đạt (tự động) |
| TC23 | F07 | Đi đủ luật `applied → screening → interview → offer → hired`; `rejected` từ bước giữa; đổi sau trạng thái cuối | recruiter chủ tin | 200 từng bước, `application_status_history` đủ dòng (dòng đầu `NULL → applied`); sau `hired`/`rejected` mọi đổi 409 | Thủ công trên `/employer/kanban` hoặc Swagger | Chưa chạy |
| TC24 | F07 | Recruiter công ty khác đổi trạng thái / xem đơn | token HR công ty B | 403 | `test_other_company_cannot_change_status`, `test_recruiter_cannot_view_other_company_applications` | Đạt (tự động) |
| TC25 | F08 | Skill Gap | hồ sơ thiếu React, TypeScript | React (bắt buộc) trước, TypeScript (ưu tiên) sau; có `jobs_demanding`; kỹ năng chưa có lộ trình dùng lộ trình mặc định 3 bước | `test_skill_gap_orders_required_first` | Đạt (tự động, kho giả) |
| TC26 | F09 | Dashboard BI hiển thị, số khớp truy vấn SQL tay | HR công ty có dữ liệu | KPI + biểu đồ (Superset hoặc Recharts dự phòng); số phễu khớp `bi/views.sql` | Thủ công (`scripts/check_bi_views.py` + trình duyệt) | Chưa chạy |
| TC27 | F09 | Chỉ thấy dữ liệu công ty mình | HR công ty A so với B; admin | số liệu phễu khác nhau theo công ty; admin thấy tất cả | Thủ công | Chưa chạy |
| TC28 | F09 | Guest token Superset | HR / admin | HR nhận RLS `company_id = <công ty>`; admin không RLS | Thủ công (cần Superset chạy) | Chưa chạy |
| TC29 | F10 | Quản trị danh mục | admin thêm kỹ năng, thêm/xóa alias | `reactjs` → React có hiệu lực ở `/ai/extract-skills`; xóa thì hết hiệu lực; ứng viên → 403 | Thủ công trên `/admin/skills` | Chưa chạy |
| TC30 | NFR | Hiệu năng | 1 cặp; 500 tin | < 200 ms; < 2 s | `test_performance_500_jobs_under_two_seconds` (dữ liệu tổng hợp, embedder băm); đo 1 cặp qua HTTP: chưa chạy | Đạt (tự động, 500 tin); 1 cặp chưa đo |
| TC31 | NFR | Chế độ demo không backend | `VITE_OFFLINE_DEMO=true npm run dev` | các màn ứng viên chạy bằng dữ liệu mẫu, không gọi API | Thủ công | Chưa chạy |
| TC32 | NFR | `docker compose up` trên máy sạch | `.env` từ `.env.example` | 4 dịch vụ chạy; vào được http://localhost:8080 và đăng nhập | Thủ công | Chưa chạy |
| TC33 | NFR | Parser CV: alias, lỗi gõ, năm kinh nghiệm, học vấn | các CV mẫu trong test | đúng kỳ vọng từng tầng | `tests/ai/test_extract.py`, `test_parser_text.py` | Đạt (tự động) |

Tổng: 33 ca; 20 ca đạt bằng kiểm thử tự động, 13 ca chưa chạy (cần giao diện hoặc Docker). Cập nhật cột cuối và số này sau khi chạy thủ công.
