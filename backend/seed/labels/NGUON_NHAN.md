# Nguồn gốc các file nhãn

Nhóm chọn dùng **agent AI** để gán nhãn (không gán tay). Báo cáo và slide phải ghi đúng điều này.

| File | Nội dung | Cách tạo |
|---|---|---|
| `labels_pairs_hung.csv` | 300 cặp CV–JD, nhãn 0–3 (lượt gán 1) | Một phiên agent AI (Claude Sonnet) độc lập, chỉ nhận bản mô tả cặp (kỹ năng, nghề, kinh nghiệm, học vấn của ứng viên; thông tin tin tuyển dụng) và hướng dẫn `docs/report/huong_dan_gan_nhan.md`. Không được xem điểm hệ thống, kết quả parser hay nhãn của lượt kia. Thứ tự đọc: 1→300. |
| `labels_pairs_hoanganh.csv` | Cùng 300 cặp (lượt gán 2) | Phiên agent AI khác, cùng điều kiện, đọc thứ tự ngược 300→1. |
| `labels_cv_skills.csv` | Kỹ năng thật sự có trong 50 CV + số năm KN | Một phiên agent AI đọc văn bản từng CV (đã trích ra .txt) và danh mục `skills.csv`; không dùng parser. |

Tên file `hung`/`hoanganh` chỉ giữ theo quy ước đặt tên của pipeline; **không phải nhãn do hai thành viên gán**.

## Hạn chế cần nêu khi báo cáo
- Hai lượt gán dùng cùng một họ mô hình nên kappa (0,959) phản ánh độ nhất quán của agent, không phải độ tin cậy giữa hai người; không có cặp nào lệch ≥ 2 bậc.
- Agent gán dựa trên kỹ năng/nghề/kinh nghiệm/học vấn, tức cùng loại thông tin mà M0–M4 dùng, nên điểm số các mô hình có xu hướng cao hơn so với nhãn người. Kết luận về hiệu quả mô hình chỉ có giá trị tham khảo.
- Vài nhãn có thể cứng nhắc hoặc khó giải thích (xem phân tích lỗi ở `docs/report/tables/error_analysis_m3.csv`).
- Nhãn không được chỉnh tay sau khi agent gán.

`seed/simulate_labels.py` là công cụ phục vụ test (sinh nhãn bằng công thức); nó **không** tạo ra các file ở trên.
