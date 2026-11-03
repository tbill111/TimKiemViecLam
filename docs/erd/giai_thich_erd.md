# Giải thích ERD (15 bảng)

Ảnh: `erd.png` (sinh bằng `scripts/render_erd.py`); nguồn văn bản: `erd.dbml` (dbdiagram.io) và `erd.puml` (PlantUML), cả hai sinh từ `backend/app/models/entities.py` bằng `backend/scripts/gen_erd.py` nên không lệch schema thật. DDL tham chiếu: `backend/scripts/export_schema.py` → `backend/schema.sql`.

## Ba nhóm chính theo đề bài

| Nhóm | Bảng | Ý nghĩa |
|---|---|---|
| Ứng viên | `users`, `candidates`, `resumes`, `candidate_skills`, `saved_jobs` | Tài khoản, hồ sơ chuẩn hoá (cột để lọc/BI) cộng `profile_json` giữ phần hồ sơ có cấu trúc của frontend; CV đã tải (văn bản, kết quả phân tích, embedding, thời điểm đồng ý); kỹ năng của ứng viên (nguồn `profile`/`cv`/`manual`, cờ đã xác nhận); tin đã lưu |
| Nhà tuyển dụng | `companies`, `recruiters` | Công ty và tài khoản tuyển dụng thuộc công ty |
| Tin tuyển dụng | `jobs`, `job_skills` | Tin (cấp bậc, hình thức, lương, `category`, `responsibilities`, `embedding`) và kỹ năng `required`/`preferred` |

Cộng hai nhóm phụ: **Tuyển dụng** (`applications`, `application_status_history`, `match_results`) và **Danh mục** (`skills`, `skill_aliases`, `locations`).

## Quan hệ chính

- `users` 1–1 `candidates` (qua `candidates.user_id`) hoặc 1–1 `recruiters`; recruiter thuộc đúng một `companies`.
- `companies` 1–n `jobs`; `jobs` n–n `skills` qua `job_skills` (cột `priority` phân biệt bắt buộc/ưu tiên). `candidates` n–n `skills` qua `candidate_skills`.
- `candidates` 1–n `resumes` (một CV đang dùng, `is_active`).
- `applications` nối `candidates` và `jobs` (UNIQUE `candidate_id, job_id` chặn nộp trùng), lưu `status` (6 giá trị) và `match_score` tại lúc nộp; mỗi lần đổi trạng thái thêm một dòng `application_status_history` (`from_status` rỗng ở dòng đầu). Phễu BI đếm hồ sơ *từng đạt* mỗi bước từ bảng lịch sử, không đếm theo trạng thái hiện tại.
- `match_results` lưu điểm theo `model` (m0–m4) và `model_version`, UNIQUE `candidate_id, job_id, model_version`.
- `skills` 1–n `skill_aliases` (ví dụ `reactjs` → React) để chuẩn hoá khi trích kỹ năng.

## Ràng buộc nổi bật

`CHECK` cho `users.role`, `jobs.status/level/job_type/work_mode`, `job_skills.priority`, `applications.status` (6 giá trị) và `match_score` 0–100, `match_results.model`, khoảng lương `min ≤ max`, `education_level` 0–4. Danh sách đầy đủ ở `erd.dbml`.

## Liên hệ với kho dữ liệu hình sao (bài trước)

Theo kế hoạch (PDF mục 2.7), mô hình hình sao `FACT_GHEP_NOI_UNG_TUYEN` của bài cá nhân được giữ nhưng triển khai bằng **SQL view** trên chính CSDL tác nghiệp, không dựng kho riêng, vì quy mô chỉ vài trăm bản ghi. Hai thay đổi so với bài cũ: chiều công việc (`DIM_CONG_VIEC`) thêm cột lương, và bảng sự kiện thêm ngày theo từng trạng thái.

Trong repo hiện thực này bằng bốn view ở `bi/views.sql`:

| View | Vai trò trong mô hình hình sao |
|---|---|
| `v_skill_supply_demand` | Cung (ứng viên) và cầu (tin) theo chiều kỹ năng |
| `v_salary` | Lương theo chiều công việc (cấp bậc, nhóm nghề, thời gian) – cột lương bổ sung ở `DIM_CONG_VIEC` |
| `v_funnel`, `v_funnel_stages` | Bảng sự kiện ghép nối ứng tuyển; số hồ sơ từng đạt mỗi bước lấy từ `application_status_history` (thời điểm từng trạng thái) |

Chiều thời gian, địa điểm, công ty, kỹ năng lấy trực tiếp từ `jobs.posted_at`, `locations`, `companies`, `skills`, nên không có bảng chiều vật lý riêng.
