# Đánh giá theo chuẩn checklist TH3 (nhánh `feat/full-system`)

Căn cứ là những gì đã **chạy thật**, không chỉ viết mã:

| Kiểm chứng | Kết quả |
|---|---|
| `cd backend && python -m pytest` | 247 passed |
| `npx tsc -b`, `npm run build` | sạch |
| `npm run lint` | 0 lỗi (chỉ cảnh báo) |
| E2E trình duyệt trên **stack Docker thật** (nginx → API + model thật → PostgreSQL 16 → Superset 4.1.1 nhúng), sau khi gán nhãn và huấn luyện lại M4 | **14/14** bước: ứng viên, nhà tuyển dụng, quản trị |
| E2E chế độ demo không backend | 12/12 bước, 0 lời gọi API |
| 4 view BI trên PostgreSQL thật so với `/api/bi/*` (`scripts/check_bi_views.py`) | khớp mọi số liệu; `bi_reader` chỉ đọc được view |
| Guest token Superset thật + RLS | công ty 1 thấy 19 hồ sơ, công ty 5 thấy 63, admin thấy 1.255, khớp API |
| Hiệu năng qua HTTP (PostgreSQL + model thật) | 1 cặp 38 ms; 150 tin 38 ms; 500 tin 70–77 ms (mục tiêu 200 ms và 2 s) |
| Đánh giá mô hình (3 notebook chạy với `Embedder: st:...`) | nhãn do **agent AI** gán: kappa 0,959; 7 mô hình M0–M6 (M4 Logistic Regression, M5 Random Forest, M6 Gradient Boosting cùng GroupKFold); M3 và M5 nDCG@10 ≈ 0,988–0,989, M0–M2 kém M3 có ý nghĩa thống kê, M4–M6 không khác M3 có ý nghĩa |

## Nguồn nhãn đánh giá (phải nói rõ khi nộp)

300 cặp CV–JD do hai phiên agent AI độc lập gán; kỹ năng 50 CV do một phiên agent AI khác gán (`backend/seed/labels/NGUON_NHAN.md`). **Không phải nhãn của con người.** Hai phiên cùng họ mô hình nên kappa cao phản ánh độ nhất quán của agent; agent dựa trên cùng loại thông tin mà M0–M4 dùng nên điểm các mô hình có xu hướng lạc quan. Báo cáo chương 6 đã ghi hạn chế này.

## Đánh giá từng mục

| Mục | Mức đạt chuẩn | Căn cứ | Còn thiếu / hạn chế |
|---|---|---|---|
| **01** Phân tích yêu cầu, thiết kế CSDL (ứng viên, nhà tuyển dụng, tin) | **Đạt** | F01–F10 + phi chức năng; Use Case 4 tác nhân/10 use case + đặc tả 3 ca (ảnh PNG); ERD 15 bảng/5 nhóm sinh từ models (PNG); `schema.sql`; migration 0001–0003 chạy trên PostgreSQL trống và nâng cấp tại chỗ; seed 108 kỹ năng, 259 alias, 30 công ty, 150 tin, 301 ứng viên, 50 CV, 1.255 đơn | — |
| **02** Mô hình AI/ML phân tích CV, tính điểm tương thích | **Đạt** về mã, quy trình, kiểm chứng và số liệu; số liệu mang hạn chế về nguồn nhãn | Parser 3 tầng; 6 đặc trưng; M0–M4; giải thích; M0 khớp TypeScript 100% (84 ca); công bằng (đổi tên/giới tính → cùng điểm 67); 38 ms/cặp; P/R/F1 từng tầng (F1 0,979 / 0,978 / 0,978), MAE năm KN 0,022; M4 huấn luyện GroupKFold theo ứng viên, `m4.joblib` (`m4-ai-labels`) | Nhãn do agent AI gán, chưa đối chiếu với con người; chỉ 30 ứng viên; tầng 2–3 không cải thiện F1; M4 không vượt M3 |
| **03** Dashboard BI (ứng viên theo kỹ năng, xu hướng lương, tỷ lệ chuyển đổi) | **Đạt** | Biểu đồ bắt buộc 2, 4, 6 + 1, 1b, 3, 8; nhúng Superset thật; RLS theo công ty đã kiểm; `dashboard_export.zip` nhập lại được; ảnh; 4 nhận định có nêu giới hạn dữ liệu mô phỏng | Biểu đồ 5, 7 và Native Filters (mở rộng) |
| **04** Frontend và tích hợp API AI/BI | **Đạt** | Đăng nhập/đăng ký, phân quyền; tìm việc, Phân tích CV–JD (M0–M4), Skill Gap, tải CV, ứng tuyển; đăng tin có gợi ý kỹ năng; Kanban 6 cột; dashboard nhúng; quản trị danh mục kỹ năng có giao diện; chế độ demo; Docker Compose; E2E 14/14 | — |
| **05** Kiểm thử với dữ liệu mẫu, báo cáo đánh giá mô hình | **Đạt** về kiểm thử và báo cáo nháp; **chưa đủ** về sản phẩm nộp | 235 test; 46 test case (nhiều ca đã chạy thật); E2E; đo hiệu năng; bảng M0–M4, ablation, hệ số M4, phân tích lỗi trong `docs/report/tables/`; báo cáo đủ 7 chương (`docs/report/BaoCao_TH3.md`); kịch bản video + dàn slide | **Video** (đề chỉ nhận video ≤ 101 MB) và slide chưa làm; các ca test ghi "Chưa kiểm" cần người chạy; nên đối chiếu một phần nhãn với con người nếu giảng viên hỏi |

## Việc còn lại (con người)

| Người | Việc |
|---|---|
| **Cả nhóm** | Quay và dựng video theo `docs/video_kich_ban.md`; nén < 100 MB; ghép slide; chạy các test case còn "Chưa kiểm"; thay mật khẩu/khoá trong `.env` nếu triển khai ngoài máy cá nhân |
| **Tuỳ chọn** | Một thành viên gán lại ~50–100 cặp để đối chiếu với nhãn agent (tính kappa người–agent) và ghi vào chương 6 |

## Sai sót mà lần chạy thật phát hiện và đã sửa

| Phát hiện khi | Lỗi | Sửa |
|---|---|---|
| Chạy Alembic trên PostgreSQL | Dấu `;` trong chú thích làm migration tách sai câu lệnh | Bỏ chú thích trước khi tách + test hồi quy |
| Dựng Superset | Thiếu `flask-cors`; cổng 8088 trùng dự án khác | Thêm gói; `SUPERSET_PORT` cấu hình được |
| Dựng dashboard qua API | Superset 4.1 cần phiên đăng nhập (cookie) cho API ghi | `bootstrap.py` đăng nhập cả hai kiểu |
| Đo bằng model thật | 417 ms/cặp vì hồ sơ chưa có CV bị mã hoá lại mỗi lần | `candidates.embedding` tính khi lưu: 38 ms |
| Chọn M1 | TF-IDF chỉ fit trên hai văn bản | Fit trên các tin đang mở |
| Nạp seed hai lần cùng lúc | DB nửa vời | Một giao dịch + khoá cố vấn PostgreSQL |
| Chạy trên trình duyệt thật | Modal ghi "Demo" khi online; nút đóng không có tên truy cập; M4 làm mất trang | Sửa từng điểm |
| Chạy lại E2E sau khi huấn luyện lại | Lần đầu 5/14 do CSDL còn trạng thái của lần chạy trước (ứng viên demo đã ứng tuyển) | `load_seed --reset` trước khi chạy E2E (đã ghi trong `docs/E2E.md`) |

## Rủi ro còn lại so với đề

1. Phần "ML" thật chỉ có ở M4; trích kỹ năng CV chủ yếu là từ điển + so khớp mờ + embedding, tầng 2–3 chưa cải thiện F1.
2. Dữ liệu ứng tuyển và lương là mô phỏng; nhận định BI chỉ minh hoạ cách tính.
3. Nhãn đánh giá do agent AI gán (xem trên); nếu giảng viên yêu cầu nhãn con người thì phải gán lại.
4. Đề chỉ nhận **video** MP4/… ≤ 101 MB, nộp một lần; hỏi giảng viên kênh nộp báo cáo/slide.
