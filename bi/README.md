# Dashboard BI "Thị trường tuyển dụng"

Superset đọc 4 view trong `views.sql` bằng role `bi_reader` (chỉ `SELECT`). Dữ liệu seed là **mô phỏng**, nên các biểu đồ minh hoạ cách tính chứ không chứng minh hiệu quả mô hình AI.

> Đã chạy thật trên Superset 4.1.1 + PostgreSQL 16 (Docker): `bootstrap.py` dựng được dashboard, nhúng hiển thị đúng trong ứng dụng và guest token áp RLS theo công ty khớp `/api/bi/funnel`. Nếu nhúng lỗi, ứng dụng tự chuyển sang 3 biểu đồ Recharts đọc `/api/bi/*`.

## 1. Chạy

```bash
cp .env.example .env
docker compose up --build         # db, api (tự migrate + seed), superset, web
```

Superset: http://localhost:8088 (admin / admin theo `.env`).

## 1b. Dựng dashboard tự động (khuyến nghị)

```bash
python bi/superset/bootstrap.py --url http://localhost:8088 --write-env .env   # đổi cổng nếu đặt SUPERSET_PORT
docker compose up -d api                                                       # nạp SUPERSET_DASHBOARD_ID, SUPERSET_RLS_DATASET_IDS
```

Script tạo kết nối (role `bi_reader`), 4 dataset, 7 biểu đồ (1, 1b, 2, 3, 4, 6, 8), dashboard "Thị trường tuyển dụng", bật nhúng cho `http://localhost:8080` và `:5173`, rồi ghi UUID và id dataset RLS vào `.env`. Chạy lại không tạo trùng. Biểu đồ 5, 7 và Native Filters thêm bằng giao diện nếu cần; mục 2–4 dưới đây là cách làm thủ công tương đương.

## 2. Kết nối dữ liệu (thủ công)

*Settings → Database Connections → + Database → PostgreSQL*:
`postgresql+psycopg2://bi_reader:<BI_READER_PASSWORD>@db:5432/smartcareer`

Tạo 4 dataset (Datasets → + Dataset) từ `v_skill_supply_demand`, `v_salary`, `v_funnel`, `v_funnel_stages`.

## 3. Biểu đồ (theo `docs/00_KE_HOACH_KY_THUAT_TH3.md` mục 4)

| # | Chart (loại) | Dataset | Cấu hình | Bắt buộc |
|---|---|---|---|---|
| 1 | KPI: tổng hồ sơ nộp, tỷ lệ tuyển (Big Number) | v_funnel | metric `COUNT(*)`; `AVG(hired::int)` | Mở rộng |
| 2 | Top 15 kỹ năng theo số ứng viên (Bar) | v_skill_supply_demand | x = `skill`, metric `MAX(so_ung_vien)`, sắp giảm dần, row limit 15 | **Có** |
| 3 | Cung so với cầu theo kỹ năng (Bar, 2 cột) | v_skill_supply_demand | x = `skill`, metrics `MAX(so_ung_vien)` và `MAX(so_tin_yeu_cau)` | Mở rộng |
| 4 | Trung vị lương theo tháng, mỗi cấp bậc một đường (Line) | v_salary | x = `thang`, series = `level`, metric `AVG(luong_tb)` (hoặc custom SQL `PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY luong_tb)`) | **Có** |
| 5 | Phân bố lương theo cấp bậc (Box Plot) | v_salary | distribute across `job_id`, metric `AVG(luong_tb)`, group by `level` | Mở rộng |
| 6 | Phễu Applied → Hired (Funnel) | v_funnel_stages | dimension `giai_doan`, metric `SUM(so_ho_so)` | **Có** |
| 7 | Trung vị time-to-hire theo tháng (Line) | v_funnel | x = `thang_nop`, metric custom SQL `PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ngay_den_khi_tuyen)`, lọc `hired` | Mở rộng |
| 8 | Tỷ lệ được tuyển theo nhóm điểm khớp (Bar) | v_funnel | x = `nhom_diem`, metric `AVG(hired::int)` | Mở rộng, nên có |

Native Filters: khoảng thời gian (`thang`/`thang_nop`), địa điểm (`dia_diem`), cấp bậc (`level`), nhóm kỹ năng (`category`).

**Đối chiếu số:** 3 chỉ số bắt buộc phải khớp `GET /api/bi/skills`, `/api/bi/salary`, `/api/bi/funnel` (cùng định nghĩa) hoặc truy vấn tay trên PostgreSQL.

## 4. Nhúng vào ứng dụng

1. Mở dashboard → `...` → *Embed dashboard* → thêm domain `http://localhost:8080` (và `http://localhost:5173` khi chạy dev) → sao chép **UUID**.
2. Trong `Datasets`, ghi id của `v_funnel` và `v_funnel_stages` (số trong URL `/dataset/<id>`), hoặc gọi `GET /api/v1/dataset/`.
3. Điền `.env`: `SUPERSET_DASHBOARD_ID=<uuid>`, `SUPERSET_RLS_DATASET_IDS=<id1>,<id2>` rồi `docker compose up -d api`.
4. Đăng nhập nhà tuyển dụng (ví dụ `hr01@smartcareer.vn`) → trang Dashboard. API cấp guest token kèm RLS `company_id = <công ty của bạn>` trên hai dataset phễu; thiếu `SUPERSET_RLS_DATASET_IDS` thì API từ chối cấp token cho nhà tuyển dụng (tránh lộ dữ liệu công ty khác).
5. Dữ liệu thị trường (kỹ năng, lương) là chung nên không gắn RLS.

## 5. Xuất để nộp

*Dashboards → chọn dashboard → Export* → lưu `bi/superset/dashboard_export.zip` (kiểm tra import lại được); chụp ảnh vào `bi/screenshots/`; viết 3–4 nhận định từ số liệu.
