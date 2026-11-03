# Đặc tả 3 use case chính

## UC-A Tải CV (F03)

| Mục | Nội dung |
|---|---|
| Tác nhân | Ứng viên; dịch vụ AI |
| Tiền điều kiện | Đã đăng nhập với vai trò ứng viên; có hồ sơ |
| Luồng chính | 1. Ứng viên chọn tệp PDF/DOCX/TXT và tích đồng ý xử lý dữ liệu. 2. Hệ thống kiểm tra định dạng và dung lượng (≤ 5 MB). 3. Dịch vụ AI đọc văn bản, chuẩn hoá, tách mục, trích kỹ năng (từ điển → so khớp mờ → embedding), số năm kinh nghiệm, học vấn. 4. Hệ thống lưu CV và trả danh sách kỹ năng đề xuất (chưa xác nhận). 5. Ứng viên bỏ chọn/thêm kỹ năng và xác nhận. 6. Kỹ năng đã xác nhận được tính vào hồ sơ và điểm khớp được tính lại |
| Luồng phụ | 2a. Thiếu đồng ý → 400 `consent_required`. 2b. Sai định dạng → 415. 2c. Quá 5 MB → 413. 3a. CV ảnh scan/không có chữ → 422 `no_text`. 3b. Tệp hỏng → 422 `corrupt`. 4a. Kỹ năng từ embedding được đánh dấu "gợi ý" độ tin cậy thấp |
| Hậu điều kiện | CV mới là CV đang dùng (CV cũ bị vô hiệu); chỉ kỹ năng đã xác nhận ảnh hưởng điểm |

## UC-B Xem việc gợi ý (F06)

| Mục | Nội dung |
|---|---|
| Tác nhân | Ứng viên; dịch vụ AI |
| Tiền điều kiện | Đã đăng nhập; có ít nhất một kỹ năng đã xác nhận (nếu không, điểm thấp) |
| Luồng chính | 1. Ứng viên mở Tổng quan hoặc Tìm việc. 2. Hệ thống chấm hồ sơ với mọi tin đang mở bằng model mặc định (M3). 3. Trả danh sách xếp giảm dần theo điểm, mỗi tin kèm điểm, kỹ năng có/thiếu, câu giải thích. 4. Ứng viên mở "Phân tích CV–JD" để đổi model M0–M4 và xem 6 thành phần điểm |
| Luồng phụ | 4a. Chọn M4 khi chưa huấn luyện → 503 `model_not_trained`, giao diện báo lỗi tại chỗ và vẫn dùng được M0–M3 |
| Hậu điều kiện | Kết quả chấm lưu ở `match_results` theo `model_version` |

## UC-C Đổi trạng thái hồ sơ ứng tuyển (F07)

| Mục | Nội dung |
|---|---|
| Tác nhân | Nhà tuyển dụng |
| Tiền điều kiện | Đã đăng nhập; hồ sơ thuộc tin của công ty mình; hồ sơ chưa ở trạng thái cuối |
| Luồng chính | 1. Nhà tuyển dụng mở "Ứng viên xếp hạng", chọn tin. 2. Hệ thống hiển thị Kanban 6 cột và điểm khớp. 3. Nhà tuyển dụng chọn "Chuyển → bước kế tiếp" hoặc "Từ chối". 4. Hệ thống kiểm tra luật chuyển, cập nhật trạng thái và ghi một dòng vào `application_status_history` |
| Luồng phụ | 4a. Nhảy cóc bước hoặc đổi hồ sơ đã `hired`/`rejected` → 409 `invalid_transition`. 4b. Hồ sơ của công ty khác → 403 |
| Hậu điều kiện | Số liệu phễu trên dashboard tính từ lịch sử nên cập nhật ngay |

Luật chuyển: `applied → screening → interview → offer → hired`; từ bất kỳ trạng thái chưa kết thúc có thể sang `rejected`; `hired` và `rejected` là cuối.
