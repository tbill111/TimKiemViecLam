# Đánh giá trạng thái checklist TH3 (nhánh `fix/main-chuan-checklist`, 06/11/2026)

Căn cứ: mã và kết quả chạy thật trên nhánh này (stack Docker Compose dựng từ nhánh, PostgreSQL 16, model embedding thật). Chỉ ghi "Đạt" khi đã chạy; chỗ chưa làm được ghi rõ ở cột "Còn thiếu".

## 1. Trạng thái từng mục

| Mục | Yêu cầu đề | Đã có (bằng chứng) | Còn thiếu / hạn chế | Mức |
|---|---|---|---|---|
| **01** | Phân tích yêu cầu, thiết kế CSDL cho ứng viên, nhà tuyển dụng, tin | Yêu cầu F01–F10, Use Case, ERD 15 bảng (`docs/report/01_phan_tich_yeu_cau.md`, `chuong_csdl_kien_truc_api.md`); migration 0001–0007 chạy trên CSDL trống (test `test_migrations_clean_db.py`, upgrade/downgrade/upgrade); seed 300 ứng viên, 150 tin, 1.200 đơn, 50 file CV | Không có | Đạt |
| **02** | Mô hình AI/ML phân tích CV và tính điểm tương thích | Parser CV 3 tầng (P/R/F1 = 0,989 trên 50 CV); 6 đặc trưng; M0–M6 (M4–M6 huấn luyện bằng GroupKFold, lưu `models_store/*.joblib`); API AI; 300 cặp và 50 CV có nhãn; bảng so sánh, bootstrap, ablation (`chuong_ai.md`, `docs/report/tables/`) | Nhãn do **agent AI** gán (kappa 0,934), chưa có nhãn của người; chỉ 30 ứng viên; học máy không vượt M3 | Đạt (kèm hạn chế) |
| **03** | Dashboard BI: số ứng viên theo kỹ năng, xu hướng lương, tỷ lệ chuyển đổi | Superset dựng tự động (`bi/superset/bootstrap.py`, `dashboard_export.zip`), 8 biểu đồ và 4 Native Filter trên 4 view, nhúng bằng guest token, RLS theo công ty, `docker compose up` tự dựng qua dịch vụ `bi-init`; `check_bi_views.py` 4/4 view khớp API; ảnh `ui_11_dashboard_bi.png` | Chưa có biểu đồ 8 và bộ lọc thời gian; dữ liệu ứng tuyển và lương là mô phỏng | Đạt (thiếu phần phụ) |
| **04** | Frontend và tích hợp API AI/BI | 12 màn hình qua API thật (`chuong_giao_dien.md`); chọn mô hình M0–M6; Skill Gap, xếp hạng ứng viên, Kanban, dashboard nhúng; chế độ demo không backend; e2e trình duyệt online 16/16 và offline 19/19 | — | Đạt |
| **05** | Kiểm thử với dữ liệu mẫu và báo cáo đánh giá mô hình | pytest **210 passed**; 33 ca trong `docs/testcases.md` (kết quả thật từng ca); `run_testcases.py` 10/10; báo cáo `BaoCao_TH3.md` và các chương; đo hiệu năng qua HTTP | Video và slide chưa làm trong nhánh này (xem mục 3) | Đạt (trừ video) |

## 2. Lỗi của `main` đã sửa trên nhánh này

1. `alembic upgrade head` lỗi `DuplicateTable` trên CSDL trống (0001 dùng `create_all` trên metadata hiện tại rồi 0003 tạo lại `labeling_tasks`); `docker compose up` trên máy sạch không chạy được. Đã sửa và có test.
2. `match_results` có ràng buộc chỉ cho m0–m4: gọi `/ai/match` với M5/M6 làm API lỗi. Thêm migration 0007 và test.
3. Seed lỗi `uq_candidate_skills` khi có CV (kỹ năng đề xuất trùng kỹ năng đã có). Sửa upsert, có test.
4. Chưa có CV, nhãn, M4–M6, dashboard Superset, số liệu đánh giá: đã bổ sung.
5. Dashboard nhúng bị 403 (role `Public` của Superset chưa có quyền đọc) và khung iframe quá thấp nên không thấy biểu đồ: thêm `PUBLIC_ROLE_LIKE = "Gamma"`, tăng chiều cao khung, ẩn thanh lọc trống.
6. Trang "Phân tích CV–JD": ghi chú cũ nói "không phải mô hình AI thật" và danh sách bên trái hiển thị điểm khác điểm chi tiết; đã sửa cho cùng nguồn M3.
7. Mở tin trước khi có điểm khớp gây trang trắng ở trang Tìm việc: đã sửa.

## 3. Rủi ro và việc còn lại (trung thực)

| # | Nội dung | Xử lý |
|---|---|---|
| 1 | Đề chỉ nhận **video** MP4/MOV/MKV/AVI/WEBM ≤ 101 MB, nộp 1 lần, hạn 08/11/2026 06:28. Video chưa được quay | Quay theo kịch bản 01 → 05 trên stack của nhánh này; ghi link repo trong mô tả |
| 2 | Nhãn do agent AI gán, không phải người | Nêu rõ trong báo cáo (mục 7 của `BaoCao_TH3.md`); nếu có thời gian nhờ một thành viên gán lại 60 cặp để đối chiếu |
| 3 | Superset chưa có biểu đồ 8 và bộ lọc thời gian | Không bắt buộc (đề cần 3 chỉ số, đã có); thêm bằng giao diện rồi xuất lại zip |
| 4 | Dữ liệu ứng tuyển và lương là mô phỏng | Đã ghi trên giao diện và báo cáo; không kết luận hiệu quả mô hình từ dữ liệu này |
| 5 | docx/pptx dựng bằng `scripts/build_report_files.py` từ báo cáo | Mở và xem bằng mắt trước khi nộp |
