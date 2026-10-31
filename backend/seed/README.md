# Dữ liệu seed và định dạng file

Mọi CSV: UTF-8 (không BOM), dấu phẩy ngăn cột, bọc `"` nếu ô có dấu phẩy. Danh sách trong một ô ngăn bằng `|`.
Các file trong `data/` hiện chỉ là **mẫu 3 dòng**; Hoàng Hưng thay bằng dữ liệu đầy đủ, giữ nguyên tên cột.

| File | Người tạo | Cột |
|---|---|---|
| `data/skills.csv` | Hoàng Hưng | `name,category` |
| `data/skill_aliases.csv` | Hoàng Hưng | `alias,skill_name` |
| `data/occupation_templates.csv` | Hoàng Hưng | `occupation,core_skills,optional_skills` |
| `data/companies.csv` | Hoàng Hưng | `name,industry,size_range,location` |
| `data/jobs.csv` | Hoàng Hưng | `external_id,company_name,title,category,level,job_type,work_mode,location,salary_min,salary_max,min_years_exp,min_education,posted_at,deadline,description,responsibilities,required_skills,preferred_skills` |
| `data/candidates_generated.csv` | `gen_candidates.py` (Thái Anh) | `candidate_id,occupation,skills,years_exp,education_level,locations,work_types,expected_salary_min,expected_salary_max,text` |
| `labels/labels_pairs_<tên>.csv` | Hoàng Hưng, Hoàng Anh | `candidate_id,job_id,label` |
| `labels/labels_cv_skills.csv` | Hoàng Anh | `cv_file,skills` (+ cột tuỳ chọn `years_exp`) |

Quy ước giá trị:

- `category` ∈ 10 giá trị của `JobCategory` ở `src/types/index.ts`.
- `level` ∈ `intern|fresher|junior|middle|senior`; `job_type` ∈ `full_time|part_time|internship`; `work_mode` ∈ `onsite|hybrid|remote`.
- `salary_min/max`: triệu VNĐ/tháng; để trống = thoả thuận.
- `min_education` và `education_level`: số **0–4** (0 không yêu cầu/không rõ, 1 Trung cấp, 2 Cao đẳng, 3 Đại học, 4 Thạc sĩ trở lên).
- `locations`, `work_types` của ứng viên: danh sách `|`; `work_types` dùng nhãn tiếng Việt như frontend (`Toàn thời gian`, `Bán thời gian`, `Thực tập`, `Remote`).
- `candidate_id`, `job_id` trong file nhãn là **mã ngoài**: `candidate_id` trong `candidates_generated.csv`, `job_id` = `external_id` trong `jobs.csv`.
- Kỹ năng phải trùng đúng tên trong `skills.csv` và chỉ là kỹ năng đơn (không `A hoặc B`).

`make_pair_list.py` sinh `labels/labels_pairs_template.csv` (30 ứng viên × 10 tin, cột `label` để trống).
