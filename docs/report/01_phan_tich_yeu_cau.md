# Phân tích yêu cầu hệ thống SmartCareer v2 (mục checklist 01)

Đề bài TH3: nền tảng kết nối tuyển dụng thông minh dùng AI khớp kỹ năng ứng viên với yêu cầu công việc (Matching Score) và tích hợp BI để phân tích xu hướng thị trường lao động, cung cấp báo cáo trực quan cho nhà tuyển dụng.

## 1. Tác nhân

| Tác nhân | Vai trò |
|---|---|
| Ứng viên (sinh viên, người mới tốt nghiệp) | Tạo hồ sơ, tải CV, xác nhận kỹ năng, nhận gợi ý việc, ứng tuyển, theo dõi trạng thái |
| Nhà tuyển dụng (HR của một công ty) | Đăng/sửa/đóng tin, xem ứng viên xếp hạng, cập nhật trạng thái, xem dashboard BI của công ty |
| Quản trị viên | Quản lý danh mục kỹ năng và từ đồng nghĩa, xem dashboard toàn thị trường |
| Dịch vụ AI (tác nhân hệ thống) | Trích kỹ năng từ CV/JD, tính Matching Score kèm giải thích |

## 2. Yêu cầu chức năng

| Mã | Chức năng | Tác nhân | Mô tả | Hiện thực | Kiểm thử |
|---|---|---|---|---|---|
| F01 | Tài khoản và phân quyền | Tất cả | Đăng ký, đăng nhập (JWT), phân quyền theo vai trò; không tự đăng ký admin | `routers/auth.py`, `deps.py` | TC01–TC05 |
| F02 | Hồ sơ ứng viên | Ứng viên | Học vấn, kinh nghiệm, địa điểm/hình thức mong muốn, lương mong muốn; đồng ý xử lý dữ liệu; xóa hồ sơ | `routers/candidates.py` | TC06, TC07 |
| F03 | Tải và phân tích CV | Ứng viên, AI | PDF/DOCX/TXT ≤ 5 MB; hệ thống đề xuất kỹ năng (từ điển, so khớp mờ, embedding); người dùng xác nhận/sửa | `routers/resumes.py`, `app/ai/parser.py` | TC08–TC10 |
| F04 | Quản lý tin tuyển dụng | Nhà tuyển dụng | Tạo/sửa/đóng tin; chọn kỹ năng bắt buộc và ưu tiên; gợi ý kỹ năng từ mô tả | `routers/jobs.py`, `/ai/extract-skills` | TC11–TC14 |
| F05 | Matching Score có giải thích | AI | Điểm 0–100, 6 điểm thành phần, kỹ năng có/thiếu, câu giải thích; 5 mô hình M0–M4 | `app/ai/scorers.py`, `/ai/match` | TC15–TC18 |
| F06 | Gợi ý và xếp hạng | AI | Top-N việc cho ứng viên; xếp hạng ứng viên đã nộp cho một tin | `/candidates/me/recommendations`, `/jobs/{id}/ranked-candidates` | TC19, TC20 |
| F07 | Ứng tuyển và trạng thái | Ứng viên, nhà tuyển dụng | Nộp đơn (lưu điểm khớp), đổi trạng thái theo phễu, ghi lịch sử | `routers/applications.py` | TC21–TC24 |
| F08 | Skill Gap | Ứng viên | Kỹ năng thiếu so với việc mục tiêu, xếp theo bắt buộc rồi theo số tin yêu cầu; lộ trình học | `/candidates/me/skill-gap` | TC25 |
| F09 | Dashboard BI | Nhà tuyển dụng, quản trị | Số ứng viên theo kỹ năng, xu hướng lương, tỷ lệ chuyển đổi; nhúng Superset hoặc dự phòng Recharts; lọc theo công ty | `routers/bi.py`, `bi/views.sql` | TC26–TC29 |
| F10 | Danh mục kỹ năng | Quản trị | Thêm kỹ năng, sửa nhóm và lộ trình học, thêm/xóa alias (ví dụ `reactjs` → React); có giao diện `/admin/skills` | `routers/saved_admin.py`, `src/pages/AdminSkillsPage.tsx` | TC30, TC39 |

## 3. Yêu cầu phi chức năng

| Nhóm | Yêu cầu | Cách đáp ứng | Kiểm thử |
|---|---|---|---|
| Hiệu năng | Chấm 1 cặp < 200 ms; gợi ý trên 500 tin < 2 giây | Embedding tính sẵn khi lưu CV, tin và hồ sơ (`resumes.embedding`, `jobs.embedding`, `candidates.embedding`); chấm bằng numpy. Đo thật: 38 ms/cặp, 70–77 ms/500 tin | TC31, TC42 |
| Giải thích được | Mọi điểm kèm điểm thành phần và danh sách kỹ năng thiếu | `MatchDTO` thống nhất, `explain.py` | TC15 |
| Bảo mật | Mật khẩu băm bcrypt, JWT, phân quyền theo vai trò; nhà tuyển dụng chỉ xem ứng viên đã nộp vào tin của công ty mình; dashboard lọc theo `company_id` | `security.py`, `deps.py`, RLS ở guest token | TC05, TC13, TC20, TC27 |
| Dữ liệu cá nhân | CV chỉ lưu khi có `consent`; có chức năng xóa hồ sơ | `consent_at`, `DELETE /candidates/me` | TC07, TC09 |
| Công bằng | Không dùng tên, giới tính, tuổi, ảnh làm đặc trưng; phần đầu CV bị loại khỏi văn bản dùng chấm điểm | `parse_cv` trả `model_text` | TC18 |
| Khả dụng | Chạy được không cần backend ở chế độ demo | `VITE_OFFLINE_DEMO=true` | TC32 |
| Triển khai | Một lệnh `docker compose up` chạy db, api, superset, web | `docker-compose.yml` | TC33, TC36 |
| Trung thực dữ liệu | Dữ liệu seed và đơn ứng tuyển là mô phỏng; hiệu quả mô hình kết luận từ nhãn do agent AI gán, kèm hạn chế về nguồn nhãn | `seed/README.md`, `gen_applications.py` | — |

## 4. Phạm vi và giới hạn

Ngoài phạm vi: thanh toán, chat hai bên, gửi email thật, thu thập dữ liệu từ LinkedIn/TopCV (điều khoản sử dụng không cho phép).
Giới hạn đã biết: CV dạng ảnh scan không đọc được (báo lỗi `no_text`); từ điển kỹ năng có 108 kỹ năng; dữ liệu mô phỏng nên xu hướng lương và tỷ lệ tuyển chỉ minh hoạ cách tính; trên bộ CV tổng hợp, so khớp mờ và embedding (tầng 2–3) chưa cải thiện F1 so với từ điển (tầng 1) (nhãn do agent AI gán; cần đối chiếu với con người để kết luận chắc chắn).
