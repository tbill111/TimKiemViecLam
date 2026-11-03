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

Ở bài này CSDL là mô hình quan hệ chuẩn hoá phục vụ ứng dụng; phần phân tích được dựng bằng bốn view SQL trong `bi/views.sql` (`v_skill_supply_demand`, `v_salary`, `v_funnel`, `v_funnel_stages`) trên các bảng trên. TODO (Hoàng Anh): đối chiếu từng bảng sự kiện/chiều của kho hình sao ở PDF kế hoạch mục 2.7 với các view này; repo không chứa mô tả kho cũ nên chưa viết chi tiết ở đây.
