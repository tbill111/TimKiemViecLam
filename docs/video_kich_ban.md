# Kịch bản video demo (6–8 phút) và dàn slide

Đề chỉ nhận video MP4/MOV/MKV/AVI/WEBM, tối đa 101 MB, nộp một lần. Quay 1080p, xuất H.264 rồi nén:
`ffmpeg -i demo.mp4 -vcodec libx264 -crf 28 -b:a 96k demo_small.mp4` (kiểm tra < 100 MB). Link repo, báo cáo đặt ở mô tả video hoặc cuối video; hỏi giảng viên có kênh nộp thêm không.

Chuẩn bị trước khi quay: `docker compose up -d`, `docker compose exec api python -m seed.load_seed --reset`, đăng xuất hết; mở http://localhost:8080. Nhớ rằng số liệu đánh giá mô hình hiện là nhãn mô phỏng: chỉ nói là "chạy thử quy trình" cho tới khi có nhãn tay.

| Thời gian | Mục | Cảnh quay | Lời dẫn gợi ý |
|---|---|---|---|
| 0:00–0:30 | Mở đầu | Sơ đồ 4 dịch vụ (README), tên đề, nhóm | Bài toán, mục tiêu, kiến trúc Compose |
| 0:30–1:30 | **01 CSDL** | `docs/erd/erd.png`, `usecase.png`; `\dt` trong psql hoặc Swagger | 15 bảng, ba đối tượng ứng viên/nhà tuyển dụng/tin; 150 tin, 301 ứng viên, 1.255 đơn; dữ liệu hư cấu |
| 1:30–3:15 | **02 AI/ML + 04 ứng viên** | Đăng nhập `tung.demo@smartcareer.vn`; Tìm việc có điểm; Hồ sơ → tải `cv-mau.pdf`, tích đồng ý, xác nhận kỹ năng; Phân tích CV–JD đổi M0→M3, xem 6 thành phần và câu giải thích | Parser 3 tầng, 6 đặc trưng, 5 mô hình; điểm có giải thích; M4 có cảnh báo vì huấn luyện trên nhãn mô phỏng; Skill Gap |
| 3:15–4:15 | **04 luồng ứng tuyển** | Ứng tuyển một tin; đăng xuất, đăng nhập `hr01@…`; Ứng viên xếp hạng, chuyển trạng thái; thử bước sai để thấy lỗi 409 | Luật trạng thái, lịch sử trạng thái, nhà tuyển dụng chỉ thấy ứng viên đã nộp tin của công ty mình |
| 4:15–5:15 | **03 BI** | Dashboard Superset nhúng; chỉ ba biểu đồ bắt buộc (kỹ năng, lương, phễu); so với công ty khác (hr05) để thấy RLS; `python scripts/check_bi_views.py` | Ba chỉ số của đề; phễu đếm "từng đạt"; số view khớp API; dữ liệu mô phỏng |
| 5:15–6:15 | Quản trị | `admin@…` → Quản lý kỹ năng: thêm alias; trích kỹ năng nhận alias mới | F10, tác động tới parser |
| 6:15–7:30 | **05 Kiểm thử + đánh giá** | Chạy `pytest` (236 xanh); `docs/testcases.md`; bảng M0–M4, ablation (bản nhãn tay khi có); hiệu năng 38 ms | Quy trình gán nhãn, kappa, GroupKFold; kết luận trung thực và hạn chế |
| 7:30–8:00 | Kết | Slide tóm tắt | Điều đạt được, hạn chế (dữ liệu mô phỏng, nhãn), hướng phát triển |

## Dàn slide (≤ 12 trang)
1. Đề và mục tiêu · 2. Kiến trúc · 3. Use Case · 4. ERD · 5. Parser và 6 đặc trưng · 6. M0–M4 · 7. Kết quả đánh giá (bảng 6.4 bản nhãn tay) · 8. Dashboard BI · 9. Luồng ứng viên và nhà tuyển dụng (ảnh E2E) · 10. Kiểm thử và hiệu năng · 11. Hạn chế · 12. Hướng phát triển
