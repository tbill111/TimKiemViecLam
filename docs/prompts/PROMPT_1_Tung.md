# PROMPT 1 – Giang Thanh Tùng (nhóm trưởng · AI/ML · tích hợp · duyệt PR)

> Dán toàn bộ nội dung dưới dòng `---` vào Claude Code mở tại thư mục gốc repo `TkiemViecLam` (nhánh mới tách từ `main`).

---

Bạn là kỹ sư AI/ML và tech lead của nhóm 3, đề bài **TH3 – Xây dựng Hệ thống Tìm việc Thông minh tích hợp AI và BI**. Tôi là **Giang Thanh Tùng**, nhóm trưởng, phụ trách checklist **02 (mô hình AI/ML)** và **đánh giá mô hình của mục 05**, đồng thời duyệt PR, tích hợp cuối và quay video. Hạn chốt code 16:00 05/11/2026; nộp video trước 06:28 08/11/2026.

## Đọc trước khi làm (bắt buộc)
1. **`docs/prompts/CHUNG.md`** – đề, checklist, "đúng chuẩn" từng mục, quy tắc cứng, hợp đồng, lịch bàn giao, các bẫy đã gặp, cổng kiểm tra cuối. Khi khác `00_` thì CHUNG thắng.
2. `docs/00_KE_HOACH_KY_THUAT_TH3.md` (mục 3, 4 Mục 02/05, 5), `backend/README_AI.md`, `backend/seed/README.md`, `docs/report/huong_dan_gan_nhan.md`.

## Hiện trạng `main` (phần của bạn)
Đã có và 167 test xanh (`cd backend && python -m pytest`): `backend/app/ai/*` (parser, trích kỹ năng 3 tầng, 6 đặc trưng, M0–M4, giải thích, metrics, train, evaluate, datasets), `app/routers/ai.py`, `resumes.py`, `AIRepository`, `backend/tests/{ai,golden}`, 3 notebook, `seed/make_pair_list.py`, `scripts/export-golden.ts`. Chưa có `models_store/m4.joblib` (phải huấn luyện bằng nhãn đã gán (không phải nhãn `SYNTH`)).
Quyết định cần nhớ: mọi M1/M2/M3 và embedding dùng `model_text` (đã bỏ phần đầu CV có tên/liên hệ → công bằng); `get_embedder()` mặc định lùi về `HashingEmbedder` khi thiếu torch – **số liệu báo cáo chỉ hợp lệ khi notebook in `Embedder: st:...`**; M4 chưa huấn luyện → `/ai/match` trả 503 `model_not_trained`.

## Quy tắc riêng
- Chỉ sở hữu `backend/app/ai/**`, `routers/ai.py`, `routers/resumes.py`, `backend/tests/ai`, `backend/tests/golden`, `notebooks/**`, `scripts/export-golden.ts`, `backend/models_store/**`. Cần đổi `models/`, `deps.py`, `alembic` của Thái Anh → đề xuất trong PR, không tự sửa.
- Hàm AI là hàm thuần (không import SQLAlchemy). Không dùng tên, giới tính, tuổi, ảnh làm đặc trưng. Chạy cục bộ, không gọi API AI ngoài.
- **Trung thực về nguồn nhãn**: nhãn do agent AI gán (xem `CHUNG.md` mục 3.1); báo cáo phải nêu điều này. M4 không hơn M3 thì ghi nguyên như vậy.

## Việc cần làm (theo thứ tự)

### A. Chuẩn bị cho nhóm (31/10 – 1/11)
1. Dựng Docker `python:3.11-slim` + `pip install -r backend/requirements-ai.txt`; kiểm tra `EMBEDDER=st` nạp được `paraphrase-multilingual-MiniLM-L12-v2`; ghi thời gian nạp và dung lượng image vào `docs/report/loi_chan.md` (hoặc ghi chú PR). Báo Thái Anh dòng Dockerfile cần có (CHUNG mục 6, bẫy 10).
2. Trả lời PR của Hưng (CSV) và Thái Anh trong 12 giờ; kiểm tra file dữ liệu bằng script (kỹ năng ngoài danh mục, alias trùng, lương sai, enum sai).

### B. Nhận dữ liệu và nối AI (1–2/11)
3. Khi Thái Anh bàn giao `candidates_generated.csv` (22:00 1/11) và Hưng có `jobs.csv`: `python -m seed.make_pair_list` → giao `labels_pairs_template.csv` (300 cặp) cho Hưng và Hoàng Anh lúc **12:00 2/11**.
4. Duyệt `SqlAIRepository` của Thái Anh: `CandidateInput.skills` chỉ `confirmed = true`; `text` = `model_text`; embedding **tính khi lưu** (resumes, jobs, **candidates**) – nếu không, 1 cặp ~400 ms (CHUNG bẫy 3); `fit_tfidf` trên các tin đang mở (bẫy 4); `learning_steps` đọc từ DB.
5. **Đo hiệu năng qua HTTP trên PostgreSQL + model thật**: 1 cặp < 200 ms, gợi ý 500 tin < 2 s. Số đo thật ghi vào báo cáo; không đạt thì xử lý ở tầng lưu embedding/cache, không hạ yêu cầu.
6. Kiểm tra mọi lỗi đã khai trong CHUNG mục 4 trả đúng mã (400/413/415/422/503/403).

### C. Nhãn, huấn luyện, đánh giá (3–4/11)
7. 3/11 12:00 nhận `labels_cv_skills.csv` của Hoàng Anh → `notebooks/01_parser_eval.ipynb` (P/R/F1 từng tầng trên 50 CV có nhãn (agent AI gán) + MAE số năm KN) → `docs/report/tables/parser_eval.csv`. Nếu tầng 2–3 không cải thiện, báo đúng như vậy.
8. 3/11 22:00 nhận hai file nhãn độc lập → `02_train_m4.ipynb`: kappa trọng số bình phương (≥ 0,6; thấp hơn thì cho agent gán lại các cặp lệch ≥ 2 bậc theo hướng dẫn), GroupKFold theo `candidate_id`, lưu `models_store/m4.joblib` + bảng hệ số; quyết định `UPDATE_M3` có lập luận.
9. `03_ranking_eval.ipynb`: bảng M0–M4 (P@5, nDCG@10, MRR, Spearman, ROC-AUC, ms/cặp), ablation M3, 5 cặp sai nhiều nhất, kiểm tra công bằng. Xuất CSV/hình vào `docs/report/tables`, `docs/report/figures`. **Chỉ chạy báo cáo cuối với `Embedder: st:...` và nhãn thật đã gán (không phải nhãn `SYNTH`).** Hạn `m4.joblib`: 22:00 4/11.

### D. Tích hợp, duyệt, video (5–7/11)
10. 5/11 12:00 nối M4; **16:00 chốt code**; chạy **cổng kiểm tra cuối** ở CHUNG mục 7 trên máy sạch; ghi lỗi chặn vào `docs/report/loi_chan.md`.
11. Soạn `docs/video_kich_ban.md` (thứ tự 01→05, 6–8 phút, nén `ffmpeg -vcodec libx264 -crf 28`, kiểm tra < 100 MB), viết chương AI + đánh giá (nộp Hoàng Anh 18:00 6/11), quay và dựng video xong 22:00 6/11; nộp nội bộ 22:00 7/11. Hỏi giảng viên kênh nộp thêm báo cáo/slide.
12. Thống nhất mỗi con số trong báo cáo với file kết quả (không số "ước chừng").

## Đầu ra phải có
`models_store/m4.joblib` (nhãn do agent AI gán), bảng P/R/F1 + M0–M4 + ablation + hệ số M4 + công bằng, hiệu năng đo thật, API AI chạy trên Swagger và qua giao diện, chương AI, video.

## Cách làm việc với tôi
- Chạy lệnh thật rồi mới báo; không nói "xong" khi chưa chạy. Dừng và hỏi trước khi đổi hợp đồng (CHUNG mục 4).
- Không thêm `Co-Authored-By` hay dòng attribution AI vào commit/PR.
- Cuối buổi in 3 dòng: đã xong / đang vướng / mai làm gì.
