# Đánh giá trạng thái checklist TH3 (chiều 31/10/2026)

Căn cứ: nội dung thực tế trong repo (nhánh `feat/tung-ai-ml`, 167 test xanh) và kế hoạch + 5 prompt. Tiến độ làm ngoài repo của Thái Anh, Ngọc Anh, Hưng, Hoàng Anh **chưa có bằng chứng trên repo** nên ghi "chưa bắt đầu trên repo", không phải "chưa làm".

## 1. Trạng thái từng mục

| Mục | Yêu cầu đề | Đã có (có bằng chứng) | Chưa có | Mức |
|---|---|---|---|---|
| **01** | Phân tích yêu cầu, thiết kế CSDL cho ứng viên, nhà tuyển dụng, tin | Kế hoạch yêu cầu F01–F10 và 15 bảng (docs); CSV mẫu và quy ước cột (`backend/seed`); hợp đồng DB bổ sung (`category`, `responsibilities`, `profile_json`, `learning_steps`) | Bảng yêu cầu hoàn chỉnh, Use Case, ERD, migration/`schema.sql`, seed 150 tin / 300 ứng viên / 1.200 đơn | Mới có đặc tả |
| **02** | Mô hình AI/ML phân tích CV và tính điểm tương thích | CV parser (PDF/DOCX/TXT, 3 tầng kỹ năng, năm KN, học vấn); 6 đặc trưng; M0–M4; giải thích; M0 khớp TypeScript 100% (84 ca); API AI đủ endpoint; công cụ huấn luyện và đánh giá; 3 notebook | Chạy với model embedding thật; nhãn 50 CV và 300 cặp; số liệu P/R/F1, bảng M0–M4; `m4.joblib`; nối `AIRepository` vào DB | Mã xong, chưa có kết quả |
| **03** | Dashboard BI: số ứng viên theo kỹ năng, xu hướng lương, tỷ lệ chuyển đổi | Chỉ có đặc tả (3 view SQL, bảng 8 biểu đồ, hướng dẫn nhúng, phương án Recharts) | `views.sql`, Superset, guest token, RLS, biểu đồ, export, nhận định | Chưa bắt đầu trên repo |
| **04** | Frontend và tích hợp API AI/BI | Prototype 10 màn hình (dữ liệu mẫu); router AI/CV đã viết và test; hợp đồng response chính xác cho Ngọc Anh | Backend lõi (auth, jobs, applications), `src/api`, đăng nhập, đăng tin, Kanban, nhúng dashboard, offline demo, Docker Compose | Mới có API AI |
| **05** | Kiểm thử với dữ liệu mẫu và báo cáo đánh giá mô hình | Notebook đánh giá, metrics, kappa, ablation, phân tích lỗi, công bằng; script chọn 300 cặp; hướng dẫn gán nhãn; test chạy bằng dữ liệu tổng hợp | Dữ liệu seed thật, nhãn, ≥ 25 test case thủ công, pytest API, đo hiệu năng trên DB, báo cáo, video | Công cụ sẵn, chưa có dữ liệu |

## 2. Plan và prompt đã đủ chuẩn đề TH3 chưa?

**Về phạm vi: đủ.** Cả 5 mục checklist đều có người phụ trách, đầu ra và tiêu chí xong. Ba chỉ số BI mà đề nêu đúng tên (ứng viên theo kỹ năng, xu hướng lương, tỷ lệ chuyển đổi) đều có view và biểu đồ bắt buộc. Phần mô tả đề (Matching Score bằng AI, BI cho nhà tuyển dụng, tối ưu quy trình tìm việc) được phủ bởi `/ai/match`, `/candidates/me/recommendations` và dashboard nhúng theo công ty.

**Hai lỗ hổng đã tìm ra và đã vá khi rà soát:**
1. Skill Gap cần lộ trình học nhưng chưa có bảng, dữ liệu hay người phụ trách. Đã thêm `skills.learning_steps`, `skill_learning_steps.csv` (Hưng) và lộ trình mặc định ở API.
2. `backend/seed/cv_files/` từng bị `.gitignore` chặn nên 50 CV không thể chia sẻ cho Hoàng Anh gán nhãn. Đã bỏ khỏi `.gitignore`.

**Rủi ro còn lại (chưa đảm bảo đạt chuẩn nếu không xử lý):**

| # | Rủi ro | Hệ quả | Cách xử lý |
|---|---|---|---|
| 1 | Phần "ML" chỉ nằm ở M4 (xếp hạng); trích kỹ năng CV chủ yếu là từ điển + so khớp mờ + embedding | Người chấm có thể xem phân tích CV là quy tắc, chưa phải ML | Trình bày parser là NLP lai, đo bằng P/R/F1 từng tầng; nhấn mạnh embedding và M4. Nếu còn thời gian, thêm một bộ phân loại học từ nhãn CV |
| 2 | Chưa chạy model embedding thật | Số liệu có thể khác khi chạy trong Docker | Chạy `EMBEDDER=st` trong Docker 3.11 trước khi chạy notebook; chỉ báo cáo số liệu có `Embedder: st:` |
| 3 | M4 huấn luyện trên ~300 cặp, ứng viên sinh từ mẫu nghề | Có thể không hơn M3, kết quả không khái quát | Báo cáo trung thực; giữ M3 mặc định nếu M4 không hơn |
| 4 | Dữ liệu ứng tuyển và lương là mô phỏng | Dashboard chỉ minh hoạ cách tính | Ghi rõ trong báo cáo; chỉ kết luận hiệu quả mô hình từ nhãn tay |
| 5 | Không có giao diện quản trị danh mục kỹ năng (F10 chỉ có API) | Thiếu một use case trên giao diện | Chấp nhận demo qua Swagger; không bắt buộc theo đề |
| 6 | Thái Anh gánh DB, API, seed, Superset, Docker; Ngọc Anh phụ thuộc API | Trễ một khâu làm trễ cả chuỗi | Dùng mock và fixture đã có; cắt phạm vi theo bảng rủi ro |
| 7 | Đề chỉ nhận **video** MP4/… ≤ 101 MB, nộp 1 lần | Báo cáo, slide, repo không nộp trực tiếp được | Kịch bản video theo 01 → 05; link repo trong mô tả; hỏi giảng viên kênh nộp thêm |
| 8 | Chưa có bằng chứng tiến độ các thành viên khác | Không đánh giá được khả năng kịp hạn | Mỗi tối nhắn 3 dòng; kiểm tra các điểm bàn giao trong mục 5.2 của `00_` |

**Kết luận:** nếu cả nhóm làm đúng prompt, các mục 01–05 đáp ứng đề. Trạng thái hiện tại mới hoàn thiện về mặt mã cho mục 02 và công cụ cho mục 05; mục 01, 03, 04 còn nguyên khối lượng chính. Điểm cần giữ sát nhất là các bàn giao: CSV của Hưng (18:00 1/11), `candidates_generated.csv` của Thái Anh (22:00 1/11) và hai file nhãn (22:00 3/11).
