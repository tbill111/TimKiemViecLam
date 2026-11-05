# Kịch bản video TH3 – bản hướng dẫn thao tác chi tiết

Thư mục dự án: `D:\a.Kì 1 năm 4\Hệ thống kinh doanh\TkiemViecLam` (gọi tắt là `<repo>`). Kịch bản này đã được chạy thử từng bước trên stack Docker thật (xem `docs/video_kich_ban.md` để có bản tóm tắt).

**Đề:** TH3 – Xây dựng Hệ thống Tìm việc Thông minh tích hợp AI và BI. Video phải cho thấy 5 mục checklist theo thứ tự 01 → 05.
**Nộp:** MP4/MOV/MKV/AVI/WEBM, ≤ 101 MB, **nộp 1 lần**, hạn **08/11/2026 06:28** (ân hạn 15 phút).

---

## A. Danh sách đường dẫn và file cần dùng

| Mục đích | Đường dẫn |
|---|---|
| Ứng dụng (web) | http://localhost:8080 |
| Swagger (API) | http://localhost:8000/docs |
| Superset (chỉ để kiểm tra, không cần mở khi quay) | http://localhost:8091 (cổng đặt bởi `SUPERSET_PORT` trong `<repo>\.env`) |
| Slide | `<repo>\docs\report\Slide_TH3.pptx` |
| Sơ đồ Use Case | `<repo>\docs\usecase\usecase.png` (nguồn `usecase.puml`, đặc tả `dac_ta_use_case.md`) |
| ERD | `<repo>\docs\erd\erd.png` (nguồn `erd.dbml`, `erd.puml`) |
| CV mẫu để tải lên | `<repo>\public\cv-mau.pdf` |
| Bảng so sánh M0–M6 | `<repo>\docs\report\tables\model_comparison.csv`, `ndcg_bootstrap.csv` |
| Kappa, ablation, phân tích lỗi | `<repo>\docs\report\tables\kappa.csv`, `ablation_m3.csv`, `error_analysis_m3.csv` |
| Test case | `<repo>\docs\testcases.md` (48 ca) |
| Báo cáo | `<repo>\docs\report\BaoCao_TH3.md` (mục 6 đánh giá, mục 7 hạn chế) |
| Ảnh dự phòng dashboard | `<repo>\bi\screenshots\dashboard_superset_embedded.png`, `dashboard_recharts_fallback.png` |
| Kiểm tra BI | `python scripts\check_bi_views.py` |
| Kiểm thử tự động | `cd backend` rồi `python -m pytest -q` |

**Tài khoản** (mật khẩu chung `Demo@12345`). Trang đăng nhập có sẵn 3 nút điền nhanh **Ứng viên / Nhà tuyển dụng / Quản trị** (điền `tung.demo@…`, `hr01@…`, `admin@…`).

| Vai trò | Email |
|---|---|
| Ứng viên | `tung.demo@smartcareer.vn` |
| Nhà tuyển dụng công ty Sao Mai Software | `hr01@smartcareer.vn` |
| Nhà tuyển dụng công ty khác (so sánh) | `hr05@smartcareer.vn` |
| Quản trị | `admin@smartcareer.vn` |

---

## B. Chuẩn bị (xong trước khi quay 1 giờ)

1. Mở **Docker Desktop**, chờ biểu tượng cá voi chuyển xanh (1–2 phút nếu máy vừa khởi động).
2. Terminal tại `<repo>`:
   ```bash
   docker compose up -d --build
   docker compose exec api python -m seed.load_seed --reset
   python scripts/check_bi_views.py
   ```
   **Kiểm tra:** dòng cuối phải là `TẤT CẢ ĐẠT`; `load_seed` in `skills: 108, candidates: 301, jobs: 150, applications: 1255`.
3. Mở http://localhost:8080 → nếu đang đăng nhập thì **Đăng xuất**.
4. **Lấy token cho Swagger (để thử nhảy cóc ở cảnh 5):** vào http://localhost:8000/docs → `POST /api/auth/login` → *Try it out* → body `{"email":"hr01@smartcareer.vn","password":"Demo@12345"}` → *Execute* → copy `access_token` → bấm **Authorize** (góc trên) → dán token → *Authorize* → *Close*.
5. Chạy thử `cd backend && python -m pytest -q` một lần (khoảng 1–2 phút, phải ra **247 passed**).
6. Mở sẵn các tab theo đúng thứ tự quay: slide, `usecase.png`, `erd.png`, web, Swagger, terminal tại `backend`, `model_comparison.csv`, `testcases.md`, `BaoCao_TH3.md`.
7. Cài đặt quay: 1920×1080, trình duyệt phóng 90–100%, tắt thông báo, dùng micro rời, ẩn thanh bookmark.

---

## C. Cảnh 1 – Mở đầu (0:00–0:30)

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Mở slide 1 (tên đề, nhóm 3) | Hiện tiêu đề TH3 |
| 2 | Sang slide 2 (bài toán, 4 dịch vụ) | Hiện sơ đồ kiến trúc |

**Lời thoại:**
> "Xin chào, đây là bài thực hành TH3 của nhóm 3: Xây dựng hệ thống tìm việc thông minh tích hợp AI và BI, tên SmartCareer v2. Bài toán: sinh viên mới ra trường khó biết mình hợp vị trí nào và còn thiếu kỹ năng gì, còn nhà tuyển dụng phải sàng lọc rất nhiều hồ sơ. Hệ thống dùng AI để tính điểm khớp giữa CV và mô tả công việc, kèm giải thích, và dùng dashboard BI để phân tích thị trường tuyển dụng. Hệ thống chạy bằng một lệnh docker compose gồm bốn dịch vụ: PostgreSQL, backend FastAPI có tầng AI, Apache Superset cho BI, và giao diện React. Video đi theo năm mục của checklist."

---

## D. Cảnh 2 – Mục 01: Phân tích yêu cầu và thiết kế CSDL (0:30–1:30)

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Mở `docs\usecase\usecase.png`. Dùng con trỏ chỉ lần lượt: 4 tác nhân (Ứng viên, Nhà tuyển dụng, Quản trị viên, Dịch vụ AI) → các chức năng F01–F10 → 3 mũi tên nét đứt `<<include>>` | Ảnh rõ nét, không bị cắt |
| 2 | Mở `docs\erd\erd.png`. Chỉ 3 khung màu: **Ứng viên**, **Nhà tuyển dụng**, **Tin tuyển dụng**; rồi khung **Tuyển dụng** và **Danh mục**. Đếm to 15 bảng | Thấy `users`, `candidates`, `jobs`, `applications`… |
| 3 | Mở Swagger http://localhost:8000/docs, cuộn qua danh sách endpoint 3–4 giây | Thấy các nhóm auth, jobs, ai, applications, bi, admin |

**Lời thoại:**
> "Mục 1: phân tích yêu cầu và thiết kế cơ sở dữ liệu. Hệ thống có bốn tác nhân và mười chức năng F01 đến F10: tài khoản, hồ sơ, tải CV, đăng tin, điểm khớp, gợi ý, ứng tuyển, Skill Gap, dashboard và quản lý danh mục kỹ năng. Quan hệ include chính: tải CV gọi trích kỹ năng; xem việc gợi ý gọi tính điểm khớp; đổi trạng thái gọi ghi lịch sử. Cơ sở dữ liệu có mười lăm bảng, chia theo ba đối tượng của đề: ứng viên, nhà tuyển dụng và tin tuyển dụng, cộng nhóm tuyển dụng và danh mục. Đơn ứng tuyển không nộp trùng, có sáu trạng thái; mỗi lần đổi trạng thái ghi một dòng lịch sử, và phễu BI tính từ lịch sử đó. Dữ liệu mẫu hoàn toàn hư cấu, sinh bằng script seed cố định: một trăm linh tám kỹ năng, ba mươi công ty, một trăm năm mươi tin rải đều mười hai tháng, ba trăm linh một ứng viên và khoảng một nghìn hai trăm đơn. Nhóm không lấy dữ liệu từ TopCV hay LinkedIn vì điều khoản không cho phép."

---

## E. Cảnh 3 – Mục 02 + 04: AI và giao diện ứng viên (1:30–3:30)

| Bước | Thao tác chi tiết | Kết quả mong đợi |
|---|---|---|
| 1 | Mở http://localhost:8080/login → bấm nút **Ứng viên** (điền sẵn email, mật khẩu) → **Đăng nhập** | Vào trang **Tổng quan**. Dừng 3 giây |
| 2 | Menu trái → **Tìm việc làm**. **Chờ vài giây** cho điểm khớp tải xong (thẻ nào cũng có số %) | Danh sách 150 tin có điểm. Cuộn chậm 2–3 giây |
| 3 | Bấm tiêu đề một tin → cửa sổ chi tiết | Thấy kỹ năng có / thiếu. Bấm **Esc** để đóng |
| 4 | Menu trái → **Hồ sơ của tôi**. Cuộn tới khung **"Nhập kỹ năng từ CV"** | Có nút **"Chọn tệp CV"** và ô đồng ý |
| 5 | **Chưa tích** ô đồng ý, chọn `public\cv-mau.pdf` (có thể làm bước này để minh hoạ lỗi) | Báo: "Bạn cần tích vào ô đồng ý để hệ thống xử lý dữ liệu CV." |
| 6 | Tích ô **"Tôi đồng ý để hệ thống lưu và phân tích CV…"**, chọn lại `cv-mau.pdf` | Hiện danh sách kỹ năng đề xuất ("Phát hiện N kỹ năng"). Kỹ năng gợi ý từ embedding có nhãn "gợi ý", không tự chọn |
| 7 | Bỏ chọn một kỹ năng, bấm **"Thêm N kỹ năng vào hồ sơ"** | Kỹ năng được thêm vào hồ sơ |
| 8 | Menu → **Phân tích CV–JD**. Chọn một tin ở cột trái. Ô **"Mô hình"**: chọn lần lượt **M0 – Quy tắc 60/25/15**, **M3 – Hybrid**, **M4 – Logistic Regression**, **M5 – Random Forest**, **M6 – Gradient Boosting** | Mỗi lần đổi, điểm và 6 thành phần cập nhật; có câu giải thích; M4 chạy được (phiên bản `m4-ai-labels`) |
| 9 | Chỉ 6 thành phần (kỹ năng bắt buộc, ưu tiên, ngữ nghĩa, kinh nghiệm, học vấn, mong muốn) và câu "Khớp N/100. Đã có… Thiếu…" | — |
| 10 | Menu → **Skill Gap Analysis**. Bấm mũi tên ⌄ cạnh một kỹ năng | Hiện lộ trình học 3 bước; kỹ năng "Ưu tiên Cao" (bắt buộc) đứng trước |

**Lời thoại:**
> "Mục 2 và 4: mô hình AI và giao diện. Mỗi tin ở trang Tìm việc có điểm khớp từ 0 đến 100, tính bằng mô hình AI chứ không phải số cố định. Khi tải CV, ứng viên phải tích đồng ý xử lý dữ liệu. Hệ thống trích kỹ năng theo ba tầng: tra từ điển và từ đồng nghĩa, so khớp mờ để bắt lỗi gõ, và embedding để gợi ý kỹ năng gần nghĩa. Kỹ năng từ embedding chỉ là gợi ý, ứng viên tự xác nhận. Phần đầu CV, gồm tên và thông tin liên hệ, bị loại khỏi văn bản dùng để chấm, nên điểm không phụ thuộc nhân thân. Trang Phân tích CV–JD cho đổi giữa bảy mô hình, thuộc bốn hướng: M0 là quy tắc sáu mươi, hai lăm, mười lăm của bài trước; M1 dùng TF-IDF; M2 dùng embedding huấn luyện sẵn; M3 là mô hình lai sáu đặc trưng với trọng số đặt tay và luật chặn khi thiếu hơn một nửa kỹ năng bắt buộc; và ba mô hình học máy do nhóm tự huấn luyện trên cùng sáu đặc trưng: M4 hồi quy logistic, M5 rừng ngẫu nhiên, M6 gradient boosting. Mỗi điểm có sáu thành phần và một câu giải thích: đã có gì, còn thiếu gì. Trang Skill Gap liệt kê kỹ năng còn thiếu, bắt buộc xếp trước, kèm lộ trình học ba bước. Về tốc độ, chấm một cặp khoảng sáu mươi mili giây, lấy điểm cho cả một trăm năm mươi tin mất khoảng bốn mươi mili giây, đo qua HTTP với model embedding thật."

**Lỗi thường gặp ở cảnh này:**
- Bấm vào tin quá sớm khi điểm khớp chưa tải xong → đợi vài giây.
- Tải CV mà chưa tích đồng ý → báo lỗi (đây cũng là phần minh hoạ, không phải lỗi hệ thống).
- M4 báo "chưa được huấn luyện" → máy chưa có `backend\models_store\m4.joblib`; nói "M4 cần huấn luyện bằng nhãn, các mô hình khác vẫn dùng được" rồi chuyển sang M3.

---

## F. Cảnh 4 – Mục 04: Ứng tuyển và nhà tuyển dụng (3:30–4:30)

| Bước | Thao tác chi tiết | Kết quả mong đợi |
|---|---|---|
| 1 | Vẫn là ứng viên: **Tìm việc làm** → gõ **`Sao Mai`** vào ô "Tên công việc, công ty hoặc kỹ năng…" | Danh sách chỉ còn tin của Sao Mai Software |
| 2 | Bấm tiêu đề **một tin của Sao Mai Software** → nút **Ứng tuyển** → **Xác nhận ứng tuyển** | Hiện "Ứng tuyển thành công". Ghi nhớ **tên tin** |
| 3 | Menu → **Việc đã lưu & Ứng tuyển** → tab đơn đã nộp / theo dõi | Thấy đơn với trạng thái "Đã ứng tuyển"; **không có ô chọn đổi trạng thái** (ứng viên chỉ xem) |
| 4 | **Đăng xuất** (cuối menu trái). Ở trang đăng nhập bấm nút **Nhà tuyển dụng** → **Đăng nhập** | Vào **Dashboard BI** của "HR Sao Mai Software" |
| 5 | Menu trái → **Ứng viên xếp hạng**. Ở ô chọn tin, **chọn đúng tin vừa ứng tuyển** (ô này chỉ liệt kê tin của công ty `hr01`, nên tin đã ứng tuyển phải thuộc Sao Mai Software) | Hiện bảng 6 cột (**Đã ứng tuyển, Đang xem xét, Phỏng vấn, Đề nghị, Đã tuyển, Từ chối**); ứng viên "Giang Thanh Tùng" nằm ở cột **Đã ứng tuyển**, kèm điểm % và lý do khớp / kỹ năng thiếu |
| 6 | Trên thẻ của ứng viên bấm **"Chuyển › Đang xem xét"** | Thẻ chuyển sang cột **Đang xem xét** (đã chạy thử: cột Đã ứng tuyển 5→4, Đang xem xét 1→2) |
| 7 | **Nhảy cóc** (cho thấy luật trạng thái): mở tab Swagger (đã Authorize ở mục B.4) → `PATCH /api/applications/{application_id}/status` → *Try it out* → `application_id` = id đơn (xem trong `GET /api/applications/me` hoặc cột Network) → body `{"status":"offer"}` → *Execute* | Trả **409** với `{"detail":{"detail":"invalid_transition","from":"…","to":"offer"}}` |
| 8 | Menu → **Đăng tin mới** → ô mô tả dán: `Cần thành thạo React và Docker, có hiểu biết về SQL.` → bấm **"Gợi ý kỹ năng từ mô tả"** (đừng bấm Đăng tin) | Hiện thông báo "Đã thêm N kỹ năng vào nhóm bắt buộc: React, Docker, SQL"; có thể bấm mũi tên chuyển một kỹ năng sang **Ưu tiên** |

**Lời thoại:**
> "Ứng viên bấm ứng tuyển, đơn được lưu kèm điểm khớp tại thời điểm nộp; ứng viên chỉ xem được trạng thái, không tự đổi. Sang vai trò nhà tuyển dụng của công ty Sao Mai. Trang Ứng viên xếp hạng sắp xếp theo điểm khớp, kèm lý do khớp và kỹ năng thiếu, và là bảng Kanban sáu cột; nhà tuyển dụng chỉ chuyển sang bước kế tiếp hoặc từ chối. Nếu cố nhảy cóc bước, backend trả lỗi bốn trăm lẻ chín. Mỗi lần chuyển được ghi vào lịch sử trạng thái, và nhà tuyển dụng công ty khác không đổi được đơn này. Khi đăng tin, nút Gợi ý kỹ năng đọc mô tả và đề xuất kỹ năng; nhà tuyển dụng chọn kỹ năng nào bắt buộc, kỹ năng nào ưu tiên."

**Lỗi thường gặp ở cảnh này:**
- `hr01` **không thấy ứng viên** → tin đã ứng tuyển không thuộc Sao Mai Software (phải chọn đúng công ty ở bước 1). Cũng sinh lỗi `403 not_your_job` khi thử PATCH.
- "Ứng tuyển" báo đã ứng tuyển → chạy lại seed (mục B.2) hoặc chọn tin khác.
- Swagger báo 401 → chưa Authorize hoặc token hết hạn (đăng nhập lại ở mục B.4).

---

## G. Cảnh 5 – Mục 03: Dashboard BI (4:30–5:30)

| Bước | Thao tác chi tiết | Kết quả mong đợi |
|---|---|---|
| 1 | Đăng nhập `hr01` (nút **Nhà tuyển dụng**) → **Dashboard BI** (http://localhost:8080/employer/dashboard). **Chờ 5–8 giây** | Hiện 4 thẻ trên cùng (301 ứng viên, 150 tin, hồ sơ đã nộp, tỷ lệ tuyển) và khung Superset nhúng bên dưới |
| 2 | Giải thích: 4 thẻ trên là **toàn thị trường**; biểu đồ Superset bên dưới **đã lọc theo công ty** (thẻ "1. Hồ sơ đã nộp" khoảng 20) | — |
| 3 | Chỉ lần lượt: **biểu đồ 2** "Top 15 kỹ năng theo số ứng viên" và **biểu đồ 3** "Cung so với cầu theo kỹ năng" → **biểu đồ 4** "Lương trung bình theo tháng và cấp bậc" → **biểu đồ 6** "Phễu tuyển dụng" | 3 chỉ số của đề đều hiện. **Bỏ qua biểu đồ 8** (hay hiện 0% với công ty nhỏ) |
| 4 | **Đăng xuất** → đăng nhập `hr05@smartcareer.vn` (gõ tay email, mật khẩu `Demo@12345`) → Dashboard BI | Số "Hồ sơ đã nộp" và phễu **khác** hr01 → minh chứng lọc theo công ty |
| 5 | Terminal tại `<repo>`: `python scripts/check_bi_views.py` | Các dòng `OK` (phễu view = API, lương, kỹ năng…), `bi_reader KHÔNG đọc được bảng users`, dòng cuối **`TẤT CẢ ĐẠT`** |
| 6 | **Dự phòng nếu Superset không lên:** mở `bi\screenshots\dashboard_superset_embedded.png` và nói rõ "đây là ảnh chụp" | — |

**Lời thoại:**
> "Mục 3: dashboard BI. Đây là dashboard Superset nhúng ngay trong trang nhà tuyển dụng, nối với bốn view SQL. Bốn thẻ phía trên là số toàn thị trường; các biểu đồ Superset bên dưới đã lọc theo công ty của nhà tuyển dụng. Ba chỉ số của đề: số ứng viên theo kỹ năng, so với số tin đang cần, cho thấy kỹ năng nào khan hiếm; xu hướng lương theo tháng và cấp bậc; và tỷ lệ chuyển đổi tuyển dụng qua các bước từ nộp hồ sơ đến được nhận. Phễu đếm số hồ sơ từng đạt mỗi bước theo lịch sử trạng thái, nên một hồ sơ đã được nhận vẫn được tính ở bước phỏng vấn. Khi đổi sang tài khoản công ty khác, phễu thay đổi, nhờ Row Level Security trong token nhúng. Em chạy script đối chiếu: số liệu trên view SQL khớp với API ở mọi chỉ số, và tài khoản BI chỉ đọc được view, không đọc được bảng người dùng. Xin lưu ý: dữ liệu ứng tuyển và lương là mô phỏng, nên biểu đồ chỉ minh hoạ cách tính, không phản ánh thị trường thật."

---

## H. Cảnh 6 – Mục 04: Quản trị kỹ năng (5:30–6:10)

| Bước | Thao tác chi tiết | Kết quả mong đợi |
|---|---|---|
| 1 | **Đăng xuất** → bấm nút **Quản trị** → **Đăng nhập** | Vào Dashboard BI với tài khoản "Quản trị SmartCareer" |
| 2 | Menu trái → **Quản lý kỹ năng** | Trang "Quản lý danh mục kỹ năng": danh sách kỹ năng bên trái |
| 3 | Ô **"Tìm trong 108 kỹ năng"** gõ `React` → bấm vào **React** trong danh sách | Bên phải hiện chi tiết React và mục **"Từ đồng nghĩa (N)"** |
| 4 | Ô **"Từ đồng nghĩa mới"** gõ `reakt` → bấm **Thêm** | Thông báo thêm thành công; `reakt` xuất hiện trong danh sách từ đồng nghĩa |
| 5 | **Đăng xuất** → đăng nhập `hr01` → **Đăng tin mới** → mô tả: `thành thạo reakt` → **Gợi ý kỹ năng từ mô tả** | Gợi ý ra **React** (nhận ra `reakt`) |
| 6 | (Tuỳ chọn, để dọn) quay lại admin, bấm dấu × cạnh `reakt` | Xoá alias |

**Lời thoại:**
> "Chức năng F10: quản trị viên quản lý danh mục kỹ năng. Em thêm từ đồng nghĩa 'reakt' cho kỹ năng React. Quay lại form đăng tin, bộ gợi ý nhận ra 'reakt' là React ngay lập tức, vì danh mục này là nền của bộ đọc CV, điểm khớp và biểu đồ BI."

---

## I. Cảnh 7 – Mục 05: Kiểm thử và đánh giá (6:10–7:30)

| Bước | Thao tác chi tiết | Kết quả mong đợi |
|---|---|---|
| 1 | Terminal tại `<repo>\backend`: `python -m pytest -q` (chờ 1–2 phút; cắt đoạn chờ khi dựng video) | `235 passed` |
| 2 | Mở `docs\testcases.md`, cuộn bảng 48 ca; chỉ cột "Kết quả thực tế" | 48 ca, gần hết "Đạt" |
| 3 | Mở `docs\report\tables\model_comparison.csv` (hoặc bảng 6.4 trong `BaoCao_TH3.md`). Chỉ hàng M0–M4, cột `ndcg@10` và `roc_auc` | M3 ≈ 0,988 và M5 ≈ 0,989 (nDCG@10); M4 ≈ 0,971, M6 ≈ 0,983; 7 hàng M0–M6 |
| 4 | Mở `docs\report\tables\kappa.csv` (hoặc mục 6.1 báo cáo) | kappa ≈ 0,959; dòng ghi "nhãn do agent AI gán" |
| 5 | Mở `BaoCao_TH3.md` mục 7 (Hạn chế) | Danh sách hạn chế |

**Lời thoại:**
> "Mục 5: kiểm thử và đánh giá. Hệ thống có hai trăm bốn mươi bảy kiểm thử tự động: parser CV, đặc trưng, bảy mô hình, phân quyền, luật trạng thái, phễu BI, seed và migration; trong đó M0 bản Python khớp một trăm phần trăm bản TypeScript của bài trước. Ngoài ra có bốn mươi tám test case theo mười chức năng và kiểm thử trình duyệt tự động trên stack Docker thật, mười bốn bước đều đạt. Để đánh giá mô hình gợi ý, nhóm chọn ba mươi ứng viên với mười tin mỗi người, tổng ba trăm cặp, gán nhãn mức phù hợp từ không đến ba. Xin nói rõ: nhãn do **agent AI** gán, hai lượt độc lập, không phải do người gán. Hệ số kappa giữa hai lượt là 0,959, nhưng vì cùng một họ mô hình nên con số này chỉ cho thấy agent gán nhất quán, chưa phải độ tin cậy như hai người. Kết quả: M3 và M5 rừng ngẫu nhiên đứng đầu, nDCG@10 khoảng 0,988 và 0,989; M0, M1, M2 kém hơn M3 một cách có ý nghĩa thống kê theo khoảng tin cậy bootstrap; còn ba mô hình học máy M4, M5, M6 không phân biệt được với M3, tức là không thể nói học máy tốt hơn hay kém hơn mô hình lai đặt tay. Do chỉ có ba mươi ứng viên và nhãn dựa trên đúng loại thông tin mà các mô hình dùng, các con số có xu hướng lạc quan. Hạn chế còn lại: dữ liệu và đơn ứng tuyển là mô phỏng; trích kỹ năng chủ yếu dựa trên từ điển, so khớp mờ và embedding chứ chưa có mô hình nhận dạng thực thể riêng; CV dạng ảnh scan chưa đọc được."

---

## J. Cảnh 8 – Kết (7:30–8:00)

Mở slide cuối "Hạn chế và hướng phát triển" (hiện link repo, tên nhóm).

**Lời thoại:**
> "Tóm lại, nhóm đã xây hệ thống đủ năm mục của checklist: thiết kế cơ sở dữ liệu, mô hình AI chấm điểm có giải thích, dashboard BI nhúng, giao diện cho ba vai trò, và kiểm thử cùng đánh giá. Hướng phát triển: học từ phản hồi thật của nhà tuyển dụng, đối chiếu nhãn với con người, bổ sung nhận dạng thực thể cho CV, và thêm bộ lọc nâng cao cho dashboard. Cảm ơn thầy cô đã xem."

---

## K. Xử lý sự cố khi quay

| Sự cố | Cách xử lý |
|---|---|
| Docker chưa chạy (`failed to connect to the docker API`) | Mở Docker Desktop, chờ xanh, `docker compose up -d` |
| Superset không lên / dashboard trống | Chiếu `bi\screenshots\dashboard_superset_embedded.png`, nói rõ là ảnh chụp |
| Cổng 8088 bị chiếm | Đặt `SUPERSET_PORT` trong `.env` (máy này dùng 8091), `docker compose up -d` lại |
| Đơn ứng tuyển báo đã nộp | `docker compose exec api python -m seed.load_seed --reset` hoặc chọn tin khác |
| `hr01` không thấy ứng viên | Tin đã ứng tuyển không thuộc Sao Mai Software; chọn lại |
| Bấm tin mà không thấy điểm | Đợi trang tải xong điểm (vài giây) rồi mới bấm |
| Không có Docker | `VITE_OFFLINE_DEMO=true npm run dev` (email bắt đầu `hr…` → nhà tuyển dụng, `admin…` → quản trị); nói rõ đây là chế độ demo |

## L. Sau khi quay

1. Ghép các cảnh, kiểm tra âm thanh nghe rõ.
2. Nén: `ffmpeg -i demo.mp4 -vcodec libx264 -crf 28 -b:a 96k demo_small.mp4`. Phải ≤ 100 MB; vượt thì tăng `-crf` lên 30–32 hoặc hạ 1280×720.
3. Xem lại toàn video: đủ 5 mục theo thứ tự 01 → 05, không lộ thông tin cá nhân.
4. Đặt link repo và tên nhóm ở cảnh cuối; hỏi giảng viên có kênh nộp thêm báo cáo hay slide không.
5. **Nộp đúng 1 lần** trước 06:28 ngày 08/11/2026.

## M. Không được nói trong video

- Không nói nhãn do người gán; phải nói do agent AI gán.
- Không nói dữ liệu là thật hay lấy từ TopCV/LinkedIn; dữ liệu là mô phỏng.
- Không nói "mô hình tốt hơn rõ rệt" khi chênh lệch giữa M0–M4 nhỏ và chỉ có 30 ứng viên.
- Không đọc số nào không có trong `docs\report\tables\` hoặc lệnh vừa chạy trên màn hình.
