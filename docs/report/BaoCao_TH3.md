# TH3 – Xây dựng Hệ thống Tìm việc Thông minh tích hợp AI và BI (SmartCareer v2)

> **Bản nháp trên nhánh backup.** Mọi số liệu về hệ thống, CSDL, API, BI và hiệu năng là số đo thật (nguồn ghi ở từng mục).
> Mọi số liệu *đánh giá mô hình* ở chương 6 được tính trên **nhãn mô phỏng** (`backend/seed/labels/README_SYNTHETIC.md`), chỉ chứng minh quy trình chạy được.
> Trước khi nộp phải gán nhãn tay, chạy lại 3 notebook (hướng dẫn ở `docs/E2E.md`) và thay các bảng đánh dấu **[THAY BẰNG NHÃN TAY]**.

## 1. Giới thiệu

**Bài toán.** Sinh viên và người mới tốt nghiệp khó biết mình phù hợp vị trí nào và còn thiếu kỹ năng gì; nhà tuyển dụng phải sàng lọc nhiều hồ sơ chất lượng không đều.
**Mục tiêu.** Xây một nền tảng (1) tự động khớp kỹ năng ứng viên với yêu cầu công việc bằng điểm Matching Score *có giải thích*; (2) cung cấp dashboard BI cho nhà tuyển dụng về ứng viên theo kỹ năng, xu hướng lương và tỷ lệ chuyển đổi tuyển dụng; (3) kiểm thử và đánh giá hiệu quả mô hình gợi ý.
**Kế thừa.** Prototype React ở bài cá nhân (10 màn hình, dữ liệu mẫu, điểm khớp 60/25/15) được giữ làm baseline M0 và chế độ demo; bài này thêm backend, CSDL, mô hình AI/ML, BI và đánh giá.
**Kiến trúc.** 4 dịch vụ Docker Compose: `db` (PostgreSQL 16), `api` (FastAPI + tầng AI), `superset` (BI), `web` (React + nginx).

## 2. Phân tích yêu cầu và thiết kế CSDL (mục 01)

- Tác nhân, 10 chức năng F01–F10 và yêu cầu phi chức năng: `docs/report/01_phan_tich_yeu_cau.md`.
- Use Case: ![Use Case](../usecase/usecase.png) Đặc tả 3 ca (Tải CV, Xem việc gợi ý, Đổi trạng thái): `docs/usecase/dac_ta_use_case.md`.
- ERD 15 bảng chia theo ba đối tượng của đề (ứng viên, nhà tuyển dụng, tin tuyển dụng) cộng đơn ứng tuyển và danh mục/AI: ![ERD](../erd/erd.png)
- DDL PostgreSQL: `backend/schema.sql` (sinh từ models, có test chống lệch); migration Alembic `0001` (15 bảng), `0002` (4 view BI), `0003` (cột `candidates.embedding`).
- Dữ liệu (hư cấu, seed cố định 42; không thu thập từ TopCV/LinkedIn): 108 kỹ năng, 259 từ đồng nghĩa, 30 công ty, 150 tin rải đều 12 tháng, 301 ứng viên, 50 CV PDF/DOCX có 5 bố cục, 1.255 đơn ứng tuyển kèm lịch sử trạng thái (`backend/seed/README.md`).

## 3. Mô hình AI (mục 02)

**Module A – CV Parser** (`backend/app/ai/parser.py`, `extract.py`): đọc PDF/DOCX/TXT; chuẩn hoá Unicode; tách mục song ngữ; trích kỹ năng 3 tầng (n-gram với từ điển và alias → so khớp mờ rapidfuzz ngưỡng 90 → embedding cosine ≥ 0,8 chỉ để đề xuất); số năm kinh nghiệm (gộp khoảng thời gian chồng nhau, bỏ mục học vấn); học vấn thang 1–4. Phần đầu CV (tên, tuổi, liên hệ) bị loại khỏi văn bản dùng chấm điểm để mô hình không dùng thông tin nhân thân.

**Module B – Matching Score** (`features.py`, `scorers.py`): 6 đặc trưng trong [0,1]: `skill_req`, `skill_pref`, `semantic` (cosine embedding `paraphrase-multilingual-MiniLM-L12-v2`), `exp`, `edu`, `pref`. Năm phương pháp cùng giao diện:

| Mã | Phương pháp | Vai trò |
|---|---|---|
| M0 | Quy tắc 60/25/15 (port đúng `calculateSkillMatch`; khớp bản TypeScript 100% trên 84 ca) | Baseline kế thừa |
| M1 | TF-IDF + cosine CV–JD | Baseline NLP cổ điển |
| M2 | Chỉ embedding | Đo riêng ngữ nghĩa |
| M3 | Hybrid `0,40/0,15/0,25/0,10/0,05/0,05` + luật chặn ≤ 50 khi thiếu hơn nửa kỹ năng bắt buộc | Mặc định triển khai |
| M4 | Logistic Regression học trọng số trên 6 đặc trưng, GroupKFold 5 theo ứng viên | Phần "Machine Learning" |

Mỗi lần chấm trả về điểm 0–100, 6 điểm thành phần, kỹ năng có/thiếu và một câu giải thích (ví dụ: "Khớp 72/100. Đã có React, Git. Thiếu TypeScript (bắt buộc) và REST API (ưu tiên).").

## 4. Dashboard BI (mục 03)

Ba chỉ số của đề bài đều có view SQL (`bi/views.sql`), API dự phòng (`/api/bi/*`) và biểu đồ Superset:

| Chỉ số | View | Biểu đồ |
|---|---|---|
| Số ứng viên theo kỹ năng | `v_skill_supply_demand` | 2 (bắt buộc), 3 |
| Xu hướng lương | `v_salary` | 4 (bắt buộc) |
| Tỷ lệ chuyển đổi tuyển dụng | `v_funnel`, `v_funnel_stages` | 6 (bắt buộc), 1, 8 |

Phễu đếm hồ sơ *từng đạt* mỗi bước từ `application_status_history` (không đếm theo trạng thái hiện tại). Dashboard nhúng vào trang nhà tuyển dụng bằng guest token; RLS `company_id` làm mỗi công ty chỉ thấy số của mình.

**Đã kiểm chứng thật (PostgreSQL 16 + Superset 4.1.1):** 4 view khớp API từng con số (`scripts/check_bi_views.py`); công ty 1 thấy 19 hồ sơ, công ty 5 thấy 63, quản trị thấy 1.255 qua guest token; `bi_reader` chỉ đọc được view. Ảnh: ![Dashboard nhúng Superset](../../bi/screenshots/dashboard_superset_embedded.png) Tệp xuất `bi/superset/dashboard_export.zip` nhập lại được.

**Nhận định** (đầy đủ ở `bi/NHAN_DINH.md`; dữ liệu mô phỏng nên chỉ minh hoạ cách đọc): chuyển đổi tổng 9,9% (124/1.255), trung vị 16,4 ngày đến khi tuyển; bước rơi lớn nhất là từ phỏng vấn lên đề nghị (39,4%); Jira và Viết test case có cầu bằng cung (15 ứng viên/15 tin); lương trung vị tăng ở mọi cấp bậc (senior +15% … intern +2%) do trình sinh gài xu hướng; tỷ lệ tuyển theo nhóm điểm khớp chênh nhỏ vì dữ liệu mô phỏng không gắn kết quả với điểm.

## 5. Kiến trúc, API và giao diện (mục 04)

- **API** (Swagger `/docs`): xác thực JWT + phân quyền 3 vai trò; hồ sơ, tải CV (415/413/422/400 cho lỗi), tin, ứng tuyển với luật trạng thái `applied → screening → interview → offer → hired` (sai luật trả 409), việc đã lưu, AI (`/ai/match`, `/candidates/me/matches`, `/recommendations`, `/skill-gap`, `/jobs/{id}/ranked-candidates`, `/ai/extract-skills`), BI, quản trị danh mục (`docs/00_KE_HOACH_KY_THUAT_TH3.md` mục 3.4).
- **Giao diện:** đăng nhập/đăng ký; ứng viên: Tổng quan, Tìm việc, Phân tích CV–JD (chọn M0–M4, 6 thành phần, giải thích), Skill Gap, hồ sơ + tải CV, Việc đã lưu & Ứng tuyển; nhà tuyển dụng: Dashboard BI, Quản lý tin, Đăng tin (có gợi ý kỹ năng), Kanban 6 cột; quản trị: Quản lý kỹ năng. Mọi trang có trạng thái tải/lỗi/rỗng. Chế độ demo (`VITE_OFFLINE_DEMO=true`) chạy không cần backend.
- Ảnh các màn hình: tạo bằng `python scripts/e2e_smoke.py --shots <thư mục>` (14 ảnh).
- **Hiệu năng đo qua HTTP trên PostgreSQL + model thật:** chấm 1 cặp 38 ms (yêu cầu < 200 ms); 150 tin 38 ms; 500 tin 70–77 ms (yêu cầu < 2 s). Nhờ embedding hồ sơ, CV và tin được tính sẵn khi lưu; trước khi bổ sung cột `candidates.embedding`, chấm 1 cặp mất 417 ms.

## 6. Thực nghiệm và đánh giá (mục 05)

### 6.1. Dữ liệu và cách gán nhãn
30 ứng viên đều theo nhóm nghề × 10 tin (4 cùng nhóm, 3 gần, 3 khác nhóm) = 300 cặp; thang 0–3; hai người gán độc lập; kappa có trọng số bình phương, mục tiêu ≥ 0,6; lệch ≥ 2 bậc thì thảo luận; nhãn nhị phân "phù hợp" khi ≥ 2 (`docs/report/huong_dan_gan_nhan.md`).

> **[THAY BẰNG NHÃN TAY]** Kết quả dưới đây dùng nhãn mô phỏng: kappa = **0,826**, 8/300 cặp lệch ≥ 2 bậc, 37% cặp "phù hợp".

### 6.2. Kiểm thử hệ thống
- 236 test tự động (pytest): parser, đặc trưng, M0–M4, phân quyền, luật trạng thái, phễu BI, seed, migration, hiệu năng; M0 khớp TypeScript 100%; bộ test chạy lại trong container với model thật (223 đạt, 2 bỏ qua do thiếu file ngoài image).
- 44 test case theo F01–F10 và phi chức năng: `docs/testcases.md` (ca nào đã chạy thật ghi rõ).
- E2E trình duyệt: 14/14 bước trên stack Docker thật (ứng viên, nhà tuyển dụng, quản trị); chế độ demo 12/12 bước, 0 lời gọi API.
- Công bằng: hai CV chỉ khác phần đầu (tên, giới tính, tuổi, email) cho cùng kỹ năng, năm kinh nghiệm, học vấn và cùng điểm M3 (67).

### 6.3. Đánh giá Module A (CV Parser) – 50 CV
| Tầng | Precision | Recall | F1 |
|---|---|---|---|
| T1 từ điển + alias | 0,935 | 0,958 | 0,946 |
| T1+2 (+ so khớp mờ) | 0,929 | 0,961 | 0,945 |
| T1+2+3 (+ embedding) | 0,929 | 0,961 | 0,945 |

MAE số năm kinh nghiệm = 0. **[THAY BẰNG NHÃN TAY]** (số trên: nhãn CV mô phỏng; trên đáp án tổng hợp của trình sinh: F1 0,981 / 0,979 / 0,979). Nhận xét: tầng 2 và 3 gần như không cải thiện F1 ở bộ này vì CV chứa ít lỗi gõ và gần như không có cụm ngoài từ điển.

### 6.4. So sánh M0–M4 trên 30 ứng viên × 10 tin (M4 tính trên fold kiểm tra GroupKFold) **[THAY BẰNG NHÃN TAY]**
| Mô hình | Precision@5 | nDCG@10 | MRR | Spearman ρ | ROC-AUC | ms/cặp |
|---|---|---|---|---|---|---|
| M0 quy tắc 60/25/15 | 0,700 | 0,959 | 0,967 | 0,775 | 0,942 | 0,06 |
| M1 TF-IDF | 0,700 | 0,969 | 0,919 | 0,825 | 0,952 | 5,01 |
| M2 embedding | 0,687 | 0,968 | 0,950 | 0,794 | 0,905 | 0,07 |
| M3 hybrid | 0,700 | 0,974 | 0,950 | 0,796 | 0,959 | 0,08 |
| M4 Logistic Regression | 0,700 | 0,976 | 0,944 | 0,814 | 0,955 | — |

Nhận xét trung thực: chênh lệch giữa các mô hình nhỏ (nDCG@10 chỉ từ 0,959 đến 0,976) và chỉ dựa trên 30 ứng viên nên không đủ để khẳng định mô hình nào tốt hơn có ý nghĩa thống kê. Với nhãn mô phỏng, mọi mô hình dựa trên độ phủ kỹ năng đều được lợi vì nhãn sinh từ cùng loại thông tin. Cần nhãn tay để kết luận.

### 6.5. Ablation M3 (bỏ lần lượt một đặc trưng, đo nDCG@10) và hệ số M4 **[THAY BẰNG NHÃN TAY]**
| Bỏ đặc trưng | nDCG@10 | Thay đổi |
|---|---|---|
| (không bỏ) | 0,974 | — |
| `skill_req` | 0,915 | −0,059 |
| `skill_pref` | 0,955 | −0,019 |
| `semantic` | 0,963 | −0,011 |
| `exp` | 0,972 | −0,002 |
| `edu` | 0,976 | +0,002 |
| `pref` | 0,975 | +0,001 |

Hệ số M4 (chuẩn hoá): `skill_req` 5,04; `semantic` 2,44; `skill_pref` 2,40; `edu` 0,81; `exp` 0,74; `pref` −0,05, so với trọng số tay của M3 (0,40/0,25/0,15/0,05/0,10/0,05): thứ tự quan trọng gần như trùng nhau, `skill_req` nổi bật nhất. Đặc trưng `pref` không đóng góp.

### 6.6. Phân tích lỗi (5 cặp lệch nhiều nhất của M3) **[THAY BẰNG NHÃN TAY]**
Ba cặp của ứng viên cand-0220 (nhóm Business Operations, nhãn 0, điểm 49–54) được chấm khá cao dù ứng viên chỉ có các kỹ năng mềm/Excel trùng với yêu cầu (Giao tiếp, Tư duy phân tích, Excel) của các tin Business Analysis và Digital Marketing; hai cặp của cand-0029 (nhóm Software Engineering, nhãn 3) bị chấm đúng 50 vì thiếu JavaScript và Git (2/3–2/4 kỹ năng bắt buộc), dù ứng viên cùng nhóm nghề với tin: luật chặn ≤ 50 phạt nặng khi thiếu kỹ năng bắt buộc nhưng không có đặc trưng nào biểu diễn "đúng nhóm nghề". Hướng cải thiện: thêm đặc trưng nhóm nghề. (Số liệu từ nhãn mô phỏng, trong đó nhóm nghề chiếm 40% độ phù hợp tiềm ẩn nên lỗi kiểu này bị nhấn mạnh.)

## 7. Hạn chế và hướng phát triển
- Dữ liệu ứng viên, CV, tin và đơn ứng tuyển là mô phỏng; xu hướng lương và tỷ lệ tuyển chỉ minh hoạ cách tính.
- Chưa có nhãn tay; `models_store/m4.joblib` hiện huấn luyện trên nhãn mô phỏng (phiên bản `m4-SYNTHETIC-labels`, giao diện hiện cảnh báo). Phải huấn luyện lại bằng nhãn tay.
- Trích kỹ năng CV chủ yếu là từ điển + so khớp mờ + embedding; chưa có mô hình nhận dạng thực thể huấn luyện riêng (hướng: PhoBERT/NER).
- CV dạng ảnh scan không đọc được (hệ thống báo lỗi, không đoán).
- Hướng phát triển: học từ phản hồi thật của nhà tuyển dụng, thêm đặc trưng nhóm nghề, giao diện quản lý tin cho quản trị, Native Filters và biểu đồ 5, 7 của Superset.
