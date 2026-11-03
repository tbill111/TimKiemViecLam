# Phân tích yêu cầu hệ thống SmartCareer v2 (mục checklist 01)

Đề bài TH3: nền tảng kết nối tuyển dụng thông minh dùng AI khớp kỹ năng ứng viên với yêu cầu công việc (Matching Score) và tích hợp BI để phân tích xu hướng thị trường lao động, cung cấp báo cáo trực quan cho nhà tuyển dụng.

## 1. Bối cảnh và vấn đề

Sinh viên và người mới tốt nghiệp khó biết mình hợp vị trí nào và còn thiếu kỹ năng gì; nhà tuyển dụng phải sàng lọc nhiều hồ sơ chất lượng không đều, quy trình tuyển dụng thiếu số liệu để tối ưu. Bài trước (SmartCareer, prototype React với dữ liệu mẫu, điểm khớp theo quy tắc 60/25/15) giải quyết phía ứng viên trên dữ liệu cố định. Bài này kế thừa giao diện đó và bổ sung backend, CSDL, mô hình AI/ML và dashboard BI.

## 2. Tác nhân

| Tác nhân | Vai trò |
|---|---|
| Ứng viên (sinh viên, người mới tốt nghiệp) | Tạo hồ sơ, tải CV, xác nhận kỹ năng, nhận gợi ý việc, ứng tuyển, theo dõi trạng thái |
| Nhà tuyển dụng (HR của một công ty) | Đăng/sửa/đóng tin, xem ứng viên xếp hạng, cập nhật trạng thái, xem dashboard BI của công ty |
| Quản trị viên | Quản lý danh mục kỹ năng và từ đồng nghĩa, xem dashboard toàn thị trường |
| Dịch vụ AI (tác nhân hệ thống) | Trích kỹ năng từ CV/JD, tính Matching Score kèm giải thích |

## 3. Yêu cầu chức năng

Cột "Mục checklist" theo 5 mục của đề: 01 phân tích/CSDL, 02 AI/ML, 03 BI, 04 frontend + tích hợp API, 05 kiểm thử + báo cáo. Cột "Hiện thực" chỉ tên file có trong repo; "Kiểm thử" là mã ở `docs/testcases.md`.

| Mã | Chức năng | Tác nhân | Mục checklist | Ưu tiên | Mô tả | Hiện thực | Kiểm thử |
|---|---|---|---|---|---|---|---|
| F01 | Tài khoản và phân quyền | Tất cả | 01, 04 | Cao | Đăng ký, đăng nhập (JWT), phân quyền 3 vai trò; không tự đăng ký admin; recruiter phải có công ty | `routers/auth.py`, `deps.py`, `LoginPage`, `RegisterPage` | TC01–TC05 |
| F02 | Hồ sơ ứng viên | Ứng viên | 01, 04 | Cao | Học vấn, kinh nghiệm, địa điểm/hình thức/lương mong muốn; xóa hồ sơ | `routers/candidates.py`, `ProfilePage` | TC06, TC07 |
| F03 | Tải và phân tích CV | Ứng viên, AI | 02, 04 | Cao | PDF/DOCX/TXT ≤ 5 MB, chỉ lưu khi đồng ý; đề xuất kỹ năng (từ điển, so khớp mờ, embedding); người dùng xác nhận/sửa | `routers/resumes.py`, `app/ai/parser.py` | TC08–TC10 |
| F04 | Quản lý tin tuyển dụng | Nhà tuyển dụng | 01, 04 | Cao | Tạo/sửa/đóng tin; kỹ năng bắt buộc và ưu tiên; gợi ý kỹ năng từ mô tả | `routers/jobs.py`, `POST /ai/extract-skills`, `PostJobPage`, `EditJobPage` | TC11–TC14 |
| F05 | Matching Score có giải thích | AI | 02 | Cao | Điểm 0–100, 6 điểm thành phần, kỹ năng có/thiếu, câu giải thích; 5 mô hình M0–M4 | `app/ai/scorers.py`, `POST /ai/match`, `MatchPage` | TC15–TC18 |
| F06 | Gợi ý và xếp hạng | AI | 02, 04 | Cao | Top-N việc cho ứng viên; xếp hạng ứng viên đã nộp cho một tin | `GET /candidates/me/recommendations`, `GET /jobs/{id}/ranked-candidates` | TC19, TC20 |
| F07 | Ứng tuyển và trạng thái | Ứng viên, nhà tuyển dụng | 01, 04 | Cao | Nộp đơn (lưu điểm khớp), đổi trạng thái theo phễu, ghi lịch sử | `routers/applications.py`, `EmployerKanbanPage`, `ApplicationsPage` | TC21–TC24 |
| F08 | Skill Gap | Ứng viên | 02, 04 | Trung bình | Kỹ năng thiếu so với việc mục tiêu, bắt buộc trước; lộ trình học | `GET /candidates/me/skill-gap`, `SkillGapPage` | TC25 |
| F09 | Dashboard BI | Nhà tuyển dụng, quản trị | 03 | Cao | Ứng viên theo kỹ năng, xu hướng lương, tỷ lệ chuyển đổi; nhúng Superset hoặc dự phòng Recharts; lọc theo công ty | `routers/bi.py`, `bi/views.sql`, `EmployerDashboardPage` | TC26–TC28 |
| F10 | Danh mục kỹ năng | Quản trị | 01, 04 | Thấp | Thêm/sửa kỹ năng, thêm/xóa alias (ví dụ `reactjs` → React) | `routers/admin.py`, `AdminSkillsPage` | TC29 |

## 4. Yêu cầu phi chức năng

| Nhóm | Yêu cầu | Cách đáp ứng | Kiểm thử |
|---|---|---|---|
| Hiệu năng | Chấm 1 cặp < 200 ms; gợi ý trên 500 tin < 2 giây | Embedding tính sẵn khi lưu CV, tin, hồ sơ (cột `embedding`); chấm bằng numpy | TC30 |
| Giải thích được | Mọi điểm kèm điểm thành phần và danh sách kỹ năng thiếu | `MatchDTO` thống nhất, `app/ai/explain.py` | TC15 |
| Bảo mật | Mật khẩu băm bcrypt, JWT HS256, phân quyền theo vai trò; nhà tuyển dụng chỉ xem đơn thuộc công ty mình; dashboard lọc theo `company_id` | `routers/auth.py`, `deps.py`, guest token kèm RLS | TC03–TC05, TC13, TC20, TC24 |
| Dữ liệu cá nhân | CV chỉ lưu khi có đồng ý; có chức năng xóa hồ sơ | `consent` ở upload, `DELETE /candidates/me` | TC07, TC09 |
| Công bằng | Không dùng tên, giới tính, tuổi làm đặc trưng; phần đầu CV bị loại khỏi văn bản dùng chấm điểm | `model_text` trong `parse_cv` | TC18 |
| Khả dụng | Chạy được không cần backend ở chế độ demo | `VITE_OFFLINE_DEMO=true` | TC31 |
| Triển khai | Một lệnh `docker compose up` chạy db, api, superset, web | `docker-compose.yml` | TC32 |
| Trung thực dữ liệu | Dữ liệu seed và đơn ứng tuyển là mô phỏng; hiệu quả mô hình chỉ kết luận từ nhãn gán tay | `backend/seed/README.md` | — |

## 5. Phạm vi và giới hạn

Ngoài phạm vi: thanh toán, chat hai bên, gửi email thật, thu thập dữ liệu từ LinkedIn/TopCV (điều khoản sử dụng không cho phép).
Giới hạn đã biết: CV dạng ảnh scan không đọc được (báo `no_text`); danh mục có 81 kỹ năng và 167 từ đồng nghĩa; dữ liệu ứng viên, tin, đơn ứng tuyển là mô phỏng (seed cố định 42) nên xu hướng lương và tỷ lệ tuyển chỉ minh hoạ cách tính.
