# Kịch bản video TH3 (nhánh `fix/main-chuan-checklist`)

Video phải cho thấy 5 mục checklist theo thứ tự 01 → 05, dài khoảng 8 phút. **Nộp:** MP4/MOV/MKV/AVI/WEBM, ≤ 101 MB, **1 lần**, hạn **08/11/2026 06:28** (ân hạn 15 phút). Các số trong kịch bản lấy từ lần chạy thật ngày 06/11/2026 trên đúng nhánh này.

## A. File và địa chỉ

| Mục đích | Đường dẫn |
|---|---|
| Ứng dụng | http://localhost:8080 |
| Swagger | http://localhost:8000/docs |
| Slide | `docs\report\Slide_TH3.pptx` |
| Use Case / ERD | `docs\usecase\usecase.png`, `docs\erd\erd.png` |
| CV mẫu để tải lên | `public\cv-mau.pdf` (hoặc `backend\seed\cv_files\cv_001.pdf`) |
| Bảng so sánh mô hình | `docs\report\tables\model_comparison.csv`, `ndcg_bootstrap.csv`, `kappa.csv` |
| Test case, báo cáo | `docs\testcases.md`, `docs\report\BaoCao_TH3.md` |

**Tài khoản** (mật khẩu chung `Demo@12345`): ứng viên `thanhtung.demo@smartcareer.vn`; nhà tuyển dụng Sao Mai Software `hr1@smartcareer.vn`; nhà tuyển dụng công ty khác `hr5@smartcareer.vn`; quản trị `admin@smartcareer.vn`. Gõ tay email và mật khẩu ở trang `/login`.

## B. Chuẩn bị (trước khi quay 1 giờ)

1. Mở Docker Desktop, chờ biểu tượng xanh.
2. Terminal tại thư mục dự án:
   ```bash
   docker compose up -d --build
   docker compose exec api python -m seed.load_seed --reset
   python scripts/check_bi_views.py
   ```
   `bi-init` tự dựng dashboard Superset (không cần sửa `.env`); xem `docker compose logs bi-init`, dòng cuối phải là `Đã ghi /bi_state/superset.json`. `check_bi_views.py` in `view_checks` toàn `true`.
3. `cd backend && python -m pytest -q` một lần (1–2 phút) → **210 passed** (cần `TEST_DATABASE_URL`, nếu không nhóm test API bị bỏ qua).
4. Mở sẵn các tab theo thứ tự quay: slide, `usecase.png`, `erd.png`, web (đã đăng xuất), Swagger, terminal, `model_comparison.csv`, `testcases.md`, `BaoCao_TH3.md`.
5. Cài đặt quay 1920×1080, phóng trình duyệt 90–100%, tắt thông báo.

## C. Cảnh 1 – Mở đầu (0:00–0:30)

Slide 1 rồi slide 2. **Lời thoại:** "Đây là bài TH3 của nhóm 3: xây dựng hệ thống tìm việc thông minh tích hợp AI và BI, SmartCareer v2. Sinh viên mới ra trường khó biết mình hợp vị trí nào và còn thiếu kỹ năng gì; nhà tuyển dụng cần số liệu để tối ưu tuyển dụng. Hệ thống có bốn dịch vụ Docker: PostgreSQL, API FastAPI chứa tầng AI, Superset cho BI và giao diện React. Toàn bộ dữ liệu là mô phỏng."

## D. Cảnh 2 – Mục 01: Phân tích yêu cầu và CSDL (0:30–1:30)

| Bước | Thao tác | Kết quả |
|---|---|---|
| 1 | Mở `usecase.png`, chỉ 4 tác nhân → chức năng F01–F10 → 3 quan hệ `<<include>>` | Ảnh rõ |
| 2 | Mở `erd.png`, chỉ ba nhóm (ứng viên, nhà tuyển dụng, tin) rồi nhóm tuyển dụng và danh mục; đếm 15 bảng | — |
| 3 | Swagger, cuộn qua các nhóm auth, jobs, ai, applications, bi, admin | — |

**Lời thoại:** "Mục 1: bốn tác nhân, mười chức năng F01 đến F10, và cơ sở dữ liệu 15 bảng cho ứng viên, nhà tuyển dụng và tin tuyển dụng, quản lý bằng migration Alembic. Một lệnh `docker compose up` trên máy trống dựng được toàn bộ; lỗi migration trên CSDL trống của bản trước đã được sửa và có test."

## E. Cảnh 3 – Mục 02 + 04: AI và giao diện ứng viên (1:30–3:30)

| Bước | Thao tác | Kết quả |
|---|---|---|
| 1 | `/login`, đăng nhập `thanhtung.demo@smartcareer.vn` | Vào Tổng quan |
| 2 | **Tìm việc làm**, chờ điểm khớp tải xong | Hơn 100 tin, thẻ nào cũng có % |
| 3 | Bấm một tin | Kỹ năng có/thiếu; Esc để đóng |
| 4 | **Hồ sơ của tôi** → khung nhập kỹ năng từ CV: chọn `cv-mau.pdf` **khi chưa tích đồng ý** | Báo lỗi cần đồng ý |
| 5 | Tích đồng ý, chọn lại file | Danh sách kỹ năng đề xuất; kỹ năng gợi ý từ embedding có nhãn, không tự chọn |
| 6 | Thêm các kỹ năng vào hồ sơ | Hồ sơ cập nhật |
| 7 | **Phân tích CV–JD**: chọn một tin, ô Mô hình chọn lần lượt M0, M3, M4, M5, M6 | Điểm đổi theo mô hình; 6 thành phần, kỹ năng có/thiếu, câu giải thích |
| 8 | **Skill Gap Analysis**, mở một kỹ năng | Lộ trình học; kỹ năng bắt buộc đứng trước |

**Lời thoại:** "Mục 2 và 4. Mỗi tin có điểm khớp 0–100 do máy chủ tính, kèm giải thích. Tải CV phải tích đồng ý xử lý dữ liệu. Parser ba tầng: từ điển và từ đồng nghĩa, so khớp mờ, rồi embedding chỉ để gợi ý; trên 50 CV đạt precision, recall và F1 khoảng 0,99. Có bảy mô hình: M0 quy tắc, M1 TF-IDF, M2 embedding, M3 kết hợp, và ba mô hình học máy M4 Logistic Regression, M5 Random Forest, M6 Gradient Boosting. Đổi tên, giới tính hay tuổi ở phần đầu CV không làm đổi điểm."

**Lỗi thường gặp:** bấm tin khi điểm chưa tải xong (đã sửa, hiện hộp "Đang tính điểm khớp", đợi vài giây); M4–M6 báo "chưa được huấn luyện" nếu thiếu `backend\models_store\m4.joblib m5.joblib m6.joblib` (có sẵn trong repo).

## F. Cảnh 4 – Mục 04: Ứng tuyển và nhà tuyển dụng (3:30–4:30)

| Bước | Thao tác | Kết quả |
|---|---|---|
| 1 | Ứng viên: **Tìm việc làm**, gõ `Sao Mai` | Chỉ tin của Sao Mai Software |
| 2 | Mở một tin → **Ứng tuyển** → xác nhận | "Ứng tuyển thành công"; ghi nhớ tên tin |
| 3 | **Việc đã lưu & Ứng tuyển** | Đơn "Đã ứng tuyển"; ứng viên không đổi được trạng thái |
| 4 | Đăng xuất, đăng nhập `hr1@smartcareer.vn` → **Ứng viên xếp hạng** → chọn đúng tin vừa nộp | Danh sách ứng viên có điểm và lý do |
| 5 | **Kanban tuyển dụng**: chuyển thẻ sang "Đang xem xét" | Thẻ đổi cột |
| 6 | (Swagger, đã Authorize bằng token `hr1`) `PATCH /api/applications/{id}/status` từ `applied` sang `interview` | 409 `invalid_transition` |
| 7 | **Đăng tin mới**, mô tả `Cần thành thạo React và Docker, có hiểu biết về SQL.` → **Gợi ý kỹ năng từ mô tả** (không bấm Đăng tin) | Gợi ý React, Docker, SQL |

**Lời thoại:** "Ứng viên nộp đơn, đơn lưu kèm điểm khớp lúc nộp. Nhà tuyển dụng thấy ứng viên xếp hạng theo điểm, kéo qua các bước, và hệ thống chặn nhảy cóc bằng lỗi 409; mọi lần đổi đều ghi lịch sử. Nhà tuyển dụng công ty khác không sửa được đơn của công ty này."

## G. Cảnh 5 – Mục 03: Dashboard BI (4:30–5:30)

| Bước | Thao tác | Kết quả |
|---|---|---|
| 1 | Đăng nhập `hr1`, vào **Dashboard nhà tuyển dụng**, chờ 5–8 giây | Dashboard Superset nhúng: 8 biểu đồ |
| 2 | Chỉ thẻ "Hồ sơ đã nộp" (50) và "Tỷ lệ được tuyển", biểu đồ 2 (top 15 kỹ năng theo số ứng viên), 3 (cung–cầu), 4 và 5 (lương theo tháng/cấp bậc và theo địa điểm), 6 (phễu), 7 (số tin theo nhóm nghề) | — |
| 3 | Bấm mũi tên mở thanh bộ lọc bên trái, chọn một **Cấp bậc** | Biểu đồ lương đổi theo |
| 4 | Cuộn xuống phần dự phòng Recharts (cùng số liệu) | — |
| 5 | Đăng xuất, đăng nhập `hr5` | Hồ sơ đã nộp = 39 (khác `hr1` = 50): lọc theo công ty bằng Row Level Security |
| 6 | Terminal: `python scripts/check_bi_views.py` | `view_checks` bốn view đều `true` |

**Lời thoại:** "Mục 3. Dashboard Superset nhúng ngay trong trang, nối với bốn view SQL, trả ba chỉ số của đề: số ứng viên theo kỹ năng, xu hướng lương và tỷ lệ chuyển đổi tuyển dụng, cộng lương theo địa điểm và số tin theo nhóm nghề, với bốn bộ lọc chung. Phễu và hồ sơ đã nộp chỉ gồm công ty của người đăng nhập nhờ guest token mang điều kiện company_id; dữ liệu kỹ năng và lương là thị trường chung. Dữ liệu ứng tuyển là mô phỏng nên phễu chỉ minh hoạ cách tính."

## H. Cảnh 6 – Quản trị kỹ năng (5:30–6:10)

| Bước | Thao tác | Kết quả |
|---|---|---|
| 1 | Đăng nhập `admin@smartcareer.vn` → **Quản lý kỹ năng** | Bảng kỹ năng, nhóm, lộ trình học |
| 2 | Tab **Alias**: Alias `reakt`, Tên kỹ năng chuẩn `React` → **Thêm alias** | Alias xuất hiện ở "Alias hiện có" |
| 3 | Đăng nhập `hr1` → **Đăng tin mới**, mô tả `thành thạo reakt` → **Gợi ý kỹ năng từ mô tả** | Gợi ý ra React |
| 4 | Quay lại admin, **Xoá** alias `reakt` | Dọn dẹp |

**Lời thoại:** "Chức năng F10: quản trị viên sửa danh mục kỹ năng và từ đồng nghĩa; thêm `reakt` thì bộ gợi ý nhận ra React ngay, vì danh mục là nền của parser và các mô hình."

## I. Cảnh 7 – Mục 05: Kiểm thử và đánh giá (6:10–7:30)

| Bước | Thao tác | Kết quả |
|---|---|---|
| 1 | Terminal `cd backend && python -m pytest -q` (cắt đoạn chờ khi dựng) | **210 passed** |
| 2 | Mở `docs\testcases.md` | 33 ca, tất cả có kết quả thật |
| 3 | Mở `model_comparison.csv`, chỉ cột `ndcg@10`, `roc_auc` | M3 0,995; M4 0,994; M5 0,992; M6 0,989; M0 0,976; M1 0,960; M2 0,945 |
| 4 | Mở `ndcg_bootstrap.csv` | M3, M4, M5 không khác nhau có ý nghĩa; M0, M1, M2 kém hơn M3 |
| 5 | Mở `kappa.csv` và `BaoCao_TH3.md` mục 7 | kappa 0,934; nhãn do agent AI gán |

**Lời thoại:** "Mục 5. Hơn hai trăm bài kiểm thử tự động cộng 33 test case, gồm cả kiểm tra qua HTTP và trình duyệt. Đánh giá trên 300 cặp CV–JD và 50 CV có nhãn. Nhãn do **agent AI gán**, không phải người, hai lượt độc lập với kappa 0,934; chỉ có 30 ứng viên nên số liệu có xu hướng lạc quan. Kết quả: mô hình kết hợp M3 và các mô hình học máy M4, M5 ngang nhau, cả ba hơn rõ ba mô hình đơn giản; học máy không vượt mô hình kết hợp đặt tay, nhưng có ROC-AUC cao hơn."

## J. Cảnh 8 – Kết (7:30–8:00)

Slide cuối. **Lời thoại:** "Nhóm đã làm đủ năm mục: thiết kế cơ sở dữ liệu, mô hình AI có giải thích, dashboard BI nhúng, giao diện ba vai trò và kiểm thử đánh giá. Hạn chế: dữ liệu mô phỏng, nhãn do agent AI gán, quy mô nhỏ. Hướng phát triển: nhãn của người, NER, phản hồi thật từ nhà tuyển dụng. Mã nguồn: https://github.com/tbill111/TimKiemViecLam."

## K. Xử lý sự cố khi quay

| Sự cố | Cách xử lý |
|---|---|
| Docker chưa chạy | Mở Docker Desktop, chờ xanh, `docker compose up -d` |
| Dashboard Superset trống | Xem `docker compose logs bi-init`; chạy lại `docker compose up -d bi-init`; hoặc dùng biểu đồ dự phòng Recharts bên dưới và nói rõ |
| Cổng 8088/8080 bị chiếm | Đổi `SUPERSET_PORT`, `WEB_PORT` trong `.env`; đặt `BI_EMBED_DOMAINS=http://localhost:<WEB_PORT>` rồi `docker compose up -d` |
| Đơn ứng tuyển báo đã nộp | `docker compose exec api python -m seed.load_seed --reset` hoặc chọn tin khác |
| Không có Docker | `VITE_OFFLINE_DEMO=true npm run dev` (email bắt đầu `hr` → nhà tuyển dụng, `admin` → quản trị); nói rõ đây là chế độ demo |

## L. Sau khi quay

1. Ghép cảnh, kiểm tra âm thanh.
2. Nén: `ffmpeg -i demo.mp4 -vcodec libx264 -crf 28 -b:a 96k demo_small.mp4`, phải ≤ 100 MB (vượt thì tăng `-crf` lên 30–32 hoặc hạ 1280×720).
3. Xem lại cả video: đủ 5 mục theo thứ tự 01 → 05, không lộ thông tin cá nhân.
4. **Nộp đúng 1 lần** trước 06:28 ngày 08/11/2026.

## M. Không được nói trong video

- Không nói nhãn do người gán; phải nói do agent AI gán.
- Không nói dữ liệu là thật hay lấy từ TopCV/LinkedIn; dữ liệu là mô phỏng.
- Không nói "học máy tốt hơn" hay "mô hình tốt hơn rõ rệt" giữa M3, M4, M5.
- Không đọc số nào không có trong `docs\report\tables\` hoặc lệnh vừa chạy trên màn hình.
