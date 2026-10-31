# Khung báo cáo TH3 – SmartCareer v2

Mỗi mục ghi nguồn số liệu/ảnh để người viết lấy đúng, không tự bịa số. Mục chưa có dữ liệu để `TODO` cho đến khi chạy xong.

1. **Giới thiệu**: bài toán, mục tiêu, kế thừa prototype SmartCareer ở bài cá nhân (`README.md`, `docs/00_KE_HOACH_KY_THUAT_TH3.md`).
2. **Phân tích yêu cầu và CSDL (mục 01)**: `docs/report/01_phan_tich_yeu_cau.md`, `docs/usecase/usecase.puml` (+ ảnh), `docs/usecase/dac_ta_use_case.md`, `docs/erd/erd.dbml` (+ ảnh từ dbdiagram.io), `backend/schema.sql`, `backend/seed/README.md` (nguồn và số lượng dữ liệu).
3. **Mô hình AI (mục 02)**: pipeline parser và 6 đặc trưng (`backend/README_AI.md`), công thức M0–M4 (`backend/app/ai/scorers.py`), lý do chọn model. Bảng P/R/F1 từng tầng: **TODO** `docs/report/tables/parser_eval.csv` (chạy `notebooks/01_parser_eval.ipynb` trên nhãn đã gán (agent AI)).
4. **Dashboard BI (mục 03)**: định nghĩa chỉ số và 4 view (`bi/views.sql`), danh sách biểu đồ (`bi/README.md`), ảnh dashboard và 3–4 nhận định (**TODO** `bi/screenshots/`), nêu rõ dữ liệu là mô phỏng.
5. **Kiến trúc, API, giao diện (mục 04)**: sơ đồ 4 dịch vụ (`docker-compose.yml`), danh sách endpoint (Swagger `/docs`, `docs/00_KE_HOACH_KY_THUAT_TH3.md` mục 3.4), ảnh màn hình (`scripts/e2e_smoke.py --shots` tạo sẵn 10 ảnh).
6. **Thực nghiệm và đánh giá (mục 05)**: dữ liệu và cách gán nhãn (`docs/report/huong_dan_gan_nhan.md`, kappa **TODO** `docs/report/tables/kappa.csv`); bảng so sánh M0–M4, ablation, hệ số M4, phân tích 5 cặp sai nhiều nhất (**TODO** `docs/report/tables/model_comparison.csv`, `ablation_m3.csv`, `m4_coefficients.csv`, `error_analysis_m3.csv`); kiểm thử hệ thống (`docs/testcases.md`, 225 test tự động, E2E, hiệu năng); công bằng (`test_fairness_header_change_does_not_change_scores`).
7. **Hạn chế và hướng phát triển**: dữ liệu mô phỏng; CV ảnh scan; từ điển 108 kỹ năng; chưa dùng PhoBERT; học từ phản hồi thật của nhà tuyển dụng; chưa có giao diện quản trị kỹ năng.
