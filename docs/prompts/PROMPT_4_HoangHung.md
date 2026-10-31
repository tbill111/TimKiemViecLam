# PROMPT 4 – Hoàng Hưng (Dữ liệu · gán nhãn · biểu đồ Superset · chương BI)

> Dán nội dung dưới `---` vào Claude Code (hoặc chat AI) mở tại thư mục gốc repo `TkiemViecLam`. Phần việc của bạn **không cần code**; AI sẽ hỗ trợ soạn dữ liệu, kiểm tra định dạng và viết nội dung.

---

Bạn là trợ lý dữ liệu và tài liệu cho nhóm 3, đề bài **TH3 – Xây dựng Hệ thống Tìm việc Thông minh tích hợp AI và BI**. Tôi là **Hoàng Hưng**, phụ trách: dữ liệu mẫu (checklist **01** và **05**), biểu đồ Superset (**03**), người gán nhãn 1, và chương BI của báo cáo. Hôm nay là chiều 31/10, mọi việc tính từ bây giờ. Hạn: kỹ năng/alias/occupation **22:00 31/10**; công ty + tin **18:00 1/11**; 50 CV **12:00 2/11**; nhãn cặp **22:00 3/11**; chốt code 16:00 5/11.

## Đọc trước khi làm
1. `docs/00_KE_HOACH_KY_THUAT_TH3.md` – mục 1 (dòng 6, 10, 11 về `category`, kỹ năng đơn, `Remote`), 3.1, 4 (Mục 01, 03, 05), 5.
2. `Kế hoạch TH3 – SmartCareer v2 ... .pdf` mục 4.3 (bảng 8 biểu đồ) và 6.1–6.2 (dữ liệu, gán nhãn).
3. Dữ liệu hiện có để giữ phong cách: `src/data/jobs.ts` (12 tin mẫu), `src/data/skillCatalog.ts` (tên kỹ năng chuẩn + từ đồng nghĩa), `src/data/skillCategories.ts` (6 nhóm kỹ năng), `src/data/candidates.ts`. File mẫu CSV (tên cột + 3 dòng) Tùng gửi trong `backend/seed/data/`.

## Quy tắc cứng
- Đặt file đúng thư mục `backend/seed/data/` (CSV), **mã hoá UTF-8 (không BOM), dấu phẩy ngăn cột, bọc `"` khi ô có dấu phẩy**, danh sách trong một ô ngăn bằng `|`. Kiểm tra mở bằng Excel không vỡ tiếng Việt (lưu "CSV UTF-8").
- Tên kỹ năng phải **trùng chính tả** với tên chuẩn đã dùng trong code (ví dụ `React`, `Node.js`, `REST API`, `Power BI`, `Thống kê cơ bản`). Chỉ dùng kỹ năng **đơn**, không viết `A hoặc B`.
- `category` trong `jobs.csv` chỉ thuộc 10 giá trị: `Frontend Development`, `Backend Development`, `Data Science & Analytics`, `Business Analysis`, `QA & Testing`, `UI/UX Design`, `IT Support`, `Digital Marketing`, `Software Engineering`, `Business Operations`.
- Giá trị `level`: `intern/fresher/junior/middle/senior`; `job_type`: `full_time/part_time/internship`; `work_mode`: `onsite/hybrid/remote`; `location` ví dụ: `Hà Nội`, `Hồ Chí Minh`, `Đà Nẵng`, `Remote`; `salary_min/max` đơn vị **triệu VNĐ/tháng** (số, có thể để trống = thỏa thuận); `posted_at` dạng `YYYY-MM-DD` rải đều 12 tháng gần nhất (từ 2025-11 tới 2026-10).
- Dữ liệu **hư cấu hoàn toàn**: tên công ty, người, email; không copy từ TopCV/LinkedIn (điều khoản không cho phép). Nếu dùng dữ liệu Kaggle phải ghi nguồn + giấy phép trong `docs/report/nguon_du_lieu.md`.
- Lương có xu hướng tăng nhẹ theo thời gian và theo cấp bậc (để biểu đồ lương có ý nghĩa).

## Ghi chú định dạng đã chốt (xem `backend/seed/README.md` và các file mẫu trong `backend/seed/data/`)

- File mẫu 3 dòng đã có sẵn cho `skills.csv`, `skill_aliases.csv`, `occupation_templates.csv`, `companies.csv`, `jobs.csv`: **giữ nguyên tên cột và thứ tự cột**, thay bằng dữ liệu đầy đủ.
- `min_education` trong `jobs.csv` là **số 0–4** (0 không yêu cầu, 1 Trung cấp, 2 Cao đẳng, 3 Đại học, 4 Thạc sĩ+).
- Thêm file **`skill_learning_steps.csv`** (`skill_name,steps`, 3 bước ngăn bằng `|`) cho các kỹ năng hay thiếu nhất (khoảng 20–30 kỹ năng; có thể lấy từ `src/data/skillGap.ts`). Kỹ năng chưa có dòng sẽ dùng lộ trình mặc định.
- Danh sách trong một ô (ví dụ `required_skills`) ngăn bằng `|`, tên kỹ năng phải trùng `skills.csv`.
- File nhãn đặt trong `backend/seed/labels/`, tên `labels_pairs_hung.csv`, cột `candidate_id,job_id,label`. `candidate_id` lấy từ `candidates_generated.csv`, `job_id` là `external_id` của `jobs.csv` (ví dụ `job-001`). Nhãn 0–3, đủ 300 dòng, giữ nguyên thứ tự của file mẫu.
- 50 file CV đặt trong `backend/seed/cv_files/` và **được commit** (dữ liệu hư cấu). Để parser đọc tốt: PDF phải có lớp chữ (xuất từ Word/Google Docs, không chụp ảnh); có tiêu đề mục như "Kỹ năng", "Kinh nghiệm", "Học vấn", "Dự án"; thời gian viết dạng `06/2023 - 09/2024` hoặc `2023 - nay`; phần đầu CV (tên, liên hệ) nằm riêng phía trên các mục; kỹ năng liệt kê cách nhau dấu phẩy hoặc xuống dòng.

## Việc cần làm

### A. Danh mục kỹ năng (hạn 22:00 31/10)
1. `skills.csv` (`name,category`): **≥ 80 kỹ năng**, 6 nhóm: `Frontend`, `Backend`, `Dữ liệu`, `DevOps`, `Thiết kế`, `Kỹ năng mềm`. Bao gồm toàn bộ kỹ năng trong `skillCatalog.ts`.
2. `skill_aliases.csv` (`alias,skill_name`): **≥ 150 alias** (viết thường), ví dụ `reactjs→React`, `nodejs→Node.js`, `postgres→PostgreSQL`, cả tiếng Việt lẫn Anh, lỗi gõ phổ biến. Không dùng viết tắt quá ngắn dễ nhầm (`js`, `ts`).
3. `occupation_templates.csv` (`occupation,core_skills,optional_skills`) cho ~8 nhóm nghề, khớp `JobCategory` (dùng để sinh ứng viên/CV).

### B. Công ty + tin tuyển dụng (hạn 18:00 1/11)
4. `companies.csv` – **30 công ty hư cấu** (`name,industry,size_range,location`), rải nhiều ngành.
5. `jobs.csv` – **150 tin**, **đã bao gồm 12 tin cũ** trong `src/data/jobs.ts` (giữ `external_id` = `job-001`…`job-012`; tin có `'React hoặc Node.js'` đổi thành `React`, `Node.js` ở `preferred_skills`). Mỗi tin có `description`, 3–5 `responsibilities`, 3–6 kỹ năng bắt buộc, 0–4 ưu tiên, đủ 5 cấp bậc, nhiều nhóm nghề, ngày đăng rải đều 12 tháng. JD sinh theo mẫu: chọn vị trí → bộ kỹ năng → viết mô tả.
6. Cho AI kiểm tra tự động (viết script ngắn trong scratch, không commit) rằng: không có kỹ năng ngoài `skills.csv`; không có hai tin trùng `title+company`; `salary_min ≤ salary_max`; mọi `company_name` có trong `companies.csv`. Sửa tới khi sạch rồi mới giao Thái Anh.

### C. 50 file CV (1/11 – hạn 12:00 2/11)
7. Dựng **50 file CV PDF/DOCX** (khác bố cục: 1 cột, 2 cột, bảng, tiêu đề tiếng Việt/Anh…) vào `backend/seed/cv_files/`, tên `cv_001.pdf … cv_050.pdf`, nội dung hư cấu theo nhóm nghề (có mục kỹ năng/kinh nghiệm/học vấn/dự án, có khoảng thời gian kiểu `06/2023 – 09/2024`, `2023 - nay`). Có thể dùng `public/cv-mau.pdf` làm mẫu bố cục. Mỗi CV có `cv_file` + danh sách kỹ năng "đúng" bạn chủ động ghi lại để Thái Anh ghép hồ sơ (`backend/seed/data/cv_manifest.csv`: `cv_file,candidate_name,occupation`). Không dùng thông tin người thật.

### D. Gán nhãn cặp CV–JD (người gán 1, từ 12:00 2/11, hạn 22:00 3/11)
8. Nhận `labels_pairs_template.csv` từ Tùng (12:00 2/11) + `docs/report/huong_dan_gan_nhan.md`. Thang: `0` không phù hợp, `1` ít, `2` phù hợp, `3` rất phù hợp. **Gán độc lập, không nhìn điểm hệ thống, không trao đổi với Hoàng Anh.** Lưu `labels_pairs_hung.csv` (`candidate_id,job_id,label`), đủ 300 cặp (tối thiểu 200 nếu trễ, báo Tùng).
9. AI hỗ trợ: tạo bảng đọc nhanh (ứng viên + tin cạnh nhau) để gán nhãn thuận tiện; **không** để AI tự gán nhãn thay tôi.

### E. Biểu đồ Superset (nhận Superset 22:00 2/11; làm 3–4/11)
10. Mở Superset, tạo 3 dataset từ `v_skill_supply_demand`, `v_salary`, `v_funnel`; dựng dashboard **"Thị trường tuyển dụng"** theo bảng 4.3 PDF: bắt buộc **biểu đồ 2** (Top 15 kỹ năng theo số ứng viên, Bar), **4** (trung vị lương theo tháng/cấp bậc, Line), **6** (phễu Applied→Screening→Interview→Offer→Hired, Funnel); mở rộng tối thiểu 2 trong **1, 3, 5, 7, 8** (nên có 8). Native Filters: thời gian, địa điểm, cấp bậc, nhóm kỹ năng. Đặt tên chart tiếng Việt, rõ đơn vị (triệu VNĐ/tháng).
11. 4/11: hoàn thiện biểu đồ mở rộng + bộ lọc; **Export dashboard** → `bi/superset/dashboard_export.zip`; kiểm tra import lại được trên Superset sạch.
12. Đối chiếu số: 3 chỉ số bắt buộc trên dashboard phải khớp truy vấn SQL tay (nhờ AI soạn truy vấn đối chiếu, ghi kết quả vào `docs/report/bi_doi_chieu.md`).
13. 5/11 (hạn 12:00): chụp ảnh dashboard (`bi/screenshots/*.png`) và viết **3–4 nhận định rút từ số liệu** (ví dụ kỹ năng thiếu người nhất = cầu/cung cao nhất; bước rơi nhiều nhất trong phễu; nhóm điểm khớp nào có tỷ lệ tuyển cao hơn). **Trung thực:** dữ liệu ứng tuyển là mô phỏng nên biểu đồ 8 chỉ minh hoạ cách tính, không kết luận mô hình tốt.

### F. Báo cáo (5–6/11)
14. Viết **chương BI**: 3 chỉ số đề bài nêu, định nghĩa chỉ số (PDF 4.1), 3 view SQL, danh sách biểu đồ, ảnh + nhận định, cách nhúng, hạn chế. Nộp markdown 12:00 6/11 cho Hoàng Anh.

## Đầu ra phải có
`skills.csv`, `skill_aliases.csv`, `occupation_templates.csv`, `companies.csv`, `jobs.csv`, 50 CV + `cv_manifest.csv`, `labels_pairs_hung.csv`, dashboard Superset + `dashboard_export.zip`, ảnh dashboard + nhận định, `bi_doi_chieu.md`, chương BI.

## Cách làm việc với tôi
- Làm theo cụm A→F; mỗi lần giao file, AI chạy kiểm tra định dạng và báo kết quả thật (số dòng, lỗi tìm thấy).
- Khi chưa chắc tên kỹ năng/giá trị enum, hỏi lại thay vì tự đặt.
- Cuối buổi in 3 dòng: đã xong / đang vướng / mai làm gì (để dán vào nhóm chat 22:00).
