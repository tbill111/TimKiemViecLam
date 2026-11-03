# Chương AI – Mô hình phân tích CV và điểm tương thích (mục checklist 02)

> Bản nháp do Tùng soạn từ mã trên `main`. Mọi con số đo được ghi nguồn và điều kiện đo. **Bảng đánh giá hiệu quả mô hình (P/R/F1, so sánh M0–M4) chưa có**, vì repo chưa có nhãn; xem mục 8, không điền số ước chừng.

## 1. Bài toán và đầu ra

Đầu vào: một CV (PDF, DOCX hoặc TXT) hoặc hồ sơ ứng viên, và một tin tuyển dụng (JD). Đầu ra: điểm tương thích số nguyên từ 0 đến 100 (Matching Score), kèm sáu điểm thành phần, danh sách kỹ năng đã có và còn thiếu, và một câu giải thích. Cả năm mô hình M0–M4 dùng chung một giao diện và trả cùng một cấu trúc `MatchDTO`:

```
{model, model_version, total_score, components{skill_req, skill_pref, semantic, exp, edu, pref},
 matched_required, missing_required, matched_preferred, missing_preferred,
 location_match, work_type_match, explanation}
```

Với M0, ba thành phần `semantic`, `exp`, `edu` là `null` vì M0 không dùng chúng.

## 2. Kiến trúc

Tầng AI nằm ở `backend/app/ai/` và là **hàm thuần**, không import SQLAlchemy. Nó nhận dữ liệu qua hai kiểu `CandidateInput`, `JobInput` và một giao diện `AIRepository` (`repository.py`). Phía backend, `SqlAIRepository` (`app/services/ai_repo.py`) hiện thực giao diện này bằng PostgreSQL. Cách tách này cho phép kiểm thử tầng AI mà không cần cơ sở dữ liệu.

| Module | Việc |
|---|---|
| `parser.py` | đọc tệp, chuẩn hoá, tách mục, số năm kinh nghiệm, học vấn |
| `skills.py`, `extract.py` | chuẩn hoá kỹ năng, từ đồng nghĩa, trích kỹ năng 3 tầng |
| `embedder.py` | embedding 384 chiều (`paraphrase-multilingual-MiniLM-L12-v2`), có bản thay thế `HashingEmbedder` cho kiểm thử |
| `features.py` | sáu đặc trưng |
| `scorers.py` | M0–M4, `score_pair`, `score_many` |
| `explain.py` | câu giải thích |
| `metrics.py`, `train.py`, `evaluate.py` | đo lường và huấn luyện, dùng trong `notebooks/` |

## 3. Phân tích CV (Module A)

1. **Đọc tệp:** PDF bằng `pdfplumber`, DOCX bằng `python-docx`, TXT trực tiếp. CV dạng ảnh scan không có lớp chữ thì báo `no_text` (HTTP 422); tệp hỏng báo `corrupt` (422). Quá 5 MB trả 413, sai định dạng trả 415, thiếu ô đồng ý trả 400 `consent_required`.
2. **Chuẩn hoá:** Unicode NFC, tách các mục bằng từ khoá song ngữ (Kỹ năng/Skills, Kinh nghiệm/Experience, Học vấn/Education, Dự án/Projects).
3. **Số năm kinh nghiệm:** nhận các dạng `06/2023 – 09/2024`, `2023 – nay` và cụm "X năm kinh nghiệm"; các khoảng thời gian chồng nhau được gộp để không tính trùng.
4. **Học vấn:** quy về thang 0–4 (0 không rõ, 1 trung cấp, 2 cao đẳng, 3 đại học, 4 thạc sĩ trở lên).
5. **Trích kỹ năng 3 tầng:**
   - **Tầng 1 – từ điển:** tách chuỗi thành cụm 1–3 từ và tra danh mục kỹ năng cùng từ đồng nghĩa (ví dụ `reactjs` → React). Dấu phẩy, xuống dòng hay gạch đầu dòng là ranh giới cụm, nên "HTML, CSS" không bị gộp thành một kỹ năng.
   - **Tầng 2 – so khớp mờ:** `rapidfuzz` với ngưỡng 90 để bắt lỗi gõ như "Javascrip".
   - **Tầng 3 – embedding:** cosine với kỹ năng trong danh mục, ngưỡng 0,8. Kết quả tầng này chỉ là **gợi ý độ tin cậy thấp**, không tự tính vào hồ sơ.
   Người dùng luôn xem và xác nhận hoặc sửa; chỉ kỹ năng đã xác nhận ảnh hưởng điểm.
6. **Công bằng:** `parse_cv` trả `model_text`, là văn bản đã **bỏ phần đầu CV** (tên, tuổi, thông tin liên hệ). Mọi embedding và các mô hình M1–M3 dùng `model_text`, nên điểm không phụ thuộc nhân thân. Có test hồi quy: hai CV chỉ khác phần đầu cho cùng điểm.

## 4. Sáu đặc trưng

Mỗi đặc trưng nằm trong [0, 1]; không có đặc trưng nào dùng tên, giới tính, tuổi hay ảnh.

| Đặc trưng | Cách tính |
|---|---|
| `skill_req` | số kỹ năng bắt buộc ứng viên có ÷ tổng số kỹ năng bắt buộc (không có yêu cầu thì 1) |
| `skill_pref` | tương tự với kỹ năng ưu tiên |
| `semantic` | cosine giữa embedding CV và embedding JD, đưa từ [−1, 1] về [0, 1] bằng (cos + 1) / 2 |
| `exp` | min(1, năm kinh nghiệm của ứng viên ÷ năm yêu cầu) |
| `edu` | 1 nếu đủ học vấn; 0,5 nếu thiếu một bậc; 0 nếu thiếu nhiều hơn |
| `pref` | trung bình các thành phần khớp mong muốn (địa điểm, hình thức, khoảng lương giao nhau); tin Remote tính khớp địa điểm; không có thông tin để so thì 0,5 |

So khớp kỹ năng dùng `has_skill`, port nguyên từ `calculateSkillMatch` của frontend TypeScript (so khớp nguyên tên, bỏ hậu tố " cơ bản", xử lý `A hoặc B`).

## 5. Năm mô hình

| Mô hình | Cách tính | Ghi chú |
|---|---|---|
| **M0** | 60% kỹ năng bắt buộc + 25% kỹ năng ưu tiên + 15% mong muốn (địa điểm, hình thức) | baseline; port của logic frontend cũ. **Khớp 100% bản TypeScript trên 84 ca** (7 hồ sơ × 12 tin) |
| **M1** | TF-IDF (từ đơn và cặp từ liền kề, tách từ tiếng Việt bằng `underthesea` nếu có) rồi cosine CV–JD | IDF được fit trên các tin đang mở (khi khởi động và khi số tin đổi). Fit trên đúng hai văn bản của một cặp cho điểm vô nghĩa |
| **M2** | chỉ dùng độ tương đồng embedding | cho biết embedding một mình làm được đến đâu |
| **M3** | hybrid: 0,40·`skill_req` + 0,15·`skill_pref` + 0,25·`semantic` + 0,10·`exp` + 0,05·`edu` + 0,05·`pref`, rồi nhân 100 | **luật chặn:** nếu thiếu hơn một nửa kỹ năng bắt buộc thì điểm không vượt 50. Trọng số đọc từ `models_store/m3_weights.json` nếu có, mặc định là bộ trên. Là mô hình mặc định |
| **M4** | Logistic Regression học trọng số trên 6 đặc trưng, điểm = xác suất × 100 | huấn luyện bằng GroupKFold theo ứng viên để tránh rò rỉ. **Chưa có `m4.joblib` trên `main`** nên `/ai/match` với `m4` trả **503 `model_not_trained`**; giao diện báo lỗi tại chỗ và vẫn dùng được M0–M3 |

Điểm luôn là số nguyên, làm tròn theo kiểu `Math.round` của JavaScript để khớp bản gốc.

## 6. Giải thích điểm

`explain.py` sinh câu theo mẫu, ví dụ: "Khớp 72/100. Đã có React, Git. Thiếu TypeScript (bắt buộc) và REST API (ưu tiên)." Cùng dữ liệu đó (kỹ năng có và thiếu) cung cấp cho trang Skill Gap: kỹ năng bắt buộc xếp trước, kèm lộ trình học 3 bước. Kỹ năng chưa có lộ trình riêng dùng lộ trình mặc định.

## 7. Tích hợp và hiệu năng

- **API:** `POST /ai/match`, `GET /candidates/me/matches`, `/recommendations`, `/skill-gap`, `GET /jobs/{id}/ranked-candidates`, `POST /ai/extract-skills`, `POST /resumes/upload`. Phân quyền: ứng viên chỉ chấm cho mình; nhà tuyển dụng chỉ xếp hạng ứng viên đã nộp vào tin của công ty mình (403 nếu khác).
- **Embedding tính sẵn khi lưu** (CV, tin và hồ sơ ứng viên chưa có CV, cột `embedding BYTEA`). Nếu để đến lúc chấm mới mã hoá thì mỗi cặp tốn khoảng 400 ms, vượt yêu cầu; tính sẵn thì còn khoảng 60 ms (số đo ở dưới).
- **Đo hiệu năng** trên mã `main` với model embedding thật trong Docker, PostgreSQL 16, qua HTTP, kết nối giữ sẵn: **chấm 1 cặp khoảng 57–60 ms** (yêu cầu < 200 ms); lấy điểm cho toàn bộ **150 tin trong 650 ms** (yêu cầu cho 500 tin < 2 s). Chưa đo trực tiếp với 500 tin qua HTTP trên `main`; test tự động `test_performance_500_jobs_under_two_seconds` đo trên dữ liệu tổng hợp với embedder băm.
- **Kiểm thử tự động:** `cd backend && python -m pytest` cho 167 passed, 1 skipped khi không có PostgreSQL; **178 passed** khi đặt `TEST_DATABASE_URL` tới một PostgreSQL 16 (11 test API cần DB thật). Phủ parser, trích kỹ năng, đặc trưng, M0–M4, phân quyền, luật trạng thái, đối chiếu M0 với TypeScript và công bằng.

## 8. Đánh giá hiệu quả mô hình – chưa có số liệu

Quy trình đã sẵn sàng nhưng **chưa có kết quả**:

- `notebooks/01_parser_eval.ipynb`: P/R/F1 của từng tầng trích kỹ năng trên 50 CV có nhãn, cộng MAE số năm kinh nghiệm.
- `notebooks/02_train_m4.ipynb`: ghép hai file nhãn độc lập, tính kappa trọng số bình phương (mục tiêu ≥ 0,6), huấn luyện M4 bằng GroupKFold theo ứng viên.
- `notebooks/03_ranking_eval.ipynb`: bảng M0–M4 (Precision@5, nDCG@10, MRR, Spearman, ROC-AUC, ms/cặp), ablation M3, 5 cặp sai nhiều nhất, kiểm tra công bằng.

**Điều kiện cần:** 50 CV và `labels_cv_skills.csv`, 300 cặp CV–JD và hai file `labels_pairs_*.csv` (hiện `backend/seed/labels/` chưa có file nhãn và `cv_files/` chưa có CV thật). Khi chạy phải thấy `Embedder: st:...` (model thật), nếu không số liệu chỉ để thử luồng. Nhóm đã chọn để **agent AI gán nhãn**; khi có số liệu, báo cáo phải ghi rõ nguồn nhãn này và các hạn chế: hai lượt gán dùng cùng họ mô hình nên kappa cao chỉ phản ánh độ nhất quán, nhãn dựa trên cùng loại thông tin các mô hình dùng nên điểm có xu hướng lạc quan, và chỉ có 30 ứng viên nên chênh lệch nhỏ giữa các mô hình không có ý nghĩa thống kê.

TODO: sau khi có file kết quả trong `docs/report/tables/`, thêm bảng P/R/F1, bảng so sánh M0–M4, ablation, hệ số M4 và 5 cặp sai nhiều nhất vào mục này.

## 9. Hạn chế

- Phần học máy thật chỉ có ở M4; trích kỹ năng chủ yếu là từ điển, so khớp mờ và embedding, chưa có mô hình nhận dạng thực thể (NER) huấn luyện riêng (hướng phát triển: PhoBERT).
- CV dạng ảnh scan không đọc được (hệ thống báo lỗi, không đoán).
- Danh mục chỉ có 81 kỹ năng và 167 từ đồng nghĩa; kỹ năng ngoài danh mục không được nhận.
- Dữ liệu ứng viên, CV, tin là mô phỏng (seed cố định 42).
