# SmartCareer – Hệ thống Tìm việc Thông minh cho Sinh viên

Prototype frontend phục vụ bài tập học phần *“Thiết kế Ý tưởng Hệ thống Tìm kiếm Việc làm Thông minh và Chiến lược Thu thập Dữ liệu”*.

Đây là **prototype chạy trên trình duyệt**, không có backend, không có cơ sở dữ liệu và không gọi API AI hay API tuyển dụng bên ngoài. Toàn bộ dữ liệu là dữ liệu mẫu trong thư mục `src/data/`. Trạng thái (hồ sơ đã sửa, việc đã lưu, ứng tuyển demo) được lưu trong `localStorage` của trình duyệt.

## Yêu cầu

- Node.js 20 trở lên (đã kiểm tra với Node 22)
- npm

## Cài đặt và chạy

```bash
npm install
npm run dev
```

Sau đó mở địa chỉ hiển thị trong terminal (thường là `http://localhost:5173`).

## Các lệnh khác

| Lệnh | Mô tả |
| --- | --- |
| `npm run build` | Kiểm tra kiểu TypeScript (`tsc -b`) và build bản production vào `dist/` |
| `npm run preview` | Chạy thử bản đã build tại `http://localhost:4173` |
| `npm run lint` | Kiểm tra mã nguồn bằng oxlint |

## Các màn hình

| Đường dẫn | Màn hình |
| --- | --- |
| `/` | Tổng quan: số liệu, việc phù hợp nhất, kỹ năng, gợi ý |
| `/jobs` | Tìm việc làm: tìm kiếm, lọc, sắp xếp, lưu việc, ứng tuyển demo |
| `/match` | Phân tích CV–JD: điểm phù hợp, kỹ năng đạt và còn thiếu |
| `/skill-gap` | Skill Gap Analysis: chọn công việc mục tiêu, đánh dấu kỹ năng đã học |
| `/applications` | Việc đã lưu & ứng tuyển: theo dõi trạng thái |
| `/profile` | Hồ sơ của tôi: chỉnh sửa thông tin, mong muốn công việc, kỹ năng, dự án, kinh nghiệm, chứng chỉ |
| `/employer` | Cổng nhà tuyển dụng: xếp hạng ứng viên theo tin tuyển dụng, cập nhật trạng thái hồ sơ |
| `/etl` | Trung tâm Dữ liệu & ETL: nguồn dữ liệu, Extract, Transform, Load, chỉ số chất lượng |
| `/dfd` | Sơ đồ luồng dữ liệu (DFD mức 1) |
| `/about` | Về SmartCareer: vấn đề, giải pháp, công nghệ đang dùng và dự kiến |

Ở sidebar có nút **Đặt lại dữ liệu demo** để khôi phục hồ sơ và trạng thái ban đầu.

## Giới hạn của prototype

- Điểm phù hợp là **mô phỏng ghép nối đa tiêu chí theo quy tắc**: 60% tỷ lệ kỹ năng bắt buộc đáp ứng + 25% tỷ lệ kỹ năng ưu tiên đáp ứng + 15% mức khớp mong muốn (địa điểm, hình thức). Đây không phải mô hình AI thật.
- Ứng viên ở cổng nhà tuyển dụng là dữ liệu minh họa; chỉ hồ sơ sinh viên hiện tại là hồ sơ người dùng nhập.
- Tin tuyển dụng, tên công ty và mức lương đều là dữ liệu minh họa.
- Tải CV chỉ ghi nhận tên tệp, không đọc nội dung CV.
- Số liệu ở trang ETL được tính từ dataset mẫu, không phải dữ liệu thu thập thật.
- Công nghệ backend (FastAPI/Node.js), PostgreSQL và pipeline ETL chỉ là kiến trúc dự kiến, chưa được triển khai.

## Công nghệ

- React 19, TypeScript, Vite
- Tailwind CSS 4
- React Router 7
- Recharts (biểu đồ radar)
- Lucide React (icon)
