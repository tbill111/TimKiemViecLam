# Hướng dẫn gán nhãn cặp CV–JD

**Mục tiêu:** cho điểm mức phù hợp giữa một ứng viên và một tin tuyển dụng để dùng huấn luyện M4 và đánh giá M0–M4.
Hai người (Hoàng Hưng, Hoàng Anh) gán **độc lập**; không xem điểm của hệ thống và không trao đổi trong lúc gán.

## Thang nhãn

| Nhãn | Ý nghĩa | Dấu hiệu |
|---|---|---|
| **0** | Không phù hợp | Khác hẳn nhóm nghề, hoặc gần như không có kỹ năng bắt buộc nào |
| **1** | Ít phù hợp | Có vài kỹ năng chung nhưng thiếu phần lớn kỹ năng bắt buộc; hoặc đúng nghề nhưng lệch nặng về cấp bậc/kinh nghiệm |
| **2** | Phù hợp | Có hơn một nửa kỹ năng bắt buộc, đúng hướng nghề, cấp bậc chấp nhận được; học thêm vài kỹ năng là làm được |
| **3** | Rất phù hợp | Có gần đủ kỹ năng bắt buộc, đúng nhóm nghề, kinh nghiệm/học vấn đáp ứng; nên mời phỏng vấn |

Bạn chỉ xét **năng lực và sự phù hợp công việc**. Không dựa vào tên, giới tính, tuổi, trường học để cho điểm.

## Ví dụ

| Ứng viên | Tin | Nhãn | Lý do |
|---|---|---|---|
| Có HTML, CSS, JavaScript, React, Git | Frontend Intern (HTML, CSS, JS, React, Git) | **3** | Đủ kỹ năng bắt buộc, đúng nghề |
| Có HTML, CSS, JavaScript | Frontend Intern (… React, Git) | **2** | Thiếu React, Git nhưng nền tảng tốt |
| Có SQL, Python, Excel | Frontend Intern | **0** | Khác nhóm nghề, không trùng kỹ năng |
| Có SQL, Excel | Data Analyst Intern (SQL, Python, Excel, Thống kê) | **2** | Có 2/4 kỹ năng bắt buộc, đúng nghề |
| Có Git | Data Analyst Intern | **1** | Chỉ trùng một kỹ năng chung |

## Cách làm

1. Nhận `labels_pairs_template.csv` (cột `candidate_id,job_id,label`, cột `label` để trống).
2. Với mỗi dòng đọc hồ sơ ứng viên và tin, điền `label` ∈ {0,1,2,3}. Không bỏ trống dòng nào (tối thiểu 200 cặp nếu thiếu thời gian, báo Tùng).
3. Lưu thành `labels_pairs_<tên>.csv` trong `backend/seed/labels/`, cùng cột và cùng thứ tự dòng.

## Chốt nhãn và độ đồng thuận (do Tùng làm)

- Tính Cohen's kappa có trọng số bình phương; mục tiêu **≥ 0,6**.
- Hai nhãn lệch **≥ 2 bậc**: hai người thảo luận và chốt lại. Lệch **1 bậc**: lấy trung bình làm tròn xuống.
- Nhãn nhị phân "phù hợp" dùng cho huấn luyện: nhãn chốt **≥ 2**.
