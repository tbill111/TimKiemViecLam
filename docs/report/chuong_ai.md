# Chương AI – Mô hình phân tích CV và điểm tương thích (mục checklist 02)

> Mọi con số trong chương lấy từ file kết quả do notebook sinh ra (`docs/report/tables/`), chạy với model embedding thật (`Embedder: st:paraphrase-multilingual-MiniLM-L12-v2`) trên dữ liệu của chính repo này. **Nhãn đánh giá do agent AI gán, không phải do người** (xem mục 8 và `backend/seed/labels/NGUON_NHAN.md`); mọi kết luận về hiệu quả mô hình mang hạn chế đó.

## 1. Bài toán và đầu ra

Đầu vào: một CV (PDF, DOCX hoặc TXT) hoặc hồ sơ ứng viên, và một tin tuyển dụng (JD). Đầu ra: điểm tương thích số nguyên từ 0 đến 100 (Matching Score), kèm sáu điểm thành phần, danh sách kỹ năng đã có và còn thiếu, và một câu giải thích. Cả bảy mô hình M0–M6 dùng chung một giao diện và trả cùng một cấu trúc `MatchDTO`:

```
{model, model_version, total_score, components{skill_req, skill_pref, semantic, exp, edu, pref},
 matched_required, missing_required, matched_preferred, missing_preferred,
 location_match, work_type_match, explanation}
```

Với M0, ba thành phần `semantic`, `exp`, `edu` là `null` vì M0 không dùng chúng.

## 2. Kiến trúc

Tầng AI nằm ở `backend/app/ai/` và là **hàm thuần**, không import SQLAlchemy. Nó nhận dữ liệu qua `CandidateInput`, `JobInput` và giao diện `AIRepository` (`repository.py`); phía backend, `SqlAIRepository` (`app/services/ai_repo.py`) hiện thực giao diện này bằng PostgreSQL. Cách tách này cho phép kiểm thử tầng AI mà không cần cơ sở dữ liệu.

| Module | Việc |
|---|---|
| `parser.py` | đọc tệp, chuẩn hoá, tách mục, số năm kinh nghiệm, học vấn |
| `skills.py`, `extract.py` | chuẩn hoá kỹ năng, từ đồng nghĩa, trích kỹ năng 3 tầng |
| `embedder.py` | embedding 384 chiều (`paraphrase-multilingual-MiniLM-L12-v2`), có bản `HashingEmbedder` cho kiểm thử |
| `features.py` | sáu đặc trưng |
| `scorers.py` | M0–M6, `score_pair`, `score_many` (dự đoán cả lô cho M4–M6) |
| `explain.py` | câu giải thích |
| `train.py`, `metrics.py`, `evaluate.py` | huấn luyện, đo lường và đánh giá, dùng trong `notebooks/` |

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
6. **Công bằng:** `parse_cv` trả `model_text`, là văn bản đã **bỏ phần đầu CV** (tên, tuổi, thông tin liên hệ). Mọi embedding và các mô hình M1–M3 dùng `model_text`, nên điểm không phụ thuộc nhân thân. Kiểm tra trên hai CV chỉ khác phần đầu (tên, giới tính, tuổi, email): cùng kỹ năng, năm kinh nghiệm, học vấn và **cùng điểm M3 (67)** (`notebooks/03_ranking_eval.ipynb`).

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

## 5. Bảy mô hình

| Mô hình | Cách tính | Học máy? |
|---|---|---|
| **M0** | 60% kỹ năng bắt buộc + 25% kỹ năng ưu tiên + 15% mong muốn (địa điểm, hình thức); port của logic frontend cũ, **khớp 100% bản TypeScript trên 84 ca** | Không (quy tắc) |
| **M1** | TF-IDF (từ đơn và cặp từ liền kề, `underthesea` nếu có) rồi cosine CV–JD; IDF fit trên các tin đang mở | Không (thống kê) |
| **M2** | chỉ dùng độ tương đồng embedding | Mạng nơ-ron huấn luyện sẵn, không tự huấn luyện |
| **M3** | hybrid 0,40·`skill_req` + 0,15·`skill_pref` + 0,25·`semantic` + 0,10·`exp` + 0,05·`edu` + 0,05·`pref`, rồi × 100; **luật chặn:** thiếu hơn một nửa kỹ năng bắt buộc thì điểm không vượt 50. Mô hình mặc định | Không (trọng số đặt tay) |
| **M4** | **Logistic Regression** trên 6 đặc trưng; C chọn bằng GroupKFold lồng (lưới 0,1–10) | **Có** |
| **M5** | **Random Forest** (300 cây, độ sâu ≤ 4, `min_samples_leaf` 5, cân bằng lớp) | **Có** |
| **M6** | **Gradient Boosting** (150 cây nông, độ sâu 2, tốc độ học 0,05, subsample 0,8) | **Có** |

M4–M6 dùng cùng 6 đặc trưng, cùng nhãn nhị phân "phù hợp" (nhãn chốt ≥ 2) và cùng GroupKFold 5 theo ứng viên (một ứng viên không bao giờ vừa ở tập huấn luyện vừa ở tập kiểm tra). Siêu tham số của M5, M6 cố định từ trước (nông, có regularization vì chỉ có 300 cặp) và **không** dò trên dữ liệu kiểm tra; riêng C của M4 chọn trong từng fold huấn luyện nên điểm kiểm tra không bị rò rỉ. Mỗi mô hình học máy được lưu thành `backend/models_store/m4.joblib`, `m5.joblib`, `m6.joblib`; chưa có file thì `/ai/match` trả 503 `model_not_trained`.

Điểm luôn là số nguyên, làm tròn theo kiểu `Math.round` của JavaScript để khớp bản gốc.

## 6. Giải thích điểm

`explain.py` sinh câu theo mẫu, ví dụ: "Khớp 72/100. Đã có React, Git. Thiếu TypeScript (bắt buộc) và REST API (ưu tiên)." Cùng dữ liệu đó cung cấp cho trang Skill Gap: kỹ năng bắt buộc xếp trước, kèm lộ trình học 3 bước; kỹ năng chưa có lộ trình riêng dùng lộ trình mặc định.

## 7. Tích hợp và hiệu năng

- **API:** `POST /ai/match`, `GET /candidates/me/matches`, `/recommendations`, `/skill-gap`, `GET /jobs/{id}/ranked-candidates`, `POST /ai/extract-skills`, `POST /resumes/upload`. Ứng viên chỉ chấm cho mình; nhà tuyển dụng chỉ xếp hạng ứng viên đã nộp vào tin của công ty mình (403 nếu khác).
- **Embedding tính sẵn khi lưu** (CV, tin và hồ sơ chưa có CV; cột `embedding BYTEA`). Nếu để đến lúc chấm mới mã hoá thì mỗi cặp tốn khoảng 400 ms, vượt yêu cầu.
- **Chấm theo lô:** `score_many` dự đoán cả lô tin bằng một lần `predict_proba` cho M4–M6; gọi từng cặp một với Random Forest chậm hơn nhiều (lấy điểm 150 tin mất 4,3 giây trước khi sửa).
- **Hiệu năng đo qua HTTP** trên PostgreSQL 16 và model embedding thật trong Docker (kết nối giữ sẵn, `main` build từ nhánh sửa): trung vị / p95 (ms) – chấm 1 cặp CV–JD bằng M0…M6: 59/62, 62/64, 55/57, 56/58, 55/59, 68/72, 55/56 (gồm lưu `match_results`); `GET /candidates/me/matches` chấm cả 150 tin: 219/227; gợi ý việc làm: 275/317; skill gap: 14/15; xếp hạng ứng viên cho một tin: 32/32; trích kỹ năng từ văn bản: 51/55; phễu BI: 6/8; cấp guest token Superset: 367/404. Tất cả dưới 1 giây; đo 8–15 lần mỗi API trên máy phát triển (Docker Desktop, Windows), không phải số liệu production.
- **Kiểm thử tự động:** `cd backend && python -m pytest` → **208 test đạt** trên PostgreSQL 16 (60 giây), gồm test parser, 6 đặc trưng, M0–M6, notebook smoke, migration trên CSDL trống (kể cả nâng cấp từ 0006 lên 0007 cho phép m5/m6), seed có 50 file CV. Kiểm thử qua HTTP/trình duyệt: `scripts/run_testcases.py` 10/10 ca đạt; `scripts/check_bi_views.py` 4/4 view khớp API; `scripts/e2e_ui.py` online 16/16 và offline 19/19 bước đạt.

## 8. Đánh giá hiệu quả mô hình

### 8.1. Dữ liệu và nhãn
30 ứng viên × 10 tin = **300 cặp** (4 tin cùng nhóm nghề, 3 gần, 3 khác nhóm; seed 42, `python -m seed.make_pair_list --template` tái lập được), thang 0–3 theo `docs/report/huong_dan_gan_nhan.md`; nhãn nhị phân "phù hợp" khi ≥ 2. Kỹ năng của **50 CV** (PDF/DOCX do `seed/gen_cv_files.py` dựng) cũng có nhãn.

**Nhãn do agent AI gán.** Hai phiên agent AI (Claude Sonnet) riêng biệt gán độc lập 300 cặp, mỗi phiên chỉ nhận mô tả cặp và hướng dẫn gán nhãn, không xem điểm hệ thống hay nhãn của phiên kia; một phiên khác đọc văn bản 50 CV để gán kỹ năng. Kết quả: kappa có trọng số bình phương = **0,934** (mục tiêu ≥ 0,6), trùng khít 84% cặp, **0** cặp lệch ≥ 2 bậc. Kappa cao phản ánh việc hai phiên dùng cùng họ mô hình và cùng tiêu chí, nên là độ nhất quán của agent chứ không phải độ tin cậy giữa hai người; chưa có đối chiếu với nhãn của con người.

### 8.2. Module A – trích kỹ năng trên 50 CV (`parser_eval.csv`)
| Tầng | Precision | Recall | F1 |
|---|---|---|---|
| T1 từ điển + alias | 0,995 | 0,952 | 0,973 |
| T1+2 (+ so khớp mờ) | 0,995 | 0,980 | 0,987 |
| T1+2+3 (+ embedding) | 0,989 | 0,989 | 0,989 |

MAE số năm kinh nghiệm = 0,118. Tầng 2 nâng recall (bắt lỗi gõ), tầng 3 nâng thêm một chút recall nhưng giảm precision. CV là dữ liệu tổng hợp theo mẫu nên các số này cao hơn so với CV thật.

### 8.3. So sánh M0–M6 trên 300 cặp (M4–M6 tính trên fold kiểm tra GroupKFold; `model_comparison.csv`)
| Mô hình | Precision@5 | nDCG@10 | MRR | Spearman ρ | ROC-AUC | ms/cặp |
|---|---|---|---|---|---|---|
| M0 quy tắc 60/25/15 | 0,733 | 0,976 | 0,983 | 0,876 | 0,956 | 0,13 |
| M1 TF-IDF | 0,720 | 0,960 | 0,940 | 0,806 | 0,958 | 5,99 |
| M2 embedding | 0,720 | 0,945 | 0,857 | 0,792 | 0,929 | 0,14 |
| M3 hybrid | 0,740 | **0,995** | 1,000 | 0,893 | 0,980 | 0,15 |
| M4 Logistic Regression | 0,740 | 0,994 | 1,000 | **0,895** | 0,981 | — |
| M5 Random Forest | 0,740 | 0,993 | 1,000 | 0,865 | 0,990 | — |
| M6 Gradient Boosting | 0,740 | 0,989 | 1,000 | 0,809 | **0,990** | — |

**Khoảng tin cậy 95% bằng bootstrap theo ứng viên** (500 lần resample cả ứng viên; `ndcg_bootstrap.csv`):

| Mô hình | nDCG@10 | KTC 95% | Chênh lệch so với M3 | KTC của chênh lệch | Khác M3 có ý nghĩa? |
|---|---|---|---|---|---|
| M0 | 0,976 | 0,963 – 0,984 | −0,020 | −0,030 đến −0,011 | **Có** (kém hơn) |
| M1 | 0,960 | 0,941 – 0,976 | −0,035 | −0,053 đến −0,020 | **Có** (kém hơn) |
| M2 | 0,945 | 0,919 – 0,966 | −0,050 | −0,073 đến −0,030 | **Có** (kém hơn) |
| M3 | 0,995 | 0,991 – 0,997 | — | — | — |
| M4 | 0,994 | 0,988 – 0,999 | −0,001 | −0,004 đến +0,002 | Không (khoảng chứa 0) |
| M5 | 0,993 | 0,987 – 0,996 | −0,002 | −0,006 đến +0,001 | Không |
| M6 | 0,989 | 0,983 – 0,993 | −0,006 | −0,012 đến −0,001 | **Có** (kém hơn nhẹ) |

Nhận xét:
1. M3, M4 và M5 đứng đầu và **không phân biệt được với nhau** (khoảng tin cậy của chênh lệch chứa 0); M0, M1, M2 kém hơn M3 một cách có ý nghĩa thống kê. M6 kém M3 nhẹ nhưng có ý nghĩa (−0,006).
2. Mô hình học máy **không vượt** mô hình lai đặt tay: không thể nói học máy tốt hơn. Điểm cộng của học máy là ROC-AUC trên fold kiểm tra cao hơn (M5, M6 ≈ 0,990 so với 0,980 của M3), tức phân biệt cặp "phù hợp" và "không phù hợp" tốt hơn, dù thứ hạng trong từng ứng viên (nDCG) không hơn.
3. Chọn C cho M4 bằng GroupKFold lồng (C = 10) chỉ nâng ROC-AUC từ 0,979 (C = 1) lên 0,981, nằm trong sai số.
4. Chỉ có 30 ứng viên và agent gán nhãn dựa trên đúng loại thông tin các mô hình dùng nên các con số có xu hướng lạc quan; nDCG@10 của mọi mô hình đều rất cao (≥ 0,945) nên khoảng cách giữa chúng nhỏ.

### 8.4. Ablation M3 (bỏ lần lượt một đặc trưng, `ablation_m3.csv`)
| Bỏ đặc trưng | nDCG@10 | Thay đổi |
|---|---|---|
| (không bỏ) | 0,995 | — |
| `skill_req` | 0,972 | −0,023 |
| `exp` | 0,990 | −0,005 |
| `edu` | 0,994 | −0,001 |
| `semantic` | 0,994 | −0,001 |
| `skill_pref` | 0,998 | +0,003 |
| `pref` | 0,996 | +0,001 |

`skill_req` quan trọng nhất; bỏ `skill_pref` hoặc `pref` còn làm nhỉnh lên một chút, nghĩa là hai đặc trưng này không giúp ích trên bộ nhãn này.

### 8.5. Độ quan trọng của đặc trưng (`m4_coefficients.csv`)
| Đặc trưng | M4 hệ số (C = 10) | M5 độ quan trọng | M6 độ quan trọng | Trọng số tay M3 |
|---|---|---|---|---|
| `skill_req` | 10,70 | 0,571 | 0,836 | 0,40 |
| `semantic` | 6,81 | 0,351 | 0,071 | 0,25 |
| `exp` | 2,53 | 0,032 | 0,077 | 0,10 |
| `edu` | 0,30 | 0,006 | 0,000 | 0,05 |
| `pref` | 0,23 | 0,007 | 0,001 | 0,05 |
| `skill_pref` | −3,98 | 0,033 | 0,016 | 0,15 |

Cả ba mô hình học máy cho `skill_req` quan trọng nhất, rồi `semantic`, cùng thứ tự với trọng số tay của M3. Hệ số âm của `skill_pref` ở M4 (−3,98) nhiều khả năng do các đặc trưng tương quan với nhau khi C lớn (chưa kiểm chứng nguyên nhân); không nên diễn giải là "có kỹ năng ưu tiên làm giảm điểm". Hai mô hình cây không cho hệ số âm.

### 8.6. Phân tích lỗi (5 cặp lệch nhiều nhất của M3, `error_analysis_m3.csv`)
Cả năm cặp đều có nhãn 0 nhưng M3 cho 43–50 điểm: ứng viên chỉ trùng một kỹ năng mềm chung (Giao tiếp hoặc Tư duy sáng tạo) với tin thuộc nhóm nghề khác (marketing, thiết kế), còn thiếu 3–4 kỹ năng bắt buộc. Luật chặn ≤ 50 chỉ ngăn điểm vượt 50, không kéo điểm xuống dưới. Hướng cải thiện: thêm đặc trưng "đúng nhóm nghề" hoặc phạt nặng hơn khi thiếu nhiều kỹ năng bắt buộc.

## 9. Hạn chế
- Nhãn do agent AI gán, chưa đối chiếu với con người; chỉ 30 ứng viên; số liệu có xu hướng lạc quan.
- Phần học máy dùng 6 đặc trưng thủ công; trích kỹ năng chủ yếu là từ điển, so khớp mờ và embedding, chưa có mô hình nhận dạng thực thể (NER) huấn luyện riêng (hướng phát triển: PhoBERT).
- CV dạng ảnh scan không đọc được (hệ thống báo lỗi, không đoán).
- Danh mục chỉ có 81 kỹ năng và 167 từ đồng nghĩa; kỹ năng ngoài danh mục không được nhận.
- Dữ liệu ứng viên, CV, tin là mô phỏng (seed cố định 42).
