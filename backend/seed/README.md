# Dữ liệu seed và định dạng file

Mọi CSV: UTF-8 (không BOM), dấu phẩy ngăn cột, bọc `"` nếu ô có dấu phẩy. Danh sách trong một ô ngăn bằng `|`.
Các file trong `data/` là **dữ liệu hư cấu đầy đủ** do các script ở thư mục này sinh ra (seed cố định 42), gồm 108 kỹ năng, 259 alias, 30 công ty, 150 tin, 300 ứng viên. Hoàng Hưng có thể thay/bổ sung bằng dữ liệu tự biên soạn, giữ nguyên tên cột; chạy lại `python -m seed.load_seed --reset` để nạp.

| File | Người tạo | Cột |
|---|---|---|
| `data/skills.csv` | Hoàng Hưng | `name,category` |
| `data/skill_aliases.csv` | Hoàng Hưng | `alias,skill_name` |
| `data/occupation_templates.csv` | Hoàng Hưng | `occupation,core_skills,optional_skills` |
| `data/companies.csv` | Hoàng Hưng | `name,industry,size_range,location` |
| `data/skill_learning_steps.csv` | Hoàng Hưng | `skill_name,steps` (các bước ngăn bằng `\|`; kỹ năng không có dòng dùng lộ trình mặc định) |
| `data/jobs.csv` | Hoàng Hưng | `external_id,company_name,title,category,level,job_type,work_mode,location,salary_min,salary_max,min_years_exp,min_education,posted_at,deadline,description,responsibilities,required_skills,preferred_skills` |
| `data/candidates_generated.csv` | `gen_candidates.py` | `candidate_id,occupation,skills,years_exp,education_level,locations,work_types,expected_salary_min,expected_salary_max,text` + cột phụ `full_name,university,year,major,phone,career_goal` |
| `data/cv_manifest.csv` | `gen_cv_files.py` | `cv_file,candidate_id,occupation,true_skills,true_years_exp,true_education_level,layout` – đáp án **tổng hợp** của trình sinh, KHÔNG phải nhãn tay |
| `data/legacy_jobs.json` | `scripts/export-legacy-jobs.ts` | 12 tin mẫu của frontend, hồ sơ demo |
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

## Chạy

```bash
cd backend
python -m seed.gen_data          # skills, aliases, learning steps, companies, jobs, locations (cần data/legacy_jobs.json)
python -m seed.gen_candidates    # 300 ứng viên
python -m seed.gen_cv_files      # 50 CV PDF/DOCX trong cv_files/ + cv_manifest.csv
python -m seed.load_seed --reset # nạp vào CSDL (DATABASE_URL), sinh ~1.200 đơn ứng tuyển
python -m seed.make_pair_list    # 30 ứng viên x 10 tin để gán nhãn
```

Tài khoản demo, mật khẩu chung `Demo@12345`: `admin@smartcareer.vn`, `hr01@smartcareer.vn` … `hr30@smartcareer.vn`,
`tung.demo@smartcareer.vn` (ứng viên demo), `cand0001@example.edu.vn` … `cand0300@example.edu.vn`.

## Lưu ý trung thực

- Đơn ứng tuyển và lịch sử trạng thái là **mô phỏng**; xác suất đi tiếp mỗi bước không phụ thuộc điểm khớp, nên biểu đồ "tỷ lệ tuyển theo nhóm điểm"
  chỉ minh hoạ cách tính. Hiệu quả mô hình chỉ kết luận từ nhãn tay.
- CV và `cv_manifest.csv` là dữ liệu tổng hợp; kết quả parser trên bộ này chỉ là kiểm tra luồng, không thay cho bảng P/R/F1 trên nhãn tay.
