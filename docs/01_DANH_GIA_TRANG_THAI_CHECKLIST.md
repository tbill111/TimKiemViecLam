# Trạng thái checklist TH3 (cập nhật sau khi hoàn thiện mã toàn hệ thống, nhánh `feat/full-system`)

Mọi con số dưới đây lấy từ lần chạy thật gần nhất: `cd backend && python -m pytest` → **225 passed**; `npm run build` và `npx tsc -b` sạch (`npm run lint` chỉ có cảnh báo, không lỗi);
`scripts/e2e_smoke.py` → **10/10** bước trên trình duyệt thật; `scripts/e2e_offline.py` → **12/12** bước, 0 lời gọi API.

## 1. Từng mục checklist

| Mục | Yêu cầu đề | Đã có (có bằng chứng) | Còn thiếu / chưa kiểm chứng |
|---|---|---|---|
| **01** | Phân tích yêu cầu, thiết kế CSDL cho ứng viên, nhà tuyển dụng, tin | Yêu cầu F01–F10 + phi chức năng; Use Case (PlantUML) + đặc tả 3 ca; ERD DBML sinh từ models (15 bảng, 5 nhóm); `schema.sql`; Alembic chạy từ DB trống; seed 108 kỹ năng, 259 alias, 30 công ty, 150 tin, 301 ứng viên, 50 CV | Ảnh PNG của Use Case và ERD (cần dbdiagram.io / PlantUML); migration chưa chạy trên PostgreSQL thật |
| **02** | Mô hình AI/ML phân tích CV và tính điểm tương thích | CV parser (PDF/DOCX/TXT, 3 tầng); 6 đặc trưng; M0–M4; giải thích; M0 khớp TypeScript 100%; API AI nối DB; công cụ huấn luyện/đánh giá; 3 notebook | Chạy với model embedding thật; nhãn tay (50 CV, 300 cặp); `m4.joblib`; bảng P/R/F1 và M0–M4 trên nhãn thật |
| **03** | Dashboard BI: ứng viên theo kỹ năng, xu hướng lương, tỷ lệ chuyển đổi | 4 view SQL (cú pháp PostgreSQL đã kiểm); API `/bi/*` cùng định nghĩa chỉ số (có test số liệu tính tay); dashboard dự phòng Recharts chạy được (E2E); guest token + RLS theo công ty (test bằng Superset giả); cấu hình và hướng dẫn Superset | Chưa chạy view trên PostgreSQL thật; chưa dựng/nhúng Superset thật; file `dashboard_export.zip`, ảnh và nhận định |
| **04** | Frontend và tích hợp API AI/BI | Đăng nhập/đăng ký, chặn route theo vai trò; tìm việc, phân tích CV–JD (chọn M0–M4), Skill Gap, hồ sơ, tải CV qua API, ứng tuyển; đăng tin có gợi ý kỹ năng; Kanban 6 cột; dashboard; chế độ demo giữ nguyên; Dockerfile + nginx + Compose | `docker compose up` chưa chạy thử (máy dựng không có Docker) |
| **05** | Kiểm thử với dữ liệu mẫu và báo cáo đánh giá mô hình | 225 test tự động; 38 test case (ca đã chạy ghi Đạt, ca chưa chạy ghi rõ); đo hiệu năng (150 tin 45 ms, 500 tin 116 ms trên SQLite); notebook đánh giá; script chọn 300 cặp; hướng dẫn gán nhãn | Hai file nhãn độc lập và kappa; kết quả đánh giá thật; báo cáo cuối; video demo |

## 2. Phần còn lại của từng thành viên (mã đã sẵn, cần việc của người)

| Người | Việc còn lại |
|---|---|
| **Tùng** | Chạy 3 notebook trong Docker với model thật khi có nhãn; huấn luyện M4; kiểm tra `docker compose up`; quay video và viết chương AI |
| **Thái Anh** | Chạy `docker compose up --build` trên máy sạch và sửa lỗi môi trường; kiểm tra view trên PostgreSQL; dựng Superset thật, lấy UUID dashboard và id dataset (xem `bi/README.md`) |
| **Ngọc Anh** | Kiểm tra giao diện trên màn hình nhỏ và trình duyệt khác; chụp ảnh các trang cho báo cáo; bổ sung trang quản trị kỹ năng nếu muốn (hiện chỉ có API) |
| **Hoàng Hưng** | Gán nhãn 300 cặp (`labels_pairs_hung.csv`); dựng biểu đồ Superset theo bảng ở `bi/README.md`; xuất `dashboard_export.zip`, chụp ảnh, viết nhận định |
| **Hoàng Anh** | Gán nhãn kỹ năng 50 CV (`labels_cv_skills.csv`) và 300 cặp (`labels_pairs_hoanganh.csv`); chạy kiểm thử thủ công các ca ghi "Chưa kiểm"; xuất PNG Use Case/ERD; ghép báo cáo và slide |

Dữ liệu CV và đơn ứng tuyển do trình sinh tạo là mô phỏng. `backend/seed/data/cv_manifest.csv` là **đáp án tổng hợp**, không phải nhãn tay; bảng P/R/F1 báo cáo cho giảng viên phải dùng nhãn tay của Hoàng Anh.

## 3. Rủi ro còn lại so với đề TH3

| # | Rủi ro | Cách xử lý |
|---|---|---|
| 1 | Phần "ML" thật chỉ có ở M4 (xếp hạng); trích kỹ năng CV chủ yếu là từ điển + so khớp mờ + embedding | Trình bày parser là NLP lai, đo bằng P/R/F1 từng tầng; nhấn mạnh embedding và M4 |
| 2 | Chưa có model embedding thật và nhãn thật nên chưa có số liệu đánh giá để nộp | Hoàn tất bước trong mục 2 trước 05/11 |
| 3 | M4 huấn luyện trên ~300 cặp, ứng viên sinh từ mẫu nghề, có thể không hơn M3 | Báo cáo trung thực; M3 vẫn là mặc định |
| 4 | Superset nhúng và Docker Compose chưa chạy thử | Có phương án dự phòng Recharts (đã E2E) và chế độ demo (đã E2E) |
| 5 | Đề chỉ nhận **video** MP4/… ≤ 101 MB, nộp một lần | Quay video theo thứ tự 01 → 05; hỏi giảng viên kênh nộp báo cáo/link repo |
