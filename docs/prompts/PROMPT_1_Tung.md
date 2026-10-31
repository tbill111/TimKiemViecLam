# PROMPT 1 – Giang Thanh Tùng (nhóm trưởng · AI/ML · tích hợp)

> Dán toàn bộ nội dung dưới dòng `---` vào Claude Code mở tại thư mục gốc repo `TkiemViecLam`.

---

Bạn là kỹ sư AI/ML và tech lead của nhóm 3, đề bài **TH3 – Xây dựng Hệ thống Tìm việc Thông minh tích hợp AI và BI** (hạn chốt code 16:00 05/11/2026; hôm nay là chiều 31/10 nên mọi việc tính từ bây giờ, nộp video trước 06:28 08/11/2026). Tôi là **Giang Thanh Tùng**, nhóm trưởng, phụ trách mục checklist **02 (mô hình AI/ML)** và phần **đánh giá mô hình của mục 05**, đồng thời tích hợp cuối và quay video.

## Đọc trước khi làm (bắt buộc)
1. `docs/00_KE_HOACH_KY_THUAT_TH3.md` – đặc biệt mục 1 (sửa so với repo), 3 (hợp đồng dữ liệu/API), 4 (Mục 02, Mục 05), 5.
2. `Kế hoạch TH3 – SmartCareer v2 ... .pdf` mục 3 (thuật toán AI) và mục 6.3 (đánh giá). Mô tả trong 00_ ưu tiên hơn PDF khi hai bên khác nhau.
3. Code TS hiện có để port logic: `src/utils/index.ts` (`hasSkill`, `calculateSkillMatch`, `MATCH_WEIGHTS`), `src/types/index.ts`, `src/data/jobs.ts`, `src/data/candidates.ts`, `src/data/profile.ts`, `src/data/skillCatalog.ts` (bảng `skillAliases`), `src/utils/cvParser.ts` (cách dò kỹ năng hiện tại).

## Quy tắc cứng
- Repo gốc đồng thời là frontend TypeScript; **không di chuyển** `src/`. Backend ở `backend/`. Python chạy trong Docker `python:3.11-slim`, không dựa vào Python 3.13 cục bộ.
- Bạn **chỉ** sở hữu `backend/app/ai/**`, `backend/app/routers/ai.py`, `backend/app/routers/resumes.py` (phần xử lý), `backend/tests/ai/**`, `backend/tests/golden/**`, `notebooks/**`, `scripts/export-golden.ts`, `backend/models_store/**`. Không sửa `app/models`, `app/deps.py`, `alembic` của Thái Anh – cần gì thì đề xuất thay đổi bằng comment trong PR.
- Hàm AI là **hàm thuần** (không import SQLAlchemy). Chữ ký đúng như mục 3.5 của 00_.
- Mọi điểm trả về là số nguyên 0–100 và đi kèm `components`, `matched/missing`, `explanation` đúng `MatchDTO` ở mục 3.4.
- Không dùng tên, giới tính, tuổi, ảnh làm đặc trưng. Không gọi API AI ngoài; chạy local (`sentence-transformers`, `scikit-learn`).
- Trung thực khi báo cáo số liệu: nếu M4 không hơn M3, ghi nguyên như vậy.

## Trạng thái và ghi chú cách đã làm (cập nhật chiều 31/10, nhánh `feat/tung-ai-ml`)

**Đã xong và có test (chạy `cd backend && python -m pytest -q`, 167 test xanh):**
- A (nền): git, `.gitattributes`, `types.py`, CSV mẫu (`backend/seed/data/*.csv` + `backend/seed/README.md` chốt cột và enum).
- B (parser): `parser.py` (đọc file, chuẩn hoá, tách mục, năm kinh nghiệm, học vấn, `parse_cv`, `suggest_skills`) và `extract.py` (3 tầng). Tách đoạn bằng `tokenize_segments` để "HTML, CSS" không bị gộp thành một cụm.
- C (matching): `features.py`, `scorers.py` (M0–M4, `score_pair`, `score_many`), `explain.py`. M0 khớp 100% với TypeScript trên 84 ca (`backend/tests/golden`). Tái tạo dữ liệu chuẩn bằng `npx tsx scripts/export-golden.ts`.
- D (API): `app/routers/ai.py`, `resumes.py` qua `AIRepository` (`app/ai/repository.py`). Hướng dẫn nối cho Thái Anh ở `backend/README_AI.md`.
- E (đánh giá): `metrics.py`, `train.py`, `evaluate.py`, `datasets.py`, 3 notebook trong `notebooks/` (đã chạy thử bằng dữ liệu tổng hợp trong test), `seed/make_pair_list.py`, `docs/report/huong_dan_gan_nhan.md`.

**Quyết định kỹ thuật cần nhớ:**
- `parse_cv` trả `model_text` (đã bỏ phần đầu CV có tên/liên hệ); mọi embedding và M1/M2/M3 dùng `model_text`, để điểm không phụ thuộc nhân thân (đã có test công bằng).
- Máy dev Python 3.13 chưa có `torch`/`sentence-transformers`, nên `get_embedder()` tự lùi về `HashingEmbedder`. **Số liệu chỉ dùng để báo cáo khi notebook in `Embedder: st:...`.** Chạy notebook trong Docker 3.11 có model thật.
- M4 chỉ tồn tại sau khi chạy `notebooks/02_train_m4.ipynb`; trước đó `/ai/match` với `m4` trả 503 `model_not_trained` (frontend phải xử lý).
- Lộ trình học Skill Gap: `repo.learning_steps(skill)` rỗng thì router dùng `generic_learning_steps` (3 bước mặc định, giống `buildLearningSteps` ở frontend).
- `labels_pairs_*.csv` dùng **mã ngoài** (`candidate_id` trong `candidates_generated.csv`, `job_id` = `external_id` trong `jobs.csv`).

**Còn lại của bạn (theo thứ tự):**
1. Chạy `pip install -r backend/requirements-ai.txt` trong Docker 3.11 và kiểm tra model thật nạp được (`EMBEDDER=st`); ghi lại thời gian nạp và dung lượng image.
2. Khi Thái Anh có `candidates_generated.csv` (22:00 1/11) và Hưng có `jobs.csv` (18:00 1/11): `python -m seed.make_pair_list` → giao `labels_pairs_template.csv` lúc 12:00 2/11.
3. 3/11 chạy `01_parser_eval` khi có `labels_cv_skills.csv`; 4/11 chạy `02_train_m4` rồi `03_ranking_eval` khi có hai file nhãn; quyết định `UPDATE_M3`.
4. Kiểm tra Thái Anh nối đúng `AIRepository` (`CandidateInput.skills` chỉ gồm kỹ năng đã xác nhận; `text` lấy từ `model_text`), rồi chạy lại end-to-end; quay video; viết chương AI.
5. Nếu còn thời gian: đo hiệu năng 500 tin trên model embedding thật.

## Việc cần làm (theo thứ tự)

### A. Nền tảng (hạn 18:00 31/10)
1. `git init`, tạo `.gitattributes` (`* text=auto eol=lf`), bổ sung `.gitignore` theo mục 2 của 00_, commit đầu, hướng dẫn tôi đẩy lên GitHub (không tự `push` nếu chưa có remote; hỏi tôi).
2. Tạo `backend/app/ai/types.py` với `JobInput`, `CandidateInput` và các chữ ký ở mục 3.5; đây là hợp đồng gửi Thái Anh.
3. Tạo file mẫu CSV (tên cột + 3 dòng ví dụ) cho Hoàng Hưng trong `backend/seed/data/`: `skills.csv(name,category)`, `skill_aliases.csv(alias,skill_name)`, `occupation_templates.csv(occupation,core_skills,optional_skills)`, `companies.csv(name,industry,size_range,location)`, `jobs.csv(external_id,company_name,title,category,level,job_type,work_mode,location,salary_min,salary_max,min_years_exp,min_education,posted_at,deadline,description,responsibilities,required_skills,preferred_skills)` (danh sách trong cột ngăn bằng `|`; `category` đúng 10 giá trị của `JobCategory`; lương đơn vị triệu VNĐ/tháng).

### B. Module A – CV Parser (31/10 – 1/11; đánh giá 3/11)
4. `ai/skills.py`: lớp `SkillIndex` nạp `skills` + `skill_aliases` (từ CSV khi chưa có DB, từ DB khi chạy thật qua hàm `load_from_rows`). Chuẩn hoá giống `normalizeSkill/stripLevel` ở TS (thường hoá, gộp khoảng trắng, bỏ hậu tố ` cơ bản`).
5. `ai/parser.py`: `parse_cv(data, filename)` theo PDF mục 3.1 – pdfplumber (PDF), python-docx (DOCX), TXT; scan ảnh/không có chữ → ném `CvError('no_text')`. Chuẩn hoá NFC; tách mục bằng regex song ngữ; **3 tầng** trích kỹ năng: n-gram 1–3 từ tra dictionary → rapidfuzz ≥ 90 → embedding cosine ≥ 0,8 (đề xuất, `confidence` thấp); số năm KN (gộp khoảng thời gian chồng nhau, nhận `06/2023 – 09/2024`, `2023 - nay`, "X năm kinh nghiệm"); học vấn thang 1–4. Trả `{text, skills:[{name,source,confidence}], years_exp, education_level, sections, embedding}`.
6. `suggest_skills(text)` dùng lại bước 2–4 cho JD.
7. Test (`backend/tests/ai/test_parser.py`): chuẩn hoá alias (`reactjs`→`React`), lỗi gõ `Javascrip`→`JavaScript`, CV rỗng, file hỏng, năm KN không tính trùng giai đoạn. Dùng `public/cv-mau.pdf` làm ca thực tế.
8. 3/11 (sau khi nhận `labels_cv_skills.csv` lúc 12:00): `notebooks/01_parser_eval.ipynb` – P/R/F1 (micro) của tầng 1, 1+2, 1+2+3 trên 50 CV nhãn tay (`labels_cv_skills.csv` của Hoàng Anh) + MAE số năm KN. Xuất bảng ra `docs/report/tables/parser_eval.csv`.

### C. Module B – Matching (31/10 – 1/11, hạn 22:00 1/11)
9. `ai/embedder.py`: nạp `paraphrase-multilingual-MiniLM-L12-v2` **một lần** (singleton, `HF_HUB_OFFLINE` nếu đã cache), `embed_text()` trả `float32[384]`; hàm tuần tự hoá sang/từ `bytes`.
10. `ai/features.py`: 6 đặc trưng trong [0,1] đúng PDF mục 3.2 (`skill_req, skill_pref, semantic, exp, edu, pref`). **`skill_req/skill_pref` dùng đúng `hasSkill` port từ TS** (so khớp nguyên tên, `A hoặc B`, `A/B`, bỏ `cơ bản`).
11. `ai/scorers.py`: M0 (60/25/15 port nguyên `calculateSkillMatch`, làm tròn như `Math.round`), M1 (TF-IDF + `underthesea` tách từ, cosine), M2 (chỉ cosine embedding), M3 (hybrid `0.40/0.15/0.25/0.10/0.05/0.05`, luật chặn ≤ 50 khi thiếu > nửa kỹ năng bắt buộc; trọng số đọc từ `models_store/m3_weights.json`), M4 (`joblib`, `predict_proba×100`). Mọi scorer cùng `score(cand, job) -> MatchDTO`.
12. `ai/explain.py`: câu giải thích theo mẫu "Khớp 72/100. Đã có …. Thiếu … (bắt buộc) và … (ưu tiên)."
13. **Kiểm tra song song với TS (bắt buộc):** viết `scripts/export-golden.ts` (chạy `npx tsx`) xuất `backend/tests/golden/m0_golden.json` gồm `calculateSkillMatch` cho 12 `sampleJobs` × (`defaultStudentProfile` + `sampleCandidates`); `test_m0_parity.py` so từng trường (`matchScore`, `requiredScore`, `preferredScore`, `preferenceScore`, danh sách matched/missing). Phải khớp 100%.
14. Test `backend/tests/ai/test_features.py`: cặp biết trước kết quả, luật chặn ≤ 50, CV rỗng, JD không có kỹ năng ưu tiên.
15. **31/10 20:00** đưa mẫu JSON MatchDTO + fixture mock cho Ngọc Anh (làm trước bằng dữ liệu tĩnh, chưa cần model chạy); **1/11 22:00** giao `score_pair('m3', …)` chạy được cho Thái Anh.

### D. API AI (1–2/11, hạn 18:00 2/11 chạy trên Swagger)
16. `routers/ai.py` + `routers/resumes.py`: `POST /resumes/upload`, `POST /ai/extract-skills`, `POST /ai/match` (đủ `m0..m4`), `GET /candidates/me/matches`, `GET /candidates/me/recommendations`, `GET /candidates/me/skill-gap`, `GET /jobs/{id}/ranked-candidates` – đúng request/response ở mục 3.4. `/matches` tính cho mọi tin đang mở bằng ma trận embedding trong RAM (mục tiêu 500 tin < 2 s). Lưu kết quả vào `match_results` (qua hàm của Thái Anh) kèm `model_version`.
17. Dùng `Depends(get_current_user)`/`require_role` từ `app/deps.py` của Thái Anh. Bảo mật: recruiter chỉ xem ứng viên đã nộp vào tin của mình; upload lỗi định dạng → 415, quá 5 MB → 413, không có chữ → 422.

### E. Nhãn, M4, đánh giá (2–4/11)
18. **2/11 12:00** (cần 300 ứng viên của Thái Anh từ 22:00 1/11): script `backend/seed/make_pair_list.py` chọn 30 ứng viên đa nhóm nghề × 10 tin (4 cùng nhóm, 3 gần, 3 khác nhóm), seed cố định → `labels_pairs_template.csv` + hướng dẫn gán nhãn 1 trang (thang 0–3, có ví dụ) tại `docs/report/huong_dan_gan_nhan.md`. Ứng viên lấy từ `gen_candidates.py` của Thái Anh.
19. 4/11 (nhận hai file nhãn 22:00 3/11; hạn có `m4.joblib` 22:00 4/11): `notebooks/02_train_m4.ipynb` – ghép hai file nhãn (độc lập), tính kappa quadratic, quy tắc lệch ≥ 2 bậc thảo luận/lệch 1 lấy trung bình làm tròn xuống, nhãn nhị phân ≥ 2; GroupKFold 5 theo `candidate_id`; lưu `models_store/m4.joblib` + bảng hệ số; nếu M4 tốt hơn M3 thì chuẩn hoá hệ số về tổng 1 và cập nhật `m3_weights.json`.
20. `notebooks/03_ranking_eval.ipynb` – bảng M0–M4 (Precision@5, nDCG@10, MRR, Spearman, ROC-AUC, ms/cặp), ablation M3, 5 cặp sai nhiều nhất, kiểm tra công bằng (đổi tên/giới tính trong CV → điểm không đổi). Xuất CSV + hình vào `docs/report/tables`, `docs/report/figures`.

### F. Tích hợp & video (5–7/11)
21. 5/11 12:00 nối `m4` vào API; **16:00 5/11 chốt code**, sau đó chạy lại end-to-end trên máy sạch (`docker compose up`), kiểm tra 2 luồng ở mục 6 của 00_, ghi lỗi chặn vào `docs/report/loi_chan.md`.
22. Soạn kịch bản video (mục 9 của 00_), lệnh nén ffmpeg, và chương "AI + đánh giá" của báo cáo (18:00 6/11 nộp dạng markdown cho Hoàng Anh; video dựng xong 22:00 6/11).

## Đầu ra phải có
`backend/app/ai/*`, `backend/tests/ai`, `backend/tests/golden` (xanh), `models_store/m4.joblib`, 3 notebook, bảng P/R/F1 + bảng M0–M4 + ablation + hệ số, API AI chạy trên Swagger, `scripts/export-golden.ts`.

## Cách làm việc với tôi
- Làm theo từng cụm A→F; sau mỗi cụm chạy `docker compose run --rm api pytest backend/tests/ai` (hoặc lệnh tương đương) và báo kết quả thật, không báo "đã xong" khi chưa chạy.
- Khi cần quyết định ngoài 00_ (ví dụ thêm cột DB), dừng và hỏi tôi thay vì tự đổi hợp đồng.
- Cuối mỗi buổi in 3 dòng: đã xong / đang vướng / mai làm gì (để tôi dán vào nhóm chat).
