# Nhãn MÔ PHỎNG – không phải nhãn tay

Các file `*_SYNTH*.csv` do `seed/simulate_labels.py` sinh để chạy trọn pipeline (huấn luyện M4, bảng M0–M4, ablation, kappa).
Hai người gán nhãn giả lập đọc cùng độ phù hợp tiềm ẩn (nhóm nghề, độ phủ kỹ năng, kinh nghiệm, học vấn) rồi cộng nhiễu riêng, nên kết quả của các mô hình dựa trên quy tắc bị lạc quan có hệ thống. **Không dùng các bảng số liệu sinh từ đây làm kết luận về hiệu quả mô hình.**

Khi Hoàng Hưng và Hoàng Anh gán nhãn thật, lưu `labels_pairs_hung.csv`, `labels_pairs_hoanganh.csv`, `labels_cv_skills.csv` ở đây rồi chạy lại 3 notebook (không đặt biến `TH3_LABELS_A/B`, `TH3_CV_LABELS`, `TH3_OUT_DIR`) và xoá `models_store/m4.joblib` mô phỏng trước khi huấn luyện lại.
