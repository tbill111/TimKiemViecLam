# Tầng AI (`backend/app/ai`) – hướng dẫn cho nhóm

Người phụ trách: Giang Thanh Tùng. Hợp đồng tổng thể ở `docs/00_KE_HOACH_KY_THUAT_TH3.md` (mục 3, 4).

## Chạy test

```bash
cd backend
python -m pytest -q            # toàn bộ test tầng AI, router và đối chiếu M0 với TypeScript
```

Test dùng `HashingEmbedder` nên không cần tải model. Trong Docker (Python 3.11) cài `requirements-ai.txt` để dùng model thật
`paraphrase-multilingual-MiniLM-L12-v2`; đặt `EMBEDDER=st` để buộc dùng model thật (lỗi nếu thiếu gói), `EMBEDDER=hash` để buộc dùng bản thử.

## Module

| File | Việc |
|---|---|
| `types.py` | `JobInput`, `CandidateInput`, `CvError`, `ModelNotAvailable` |
| `skills.py` | chuẩn hoá và `has_skill` (port từ `src/utils/index.ts`), `SkillIndex` |
| `parser.py` | đọc PDF/DOCX/TXT, tách mục, năm kinh nghiệm, học vấn, `parse_cv`, `suggest_skills` |
| `extract.py` | trích kỹ năng 3 tầng (n-gram → rapidfuzz ≥ 90 → embedding ≥ 0,8) |
| `embedder.py` | embedding 384 chiều; tự lùi về `HashingEmbedder` nếu thiếu `sentence-transformers` |
| `features.py` | 6 đặc trưng `skill_req, skill_pref, semantic, exp, edu, pref` |
| `scorers.py` | M0–M4, `score_pair`, `score_many` |
| `explain.py` | câu giải thích theo mẫu |
| `metrics.py`, `train.py`, `evaluate.py`, `datasets.py` | đánh giá và huấn luyện (dùng trong `notebooks/`) |
| `repository.py` | `AIRepository` – hợp đồng với DB |

## Việc Thái Anh cần làm để nối vào backend

1. Hiện thực `AIRepository` bằng SQLAlchemy (ví dụ `app/services/ai_repo.py`). Mỗi phương thức có docstring mô tả dữ liệu cần trả.
   - `CandidateInput.skills` chỉ lấy kỹ năng **đã xác nhận** (`candidate_skills.confirmed = true`).
   - `CandidateInput.text` và `resumes.embedding` lấy từ `parsed["model_text"]` / `parsed["embedding"]` của `parse_cv` (đã bỏ tên và liên hệ), không dùng `parsed["text"]`.
   - `JobInput.work_type_label` dùng quy tắc ở mục 3.2 của `00_` (`remote` → `Remote`, còn lại theo `job_type`).
   - `JobInput.embedding` và `jobs.embedding`: tính khi lưu tin bằng `app.ai.embedder.embed_text(...)`, lưu `to_bytes(...)`.
2. Trong `main.py`:
   ```python
   from app.ai.repository import get_ai_repo
   from app.routers import ai, resumes
   app.include_router(ai.router, prefix="/api")
   app.include_router(resumes.router, prefix="/api")
   app.dependency_overrides[get_ai_repo] = lambda db=Depends(get_db): SqlAIRepository(db)
   ```
3. `app/deps.py` cần có `get_current_user()` (đối tượng có `.id`, `.role`, `.company_id`) và `require_role(*roles)` trả dependency kiểm tra vai trò rồi trả lại user. Test router trong `tests/ai/conftest.py` tự dựng bản thay thế khi chưa có `app.deps`.
4. Dockerfile: sau `pip install`, tải trước model để chạy offline:
   `RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"` rồi đặt `HF_HUB_OFFLINE=1` khi chạy.
5. Khi nạp danh mục: `SkillIndex.from_rows(skills, aliases)`; sau khi nạp tin, gọi `app.ai.scorers.fit_tfidf([j.text for j in jobs])` một lần cho M1.

## Dữ liệu và nhãn

Định dạng CSV ở `backend/seed/README.md`. Chọn 300 cặp gán nhãn:
`python -m seed.make_pair_list` (chạy trong `backend/`). Hướng dẫn gán nhãn ở `docs/report/huong_dan_gan_nhan.md`.

## Quy trình đánh giá (notebooks)

1. `notebooks/01_parser_eval.ipynb` – cần `backend/seed/cv_files/*` và `labels/labels_cv_skills.csv`.
2. `notebooks/02_train_m4.ipynb` – cần `labels_pairs_hung.csv`, `labels_pairs_hoanganh.csv`; tạo `models_store/m4.joblib`.
3. `notebooks/03_ranking_eval.ipynb` – bảng M0–M4, ablation, phân tích lỗi → `docs/report/tables/`.

## Lưu ý trung thực khi báo cáo

- Số liệu chỉ có ý nghĩa khi `Embedder:` in ra là `st:...` (model thật). Với `hash-384` chỉ để chạy thử luồng.
- Tests dùng dữ liệu tổng hợp để kiểm tra mã; không dùng số liệu đó trong báo cáo.
- Hiệu quả mô hình chỉ kết luận từ 300 cặp gán nhãn tay; dữ liệu ứng tuyển mô phỏng không dùng để kết luận.
