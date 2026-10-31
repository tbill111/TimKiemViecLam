# Đánh giá theo chuẩn checklist TH3 (cuối phiên, nhánh `feat/full-system`)

Căn cứ là những gì đã **chạy thật**, không chỉ viết mã:

| Kiểm chứng | Kết quả |
|---|---|
| `cd backend && python -m pytest` | 231 passed |
| Cùng bộ test trong container với model embedding thật (`EMBEDDER=st`) | 223 passed, 2 skipped (thiếu file ngoài image) |
| `npx tsc -b`, `npm run build` (online và demo) | sạch |
| `npm run lint` | exit 0, 8 cảnh báo, 0 lỗi |
| E2E trình duyệt trên **stack Docker thật** (nginx → API + model thật → PostgreSQL 16 → Superset 4.1.1 nhúng) | **14/14** bước: ứng viên, nhà tuyển dụng, quản trị |
| E2E chế độ demo không backend | 12/12 bước, 0 lời gọi API |
| 4 view BI trên PostgreSQL thật so với `/api/bi/*` (`scripts/check_bi_views.py`) | khớp mọi số liệu; `bi_reader` chỉ đọc được view |
| Guest token Superset thật + RLS | công ty 1 thấy 19 hồ sơ, công ty 5 thấy 63, admin thấy 1.255, khớp API |
| Hiệu năng qua HTTP (PostgreSQL + model thật) | 1 cặp 38 ms; 150 tin 38 ms; 500 tin 70–77 ms (mục tiêu 200 ms và 2 s) |

## Đánh giá từng mục

| Mục | Mức đạt chuẩn | Căn cứ | Còn thiếu để nộp |
|---|---|---|---|
| **01** Phân tích yêu cầu, thiết kế CSDL (ứng viên, nhà tuyển dụng, tin) | **Đạt** về nội dung và kiểm chứng | F01–F10 + phi chức năng; Use Case + đặc tả 3 ca; ERD 15 bảng/5 nhóm sinh từ models; `schema.sql`; migration 0001–0003 chạy trên PostgreSQL thật, gồm nâng cấp CSDL cũ tại chỗ; seed 108 kỹ năng, 259 alias, 30 công ty, 150 tin, 301 ứng viên, 50 CV | Xuất ảnh PNG Use Case (PlantUML) và ERD (dbdiagram.io) |
| **02** Mô hình AI/ML phân tích CV, tính điểm tương thích | **Đạt về mã và kiểm chứng; chưa đủ chuẩn nộp** | Parser 3 tầng, 6 đặc trưng, M0–M4, giải thích; M0 khớp TypeScript 100%; chạy với model thật (cosine Việt–Anh 0,847); đo công bằng; 38 ms/cặp | **Nhãn tay** (50 CV, 300 cặp), `m4.joblib` và bảng đánh giá thật. Chỉ có kết quả trên đáp án *tổng hợp* (F1 parser 0,98) |
| **03** Dashboard BI (ứng viên theo kỹ năng, xu hướng lương, tỷ lệ chuyển đổi) | **Đạt** | 3 biểu đồ bắt buộc (2, 4, 6) + 1, 1b, 3, 8; nhúng Superset thật trong ứng dụng; RLS theo công ty đã kiểm; `dashboard_export.zip` nhập lại được; ảnh; 4 nhận định có nêu giới hạn dữ liệu mô phỏng | Biểu đồ 5, 7 và Native Filters (mở rộng, thêm bằng giao diện) |
| **04** Frontend và tích hợp API AI/BI | **Đạt** | Đăng nhập/đăng ký và phân quyền; tìm việc, Phân tích CV–JD (M0–M4), Skill Gap, tải CV, ứng tuyển; đăng tin có gợi ý kỹ năng; Kanban 6 cột; dashboard nhúng; **quản trị danh mục kỹ năng (F10) có giao diện**; chế độ demo; Docker Compose chạy thật | — |
| **05** Kiểm thử với dữ liệu mẫu, báo cáo đánh giá mô hình | **Một phần** | 231 test; 44 test case (ca đã chạy ghi Đạt, ca chưa chạy ghi rõ); E2E; đo hiệu năng; notebook, kappa, ablation, script chọn 300 cặp, hướng dẫn gán nhãn | Hai file nhãn độc lập; chạy notebook trên nhãn thật; báo cáo cuối; video |

## Phần phải do người làm (không thể thay bằng mã)

| Người | Việc |
|---|---|
| **Hoàng Hưng, Hoàng Anh** | Gán nhãn độc lập 300 cặp (`labels_pairs_hung.csv`, `labels_pairs_hoanganh.csv`); Hoàng Anh gán nhãn kỹ năng 50 CV (`labels_cv_skills.csv`); kiểm thử thủ công các ca còn ghi "Chưa kiểm"; xuất PNG Use Case/ERD |
| **Tùng** | Chạy 3 notebook trong container với nhãn thật (`EMBEDDER=st`), huấn luyện M4, quyết định `UPDATE_M3`; viết chương AI; quay video |
| **Cả nhóm** | Ghép báo cáo từ `docs/report/BaoCao_TH3_khung.md`; thay mật khẩu/khoá trong `.env` nếu triển khai ngoài máy cá nhân |

## Sai sót mà lần chạy thật phát hiện và đã sửa (không lộ ra ở test dùng SQLite hay dữ liệu giả)

| Phát hiện khi | Lỗi | Sửa |
|---|---|---|
| Chạy Alembic trên PostgreSQL | Dấu `;` trong một dòng chú thích làm migration tách sai câu lệnh | Bỏ chú thích trước khi tách + test hồi quy |
| Dựng Superset | Thiếu gói `flask-cors`; cổng 8088 trùng dự án khác | Thêm gói; `SUPERSET_PORT` cấu hình được |
| Dựng dashboard qua API | Superset 4.1 cần phiên đăng nhập (cookie) cho một số API ghi | `bootstrap.py` đăng nhập cả hai kiểu |
| Đo bằng model thật | Chấm 1 cặp 417 ms (> 200 ms) vì hồ sơ chưa có CV bị mã hoá lại mỗi yêu cầu | Thêm `candidates.embedding` tính khi lưu (migration 0003): 38 ms |
| Chọn M1 | TF-IDF chỉ fit trên hai văn bản nên điểm vô nghĩa | Fit trên các tin đang mở |
| Chạy nạp seed hai lần cùng lúc | DB nửa vời (có tin, không có đơn) và không tự nạp lại | Nạp trong một giao dịch + khoá cố vấn PostgreSQL |
| Chạy trên trình duyệt thật | Modal ứng tuyển ghi "Demo" khi online; nút đóng không có tên truy cập, không đóng bằng Esc; chọn M4 làm mất trang; chữ cái avatar không viết hoa; lưu hồ sơ lỗi giữ giá trị chưa lưu | Sửa từng điểm |

## Rủi ro còn lại so với đề

1. Phần "ML" thật chỉ có ở M4 (xếp hạng); trích kỹ năng CV chủ yếu là từ điển + so khớp mờ + embedding. Trên bộ CV tổng hợp, tầng 2–3 chưa cải thiện F1 (0,981 → 0,979); cần nhãn tay để kết luận trung thực.
2. Dữ liệu ứng tuyển và lương là mô phỏng; mọi nhận định BI chỉ minh hoạ cách tính.
3. Đề chỉ nhận **video** MP4/… ≤ 101 MB, nộp một lần: cần kịch bản theo thứ tự 01 → 05 và hỏi giảng viên kênh nộp báo cáo.
