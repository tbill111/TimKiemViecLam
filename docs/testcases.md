# Bảng test case (≥ 25) theo F01–F10

**Cách đọc cột "Kết quả thực tế":** chỉ ghi *Đạt* khi test tự động hoặc kịch bản E2E tương ứng đã được chạy và xanh ở lần chạy gần nhất
(`cd backend && python -m pytest` → 231 passed; trong container có model thật `EMBEDDER=st` → 223 passed + 2 skipped do thiếu file ngoài image;
`scripts/e2e_smoke.py` → **14/14 bước trên stack Docker thật** (nginx → API + model thật → PostgreSQL 16 → Superset 4.1.1 nhúng);
`scripts/e2e_offline.py` → 12/12 bước, 0 lời gọi API).
Các ca ghi *Chưa kiểm* cần người kiểm thủ công hoặc dữ liệu chưa có (nhãn tay).
Hoàng Anh bổ sung kết quả thủ công và ảnh minh chứng vào cột cuối.

| Mã | Chức năng | Mô tả / bước | Dữ liệu vào | Kết quả mong đợi | Cách kiểm | Kết quả thực tế |
|---|---|---|---|---|---|---|
| TC01 | F01 | Đăng ký ứng viên hợp lệ rồi đăng nhập | email, mật khẩu ≥ 8 ký tự | 201 kèm token; đăng nhập (không phân biệt hoa thường email) lấy lại token; `/auth/me` đúng | `test_auth_profile::test_register_login_me` | Đạt |
| TC02 | F01 | Đăng ký trùng email | email đã tồn tại | 409 `email_taken` | `test_duplicate_email_and_bad_credentials` | Đạt |
| TC03 | F01 | Đăng nhập sai mật khẩu / email lạ | sai thông tin | 401 `invalid_credentials` | như TC02 | Đạt |
| TC04 | F01 | Đăng ký vai trò admin, mật khẩu ngắn, recruiter thiếu công ty | các payload sai | 422 cho cả ba | `test_validation_and_no_admin_registration` | Đạt |
| TC05 | F01 | Gọi API không token, token rác, sai vai trò | — | 401, 401, 403 | `test_protected_routes_need_token_and_role` | Đạt |
| TC06 | F02 | Lưu hồ sơ có kỹ năng `reactjs`, `Python cơ bản`, `Kỹ năng lạ` + đồng ý | PUT `/candidates/me` | kỹ năng chuẩn hoá `React`, `Python`; kỹ năng lạ bị bỏ; `consent=true`; hoàn thiện 100% | `test_profile_roundtrip_with_skills_and_consent` | Đạt |
| TC07 | F02 | Xóa hồ sơ | DELETE `/candidates/me` | 204; token cũ và đăng nhập đều thất bại; đơn ứng tuyển bị xóa theo | `test_delete_profile_removes_account` | Đạt |
| TC08 | F03 | Tải CV hợp lệ có đồng ý | `cv.txt` (có `Reactjs, HTML5, Javascrip…`) | kỹ năng đề xuất `React, HTML, CSS, JavaScript, Git` (alias và lỗi gõ được sửa); chưa tính vào hồ sơ tới khi xác nhận; học vấn = 3 | `test_ai_bi::test_upload_cv_suggests_skills_then_candidate_confirms`; E2E bước "tải CV mẫu" với `public/cv-mau.pdf` | Đạt |
| TC09 | F03 | Tải CV lỗi | thiếu đồng ý / `.exe` / rỗng / > 5 MB / PDF hỏng / recruiter | 400, 415, 422, 413, 422, 403 | `test_upload_requires_consent_and_validates_files` | Đạt |
| TC10 | F03 | Xác nhận/sửa kỹ năng | danh sách mới | thay toàn bộ tập kỹ năng; kỹ năng ngoài danh mục nằm ở `unresolved` | `test_confirm_skills_replaces_set_and_reports_unresolved` | Đạt |
| TC11 | F04 | Nhà tuyển dụng đăng tin hợp lệ | form đầy đủ | 201; công ty đúng; kỹ năng bắt buộc/ưu tiên đúng | `test_jobs_applications::test_recruiter_creates_job_and_dto_shape` | Đạt |
| TC12 | F04 | Đăng tin không hợp lệ | kỹ năng lạ; lương min > max; nhóm nghề sai; ứng viên đăng; chưa đăng nhập | 422, 422, 422, 403, 401 | `test_create_job_validations` | Đạt |
| TC13 | F04 | Công ty khác sửa/đóng tin | token HR công ty B | 403; công ty A sửa/đóng được; tin đóng biến mất khỏi danh sách công khai | `test_only_owner_company_can_edit_or_close` | Đạt |
| TC14 | F04 | Gợi ý kỹ năng từ mô tả | "Cần thành thạo reactjs, Git và hiểu Docker" | `React, Git, Docker`; ứng viên gọi → 403 | `test_extract_skills_for_job_description`; E2E bước "đăng tin" | Đạt |
| TC15 | F05 | Chấm điểm cặp hồ sơ–tin | model m0–m3 | điểm 0–100, 6 thành phần, kỹ năng có/thiếu, câu giải thích đúng mẫu | `test_match_and_recommendations_use_confirmed_skills`; E2E bước "Phân tích CV–JD" | Đạt |
| TC16 | F05 | Chọn M4 khi chưa huấn luyện | model m4 | 503 `model_not_trained`; giao diện báo lỗi tại chỗ, đổi lại M0 vẫn dùng được; sau khi có `m4.joblib` thì chấm được | cùng TC15; `test_m4_available_after_training`; E2E | Đạt |
| TC17 | F05 | M0 Python khớp bản TypeScript | 84 ca (7 hồ sơ × 12 tin) | khớp 100% | `backend/tests/golden/test_m0_parity.py` | Đạt |
| TC18 | F05 | Công bằng: đổi tên/giới tính ở phần đầu CV | hai CV chỉ khác phần đầu | cùng kỹ năng, năm KN, học vấn và điểm M3 | `tests/ai/test_evaluate::test_fairness_header_change_does_not_change_scores` | Đạt |
| TC19 | F06 | Gợi ý việc, sắp theo độ phù hợp | hồ sơ HTML/CSS/React | tin frontend lên đầu; `sort=newest` đổi thứ tự | `test_candidate_sees_match_and_relevance_sort` | Đạt |
| TC20 | F06 | Xếp hạng ứng viên của một tin | HR công ty A / B / ứng viên | chỉ ứng viên đã nộp; công ty B và ứng viên → 403; chấm ứng viên chưa nộp → 403 | `test_ranked_candidates_only_applicants_of_own_job` | Đạt |
| TC21 | F07 | Nộp đơn | job_id | 201, `match_score` được lưu, lịch sử có dòng `NULL → applied`; nộp lại 409 `already_applied`; tin đóng 409; recruiter nộp 403 | `test_apply_records_score_history_and_blocks_duplicates`, `test_cannot_apply_to_closed_job_or_as_recruiter` | Đạt |
| TC22 | F07 | Đổi trạng thái đúng luật và nhảy cóc | applied→screening→interview→offer→hired; nhảy sang interview/offer/hired/applied | 200 từng bước, lịch sử đủ 5 dòng; 409 cho 4 ca nhảy cóc | `test_status_flow_follows_funnel_and_logs_history`, `test_jumping_steps_returns_409` | Đạt |
| TC23 | F07 | Trạng thái cuối và từ chối | `rejected` từ bước giữa; đổi sau khi `rejected` | 200 khi từ chối; sau đó mọi thay đổi 409 | `test_final_states_cannot_change_and_reject_from_any_open_step` | Đạt |
| TC24 | F07 | Phân quyền đổi trạng thái | HR công ty khác; ứng viên; id không tồn tại | 403, 403, 404 | `test_other_company_and_candidates_cannot_change_status` | Đạt |
| TC25 | F08 | Skill Gap | hồ sơ có `HTML` | thiếu CSS, React (bắt buộc) trước, TypeScript, Git (ưu tiên) sau; có `jobs_demanding`; kỹ năng chưa có dữ liệu dùng lộ trình mặc định 3 bước | `test_skill_gap_with_default_learning_steps`; E2E bước Skill Gap | Đạt |
| TC26 | F09 | Phễu đếm "từng đạt" | 4 hồ sơ: hired, dừng ở offer, rớt ở interview, mới nộp | 4/3/3/2/1; chuyển đổi 0,75/1,0/0,667/0,5; tổng 0,25; trung vị 10 ngày; nhóm điểm đúng | `test_funnel_counts_ever_reached_not_current_status` | Đạt |
| TC27 | F09 | Lọc theo công ty | HR công ty B / admin / ứng viên | B thấy 0; admin thấy 4; ứng viên 403 | `test_funnel_is_scoped_to_company_but_admin_sees_all` | Đạt |
| TC28 | F09 | Guest token Superset | HR / admin; chưa cấu hình; thiếu dataset RLS | HR nhận RLS `company_id = <công ty>` trên cả hai dataset; admin không RLS; chưa cấu hình/thiếu RLS → 503 | `test_guest_token_*` (Superset giả bằng `httpx.MockTransport`) | Đạt (token) / Chưa kiểm với Superset thật |
| TC29 | F09 | Dashboard hiển thị khi chưa có Superset | HR đăng nhập | KPI + 3 biểu đồ dự phòng (kỹ năng, lương, phễu) | E2E bước "dashboard hiển thị 3 biểu đồ" | Đạt |
| TC30 | F10 | Quản trị danh mục | admin thêm kỹ năng, alias; trùng; alias tới kỹ năng lạ; ứng viên gọi | 201, 409, 404, 403 | `test_admin_skill_catalog` | Đạt |
| TC31 | NFR | Hiệu năng | 1 cặp; 150 và 500 tin | < 200 ms; < 2 s | `test_performance.py` (SQLite, embedder thay thế: 45 ms / 116 ms) và **đo qua HTTP trên PostgreSQL + model thật**: 1 cặp 38 ms (trung vị 58 ms), 150 tin 38 ms, 500 tin 70–77 ms, ngay sau khi lưu hồ sơ 20 ms | Đạt |
| TC32 | NFR | Chế độ demo không backend | `VITE_OFFLINE_DEMO=true` | 12 bước đều qua, 0 lời gọi API | `scripts/e2e_offline.py` | Đạt |
| TC33 | NFR | Migration và 15 bảng | Alembic `upgrade head` / `downgrade base` từ DB trống | đủ 15 bảng; gỡ sạch | `test_alembic_upgrade_creates_all_15_tables_and_downgrades` (SQLite) và chạy thật trên PostgreSQL 16 trong container `api` | Đạt |
| TC34 | Dữ liệu | Số lượng seed | — | ≥ 80 kỹ năng, ≥ 150 alias, 30 công ty, 150 tin, 301 ứng viên, 50 CV; phễu hợp lệ | `test_seed.py` | Đạt |
| TC35 | NFR | View BI trên PostgreSQL | `bi/views.sql` | chạy được và số khớp `/api/bi/*` | cú pháp `test_views_sql_parses_as_postgresql`; **chạy thật** `scripts/check_bi_views.py` | Đạt: 4 view tạo được; phễu, chuyển đổi tổng, trung vị time-to-hire, nhóm điểm, cung–cầu 108 kỹ năng, lương 51 nhóm tháng×cấp bậc, lọc theo công ty đều khớp API; `bi_reader` đọc được view, không đọc được bảng `users` |
| TC36 | NFR | `docker compose up` | `.env` từ `.env.example` | 4 dịch vụ chạy; đăng nhập được ở http://localhost:8080 | chạy thật trên Docker Desktop (WSL2) | Đạt (db, api có model thật, superset, web); cổng Superset đổi bằng `SUPERSET_PORT` khi 8088 bị chiếm |
| TC37 | F03/F05 | Model embedding thật | `EMBEDDER=st` trong container | nạp offline được; hiểu Việt–Anh | `Embedder: st:paraphrase-multilingual-MiniLM-L12-v2`, nạp 7,4 s; cosine câu Việt–Anh cùng nghĩa 0,847, khác nghĩa 0,036; bộ test AI/API đạt với model thật | Đạt (chưa có số liệu trên nhãn tay) |
| TC38 | F09 | Nhúng Superset thật + RLS | dashboard tạo bằng `bi/superset/bootstrap.py` | dashboard hiển thị trong trang; HR chỉ thấy dữ liệu công ty mình | E2E (iframe hiển thị 7 biểu đồ); gọi `/api/v1/chart/data` bằng guest token: HR công ty 1 → 19 hồ sơ, công ty 5 → 63, admin → 1255, khớp `/api/bi/funnel` | Đạt |
| TC39 | F10 | Giao diện quản trị kỹ năng | thêm kỹ năng, alias, lộ trình; xóa alias | alias mới có hiệu lực ở `/ai/extract-skills`, xóa thì hết hiệu lực | `scripts/e2e_smoke.py` (4 bước quản trị), `test_admin_can_edit_skill_and_delete_alias` | Đạt |
| TC40 | NFR | Nạp seed an toàn | lỗi giữa chừng; hai tiến trình `--reset` cùng lúc | không để dữ liệu nửa vời; tuần tự nhờ khoá cố vấn, kết quả 150 tin / 301 ứng viên / 1255 đơn | `test_seed_is_atomic_failure_midway_leaves_no_partial_data`; chạy thật trên PostgreSQL | Đạt |
| TC41 | NFR | Nâng cấp CSDL cũ | PostgreSQL đang có dữ liệu ở revision 0002 | `alembic upgrade head` thêm cột `candidates.embedding` mà không mất dữ liệu | chạy thật: `Running upgrade 0002 -> 0003` | Đạt |
| TC42 | F05 | Điểm khớp không mã hoá lại khi chấm | lưu hồ sơ rồi gọi match | embedding hồ sơ/tin lấy từ DB, không gọi encode | `test_profile_embedding_is_stored_on_save_and_scoring_does_not_re_encode` | Đạt |
| TC43 | F03 | Đánh giá parser trên nhãn tay | 50 CV + `labels_cv_skills.csv` | bảng P/R/F1 từng tầng | `notebooks/01_parser_eval.ipynb` | **Chưa kiểm** (chưa có nhãn tay). Trên đáp án *tổng hợp* với model thật: P/R/F1 T1 0,969/0,993/0,981; T1+2 0,963/0,996/0,979; T1+2+3 0,963/0,996/0,979; MAE năm KN 0 |
| TC44 | F05 | Đánh giá M0–M4 trên nhãn tay | 300 cặp, hai người gán | bảng P@5, nDCG@10, MRR, Spearman, AUC; huấn luyện M4 | `notebooks/02`, `03` | **Chưa kiểm** (chưa có nhãn tay) |
