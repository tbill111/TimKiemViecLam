# SOP: Tạo dashboard BI trên Apache Superset

Hướng dẫn này dùng ba view được tạo bởi Alembic migration `0004_bi_views`:
`vw_candidate_skills`, `vw_salary_trends` và `vw_ai_matching_stats`.

> **Lưu ý về tên view:** `bi/views.sql` hiện tại vẫn định nghĩa các view cũ có tiền tố
> `v_` (`v_skill_supply_demand`, `v_salary`, `v_funnel`, `v_funnel_stages`), không
> chứa ba view `vw_*` trong hướng dẫn này. Các trường bên dưới được lấy từ SQL trong
> migration `0004_bi_views`.

## 1. Chuẩn bị database và kết nối Superset

### 1.1. Cập nhật schema và quyền đọc

Từ PowerShell tại thư mục gốc dự án, chạy migration bằng cùng `DATABASE_URL` đang
trỏ tới PostgreSQL của Docker:

```powershell
docker compose exec api alembic upgrade head
```

Migration mới nhất tạo/cấp quyền `SELECT` cho role BI trên ba view. Kiểm tra log lệnh
không có lỗi trước khi tạo Dataset.

### 1.2. Thông số kết nối PostgreSQL

Service `superset` trong `docker-compose.yml` tự tạo/cập nhật một Database connection
tên **SmartCareer** khi container khởi động. Vì vậy, thông thường không cần nhập lại
thông tin này trong giao diện.

Nếu cần kiểm tra hoặc tự thêm Database connection, dùng các giá trị sau:

| Trường trong Superset | Giá trị |
|---|---|
| Database type | PostgreSQL |
| Host | `db` |
| Port | `5432` |
| Database name | Giá trị `POSTGRES_DB` trong `.env`; mặc định `smartcareer` |
| Username | Giá trị `BI_DATABASE_USER`; mặc định `bi_reader` |
| Password | Giá trị `BI_READER_PASSWORD` trong `.env` |
| Display name | `SmartCareer` |

Hostname `db` chỉ dùng được từ container Superset trong Docker Compose; không dùng
`localhost` trong cấu hình kết nối giữa các container. Không nhập URI có password
vào tài liệu hoặc chia sẻ ảnh chụp màn hình chứa credentials.

### 1.3. Tạo ba Dataset từ các view

Lặp lại các bước sau cho từng view:

1. Đăng nhập Superset tại `http://localhost:8088`.
2. Trên thanh điều hướng, chọn **Data → Datasets**.
3. Chọn **+ Dataset** (hoặc **Add dataset**, tùy bố cục màn hình).
4. Chọn Database **SmartCareer**.
5. Chọn schema **public**.
6. Chọn một view từ danh sách:
   - `vw_candidate_skills`
   - `vw_salary_trends`
   - `vw_ai_matching_stats`
7. Chọn **Add** / **Save** để đăng ký Dataset.
8. Lặp lại để tạo đủ ba Dataset. Ghi lại Dataset tương ứng với từng view để chọn
   đúng khi tạo Chart.

## 2. Chart 1 — Phân bố kỹ năng ứng viên

Mục tiêu: so sánh số ứng viên có từng kỹ năng.

1. Chọn **Charts → + Chart**.
2. Chọn Dataset **`vw_candidate_skills`**.
3. Chọn loại **Bar Chart** (ECharts).
4. Trong phần cấu hình dữ liệu:
   - **X-axis**: `skill_name`
   - **Metric**: `SUM(candidate_count)`
   - **Sort by**: `SUM(candidate_count)`, giảm dần
   - **Row limit**: tùy chọn, ví dụ `20` để biểu đồ dễ đọc
5. Chọn **Run** để xem biểu đồ.
6. Đặt tên, ví dụ **Số ứng viên theo kỹ năng**, rồi chọn **Save**.

View có một dòng cho mỗi kỹ năng, vì vậy tổng `candidate_count` theo `skill_name`
chính là số ứng viên của kỹ năng đó. View này chỉ có số lượng ứng viên; không có
cột nhu cầu tuyển dụng.

## 3. Chart 2 — Xu hướng mức lương theo chức danh

View hiện nhóm theo `title` và `level`, không có trường ngày/tháng. Vì vậy nên dùng
**Bar Chart**; không dùng Line Chart để thể hiện xu hướng thời gian khi chưa có trục
thời gian trong Dataset.

1. Chọn **Charts → + Chart**.
2. Chọn Dataset **`vw_salary_trends`**.
3. Chọn loại **Bar Chart** (ECharts).
4. Cấu hình:
   - **X-axis**: `title`
   - **Metric**: `MAX(average_salary)`
   - **Series / Group by**: `level` (nếu giao diện có trường này), để phân biệt
     cấp bậc trong cùng chức danh
   - **Sort by**: `MAX(average_salary)`, giảm dần
5. Chọn **Run**, đặt tên **Lương trung bình theo chức danh và cấp bậc**, rồi **Save**.

`average_salary` đã được tính trong SQL view từ `salary_min` và `salary_max`.
`MAX(average_salary)` dùng để giữ nguyên giá trị đã tổng hợp cho mỗi cặp chức danh
và cấp bậc, không phải tính lại trung bình từ các bản ghi Job gốc. Dữ liệu lương
được lưu theo triệu VND/tháng; đặt nhãn trục Y tương ứng nếu phiên bản Superset cho
phép cấu hình.

## 4. Chart 3 — Tỷ lệ AI Matching

Mục tiêu: thể hiện số cặp CV–Job trong từng nhóm điểm và tỷ trọng trên tổng số cặp
đã được AI chấm.

1. Chọn **Charts → + Chart**.
2. Chọn Dataset **`vw_ai_matching_stats`**.
3. Chọn **Pie Chart**; bật kiểu **Donut** nếu phần **Customize** có tùy chọn đó.
4. Cấu hình dữ liệu:
   - **Dimension / Group by**: `score_bucket`
   - **Metric**: `SUM(pair_count)`
   - **Labels**: bật hiển thị nhãn và phần trăm nếu có tùy chọn trong **Customize**
5. Chọn **Run**, đặt tên **Tỷ lệ các nhóm điểm AI Matching**, rồi **Save**.

Các nhóm điểm trong view là `Kém` (<50), `Khá` (50–75, bao gồm cả 75) và `Tốt`
(>75). Cột `percentage` đã là phần trăm trên tổng số tác vụ hoàn tất có điểm; có thể
chọn `MAX(percentage)` làm Metric thay cho `SUM(pair_count)` nếu muốn nhãn/giá trị
biểu đồ dùng trực tiếp phần trăm. Không cộng `percentage` qua nhiều chiều khác vì
view chỉ có một dòng cho mỗi nhóm điểm.

## 5. Đưa các Chart vào Dashboard

1. Mở từng Chart đã lưu và chọn **Add to dashboard**; hoặc tạo Dashboard mới qua
   **Dashboards → + Dashboard**.
2. Đặt tên, ví dụ **SmartCareer — BI và Phân tích dữ liệu**.
3. Thêm ba Chart vào Dashboard, sắp xếp và đổi kích thước các khung theo nhu cầu.
4. Chọn **Save** trên Dashboard.
5. Dùng **Refresh** sau khi nạp dữ liệu mới để xem lại kết quả.

Nếu Chart báo lỗi quyền truy cập, hãy xác nhận đã chạy `docker compose exec api alembic
upgrade head`, role `bi_reader` trong `.env` khớp với cấu hình PostgreSQL, và Superset
đang kết nối đúng Database **SmartCareer**.
