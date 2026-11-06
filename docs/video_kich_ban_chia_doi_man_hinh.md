# Kịch bản video TH3 – bố cục chia đôi màn hình, không dùng slide (nhánh `fix/main-chuan-checklist`)

Các số trong kịch bản lấy từ lần chạy thật ngày 06/11/2026 trên đúng nhánh này (xem `docs/video_kich_ban.md` cho bản tóm tắt).

**Đề:** TH3 – Xây dựng Hệ thống Tìm việc Thông minh tích hợp AI và BI. Video phải cho thấy 5 mục checklist theo thứ tự 01 → 05, dài khoảng 8 phút.
**Nộp:** MP4/MOV/MKV/AVI/WEBM, ≤ 101 MB, **nộp 1 lần**, hạn **08/11/2026 06:28** (ân hạn 15 phút).

---

## 0. Bố cục chia đôi màn hình (không show slide)

- **Nửa trái (960×1080):** bảng checklist 5 mục của đề. Mở `docs\video\checklist_panel.html` bằng trình duyệt, **bấm phím 1–5** để tô sáng mục đang demo (0 = bỏ tô); mục đã qua tự mờ đi. Nếu dựng hậu kỳ thì dùng 6 ảnh sẵn `docs\video\checklist_00.png` … `checklist_05.png` (cùng nội dung, 960×1080).
- **Nửa phải (960×1080):** phần demo (web, Swagger, ảnh Use Case/ERD, CSV, md và terminal). Dùng Windows **Win+←** cho cửa sổ checklist, **Win+→** cho cửa sổ demo; mở thêm tab ở cửa sổ phải, không mở thêm cửa sổ.
- Quay toàn màn 1920×1080. Khi chuyển mục, bấm phím số bên trái **trước**, rồi mới thao tác bên phải.
- Không dùng `Slide_TH3.pptx`. Mở đầu và kết thúc đều nói với bảng checklist ở bên trái (phím 0).

| Cảnh | Phím bên trái | Bên phải |
|---|---|---|
| 1 Mở đầu | 0 | Trang `/login` |
| 2 Mục 01 | 1 | `usecase.png`, `erd.png`, Swagger |
| 3 Mục 02 + 04 | 2, rồi 4 | Giao diện ứng viên (AI) |
| 4 Mục 04 | 4 | Ứng tuyển, xếp hạng, Kanban, Swagger |
| 5 Mục 03 | 3 | Dashboard BI, terminal |
| 6 Mục 04 | 4 | Quản trị kỹ năng |
| 7 Mục 05 | 5 | Terminal pytest, csv, md |
| 8 Kết | 0 | `BaoCao_TH3.md` mục 7 hoặc `/login` |

## A. Danh sách đường dẫn và file cần dùng

Gọi thư mục dự án (nhánh `fix/main-chuan-checklist`) là `<repo>`: clone bằng `git clone -b fix/main-chuan-checklist https://github.com/tbill111/TimKiemViecLam.git`, rồi tạo `.env` từ `.env.example`.

| Mục đích | Đường dẫn |
|---|---|
| Ứng dụng (web) | http://localhost:8080 |
| Swagger (API) | http://localhost:8000/docs |
| Superset (chỉ để kiểm tra, không cần mở khi quay) | http://localhost:8088 (cổng đặt bởi `SUPERSET_PORT` trong `.env`) |
| Bảng checklist nửa trái | `<repo>\docs\video\checklist_panel.html` (phím 0–5) và ảnh `checklist_00..05.png` |
| Sơ đồ Use Case | `<repo>\docs\usecase\usecase.png` (đặc tả `dac_ta_use_case.md`) |
| ERD | `<repo>\docs\erd\erd.png` (giải thích `giai_thich_erd.md`) |
| CV mẫu để tải lên | `<repo>\public\cv-mau.pdf` (hoặc `<repo>\backend\seed\cv_files\cv_001.pdf`) |
| Bảng so sánh M0–M6 | `<repo>\docs\report\tables\model_comparison.csv`, `ndcg_bootstrap.csv` |
| Kappa, ablation, phân tích lỗi | `<repo>\docs\report\tables\kappa.csv`, `ablation_m3.csv`, `error_analysis_m3.csv` |
| Test case | `<repo>\docs\testcases.md` (33 ca) |
| Báo cáo | `<repo>\docs\report\BaoCao_TH3.md` (mục 6 đánh giá, mục 7 hạn chế) |
| Ảnh dự phòng dashboard | `<repo>\docs\report\figures\ui_11_dashboard_bi.png`, `ui_13_dashboard_bo_loc.png` |
| Kiểm tra BI | `python scripts\check_bi_views.py` |
| Kiểm thử tự động | `cd backend` rồi `python -m pytest -q` |

**Tài khoản** (mật khẩu chung `Demo@12345`; trang `/login` có 3 nút điền nhanh **Ứng viên / Nhà tuyển dụng / Quản trị** (điền `thanhtung.demo@`, `hr1@`, `admin@` và mật khẩu); `hr5` phải gõ tay):

| Vai trò | Email |
|---|---|
| Ứng viên | `thanhtung.demo@smartcareer.vn` |
| Nhà tuyển dụng công ty Sao Mai Software | `hr1@smartcareer.vn` |
| Nhà tuyển dụng công ty khác (để so sánh) | `hr5@smartcareer.vn` |
| Quản trị | `admin@smartcareer.vn` |

---

## B. Chuẩn bị (xong trước khi quay 1 giờ)

1. Mở **Docker Desktop**, chờ biểu tượng cá voi chuyển xanh (1–2 phút nếu máy vừa khởi động lại).
2. Terminal tại `<repo>`:
   ```bash
   docker compose up -d --build
   docker compose exec api python -m seed.load_seed --reset
   docker compose logs bi-init
   python scripts/check_bi_views.py
   ```
   **Kiểm tra:** `load_seed` in `skills=81, aliases=167, candidates=300, new_applications=1200`; `docker compose logs bi-init` có dòng cuối `Đã ghi /bi_state/superset.json` (dịch vụ `bi-init` tự dựng dashboard Superset, **không cần sửa `.env`**); `check_bi_views.py` in `view_checks` với bốn view đều `true`.
3. Mở http://localhost:8080; nếu đang đăng nhập thì **Đăng xuất**.
4. **Token cho Swagger (để thử nhảy cóc ở cảnh 4):** vào http://localhost:8000/docs → `POST /api/auth/login` → *Try it out* → body `{"email":"hr1@smartcareer.vn","password":"Demo@12345"}` → *Execute* → copy `access_token` → nút **Authorize** → dán → **Authorize** → **Close**. Làm tương tự với `thanhtung.demo@smartcareer.vn` để biết token ứng viên (dùng lấy id đơn ở cảnh 4, bước 7).
5. Chạy thử `cd backend && python -m pytest -q` một lần (khoảng 1 phút, cần `TEST_DATABASE_URL` trỏ tới PostgreSQL riêng; phải ra **210 passed**).
6. Mở sẵn các tab bên phải theo thứ tự quay: `/login`, `usecase.png`, `erd.png`, web, Swagger, terminal tại `backend`, `model_comparison.csv`, `testcases.md`, `BaoCao_TH3.md`.
7. Cài đặt quay: 1920×1080, trình duyệt phóng 90–100%, tắt thông báo, dùng micro rời, ẩn thanh bookmark.

---

## C. Cảnh 1 – Mở đầu (0:00–0:30)

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 1 | Bên trái bấm phím **0**; bên phải mở http://localhost:8080/login | Đề bài ở trái, trang đăng nhập ở phải |
| 2 | Trỏ chuột lần lượt qua 5 mục bên trái khi nhắc từng mục | — |

**Lời thoại:**
> "Xin chào, đây là bài thực hành TH3 của nhóm 3: Xây dựng hệ thống tìm việc thông minh tích hợp AI và BI, tên SmartCareer v2. Bài toán: sinh viên mới ra trường khó biết mình hợp vị trí nào và còn thiếu kỹ năng gì, còn nhà tuyển dụng phải sàng lọc rất nhiều hồ sơ. Hệ thống dùng AI để tính điểm khớp giữa CV và mô tả công việc, kèm giải thích, và dùng dashboard BI để phân tích thị trường tuyển dụng. Hệ thống chạy bằng một lệnh docker compose gồm bốn dịch vụ: PostgreSQL, backend FastAPI có tầng AI, Apache Superset cho BI, và giao diện React. Video đi theo năm mục của checklist."

---

## D. Cảnh 2 – Mục 01: Phân tích yêu cầu và thiết kế CSDL (0:30–1:30)

| Bước | Thao tác | Kết quả mong đợi |
|---|---|---|
| 0 | Bên trái bấm phím **1** | Mục 01 sáng lên |
| 1 | Mở `docs\usecase\usecase.png`. Chỉ lần lượt: 4 tác nhân (Ứng viên, Nhà tuyển dụng, Quản trị viên, Dịch vụ AI) → các chức năng F01–F10 → 3 mũi tên nét đứt `<<include>>` | Ảnh rõ nét |
| 2 | Mở `docs\erd\erd.png`. Chỉ 3 khung **Ứng viên**, **Nhà tuyển dụng**, **Tin tuyển dụng**; rồi khung **Tuyển dụng** và **Danh mục**. Đếm to 15 bảng | Thấy `users`, `candidates`, `jobs`, `applications`… |
| 3 | Mở Swagger http://localhost:8000/docs, cuộn qua danh sách endpoint 3–4 giây | Thấy các nhóm auth, jobs, ai, applications, bi, admin |

**Lời thoại:**
> "Mục 1: phân tích yêu cầu và thiết kế cơ sở dữ liệu. Hệ thống có bốn tác nhân và mười chức năng F01 đến F10: tài khoản, hồ sơ, tải CV, đăng tin, điểm khớp, gợi ý, ứng tuyển, Skill Gap, dashboard và quản lý danh mục kỹ năng. Quan hệ include chính: tải CV gọi trích kỹ năng; xem việc gợi ý gọi tính điểm khớp; đổi trạng thái gọi ghi lịch sử. Cơ sở dữ liệu có mười lăm bảng, chia theo ba đối tượng của đề: ứng viên, nhà tuyển dụng và tin tuyển dụng, cộng nhóm tuyển dụng và danh mục. Đơn ứng tuyển không nộp trùng, có sáu trạng thái; mỗi lần đổi trạng thái ghi một dòng lịch sử, và phễu BI tính từ lịch sử đó. Cơ sở dữ liệu được quản lý bằng migration Alembic và chạy được từ một cơ sở dữ liệu trống bằng một lệnh docker compose up; lỗi migration trên cơ sở dữ liệu trống của bản trước đã được sửa và có kiểm thử riêng. Dữ liệu mẫu hoàn toàn hư cấu, sinh bằng script seed cố định: tám mươi mốt kỹ năng, ba mươi công ty, một trăm năm mươi tin, ba trăm ứng viên và một nghìn hai trăm đơn ứng tuyển. Nhóm không lấy dữ liệu từ TopCV hay LinkedIn vì điều khoản không cho phép."

---

## E. Cảnh 3 – Mục 02 + 04: AI và giao diện ứng viên (1:30–3:30)

| Bước | Thao tác chi tiết | Kết quả mong đợi |
|---|---|---|
| 0 | Bên trái bấm phím **2** (khi sang bước 7 bấm **4**) | Mục 02 sáng lên |
| 1 | Mở http://localhost:8080/login → bấm nút **Ứng viên** (điền sẵn email và mật khẩu) → **Đăng nhập** | Vào trang **Tổng quan**. Dừng 3 giây |
| 2 | Menu trái → **Tìm việc làm**. **Chờ vài giây** cho điểm khớp tải xong | Hơn 100 tin, thẻ nào cũng có số %. Cuộn chậm 2–3 giây |
| 3 | Bấm tiêu đề một tin → cửa sổ chi tiết | Thấy kỹ năng có / thiếu. Bấm **Esc** để đóng |
| 4 | Menu → **Hồ sơ của tôi**, cuộn tới khung nhập kỹ năng từ CV | Có nút chọn tệp CV và ô đồng ý |
| 5 | **Chưa tích** ô đồng ý, chọn `public\cv-mau.pdf` (cố ý để minh hoạ lỗi) | Báo "Bạn cần đồng ý cho phép xử lý CV trước khi tải lên." |
| 6 | Tích ô "Tôi đồng ý cho hệ thống xử lý CV để trích xuất kỹ năng.", chọn lại `cv-mau.pdf` | "Đã xử lý cv-mau.pdf. Phát hiện 9 kỹ năng." và danh sách kỹ năng đề xuất; kỹ năng gợi ý từ embedding có nhãn "gợi ý", không tự chọn |
| 7 | Bỏ chọn một kỹ năng, bấm nút **"Thêm N kỹ năng vào hồ sơ"** | Kỹ năng vào hồ sơ |
| 8 | Menu → **Phân tích CV–JD**, chọn một tin ở cột trái. Ô **Mô hình**: chọn lần lượt **M0**, **M3**, **M4**, **M5**, **M6** | Điểm và các thành phần cập nhật theo từng mô hình; không báo lỗi |
| 9 | Chỉ các thành phần điểm (kỹ năng bắt buộc, ưu tiên, ngữ nghĩa, kinh nghiệm, học vấn, mong muốn) và danh sách kỹ năng có/thiếu | — |
| 10 | Menu → **Skill Gap Analysis**. Bấm mũi tên cạnh một kỹ năng | Hiện lộ trình học; kỹ năng bắt buộc đứng trước |

**Lời thoại:**
> "Mục 2 và 4: mô hình AI và giao diện. Mỗi tin ở trang Tìm việc có điểm khớp từ 0 đến 100, tính bằng mô hình AI ở máy chủ chứ không phải số cố định. Khi tải CV, ứng viên phải tích đồng ý xử lý dữ liệu. Hệ thống trích kỹ năng theo ba tầng: tra từ điển và từ đồng nghĩa, so khớp mờ để bắt lỗi gõ, và embedding để gợi ý kỹ năng gần nghĩa. Kỹ năng từ embedding chỉ là gợi ý, ứng viên tự xác nhận. Trên năm mươi CV mẫu, bộ đọc đạt precision, recall và F1 khoảng không phẩy chín tám chín. Phần đầu CV, gồm tên và thông tin liên hệ, bị loại khỏi văn bản dùng để chấm, nên điểm không phụ thuộc nhân thân. Trang Phân tích CV–JD cho đổi giữa bảy mô hình: M0 là quy tắc sáu mươi, hai lăm, mười lăm của bài trước; M1 dùng TF-IDF; M2 dùng embedding; M3 là mô hình lai sáu đặc trưng với luật chặn khi thiếu hơn một nửa kỹ năng bắt buộc; và ba mô hình học máy: M4 hồi quy logistic, M5 rừng ngẫu nhiên, M6 gradient boosting, huấn luyện bằng nhãn. Mỗi điểm có các thành phần và một câu giải thích: đã có gì, còn thiếu gì. Trang Skill Gap liệt kê kỹ năng còn thiếu, bắt buộc xếp trước, kèm lộ trình học. Về tốc độ, đo qua HTTP với model embedding thật: chấm một cặp khoảng sáu mươi mili giây, lấy điểm cho cả một trăm năm mươi tin khoảng hai trăm hai mươi mili giây."

**Lỗi thường gặp ở cảnh này:**
- Bấm vào tin quá sớm khi điểm khớp chưa tải xong → hiện hộp "Đang tính điểm khớp…", đợi vài giây rồi bấm lại.
- Tải CV mà chưa tích đồng ý → báo lỗi (đây cũng là phần minh hoạ, không phải lỗi hệ thống).
- M4–M6 báo "chưa được huấn luyện" → máy thiếu `backend\models_store\m4.joblib`, `m5.joblib`, `m6.joblib` (có sẵn trong repo); nói "các mô hình khác vẫn dùng được" rồi chuyển sang M3.

---

## F. Cảnh 4 – Mục 04: Ứng tuyển và nhà tuyển dụng (3:30–4:30)

| Bước | Thao tác chi tiết | Kết quả mong đợi |
|---|---|---|
| 1 | Vẫn là ứng viên: **Tìm việc làm** → gõ **`Sao Mai`** vào ô tìm kiếm | Danh sách chỉ còn tin của Sao Mai Software |
| 2 | Bấm tiêu đề **một tin của Sao Mai Software** → nút **Ứng tuyển** → xác nhận | Hiện "Ứng tuyển thành công". Ghi nhớ **tên tin** |
| 3 | Menu → **Việc đã lưu & Ứng tuyển** | Đơn trạng thái "Đã ứng tuyển"; **không có ô đổi trạng thái** (ứng viên chỉ xem) |
| 4 | **Đăng xuất** (cuối menu trái). Đăng nhập `hr1@smartcareer.vn` / `Demo@12345` | Vào trang nhà tuyển dụng "Sao Mai Software" |
| 5 | Menu → **Ứng viên xếp hạng**. Chọn **đúng tin vừa ứng tuyển** (ô chọn chỉ liệt kê tin của công ty `hr1`) | Danh sách ứng viên đã nộp, sắp theo điểm, kèm lý do khớp và kỹ năng thiếu |
| 6 | Menu → **Kanban tuyển dụng**. Chọn tin đó, bấm nút **"→ Đang xem xét"** trên thẻ của ứng viên (thẻ cũng có nút **Từ chối**) | Thẻ sang cột kế tiếp |
| 7 | **Nhảy cóc** (cho thấy luật trạng thái): Swagger → **Authorize** bằng token ứng viên → `GET /api/applications/me` lấy `id` một đơn còn ở `applied` (ví dụ đơn vừa nộp nếu chưa chuyển; nếu đã chuyển ở bước 6 thì dùng đơn khác) → Authorize lại bằng token `hr1` → `PATCH /api/applications/{id}/status`, body `{"status":"interview"}` | **409** `{"detail":{"detail":"invalid_transition","from":"applied","to":"interview"}}` |
| 8 | Menu → **Đăng tin mới** → ô mô tả dán: `Cần thành thạo React và Docker, có hiểu biết về SQL.` → **Gợi ý kỹ năng từ mô tả** (đừng bấm Đăng tin) | Hiện các kỹ năng gợi ý (React, Docker, SQL) để chọn bắt buộc hay ưu tiên |

**Lời thoại:**
> "Ứng viên bấm ứng tuyển, đơn được lưu kèm điểm khớp tại thời điểm nộp; ứng viên chỉ xem được trạng thái, không tự đổi. Sang vai trò nhà tuyển dụng của công ty Sao Mai. Trang Ứng viên xếp hạng sắp xếp theo điểm khớp, kèm lý do khớp và kỹ năng còn thiếu. Trang Kanban hiển thị sáu cột từ đã ứng tuyển đến đã tuyển hoặc từ chối; nhà tuyển dụng chỉ chuyển sang bước kế tiếp hoặc từ chối. Nếu cố nhảy cóc bước, backend trả lỗi bốn trăm lẻ chín. Mỗi lần chuyển được ghi vào lịch sử trạng thái, và nhà tuyển dụng công ty khác không đổi được đơn này, backend trả lỗi bốn trăm lẻ ba. Khi đăng tin, nút Gợi ý kỹ năng đọc mô tả và đề xuất kỹ năng; nhà tuyển dụng chọn kỹ năng nào bắt buộc, kỹ năng nào ưu tiên."

**Lỗi thường gặp ở cảnh này:**
- `hr1` **không thấy ứng viên** → tin đã ứng tuyển không thuộc Sao Mai Software (phải chọn đúng công ty ở bước 1). Cũng sinh lỗi 403 khi thử PATCH.
- "Ứng tuyển" báo đã ứng tuyển → chạy lại seed (mục B.2) hoặc chọn tin khác.
- Swagger báo 401 → chưa Authorize hoặc token hết hạn (đăng nhập lại ở mục B.4).

---

## G. Cảnh 5 – Mục 03: Dashboard BI (4:30–5:30)

| Bước | Thao tác chi tiết | Kết quả mong đợi |
|---|---|---|
| 0 | Bên trái bấm phím **3** | Mục 03 sáng lên |
| 1 | Đăng nhập `hr1` → **Dashboard nhà tuyển dụng** (http://localhost:8080/employer/dashboard). **Chờ 5–8 giây** | Khung Superset nhúng hiện 8 biểu đồ; phía dưới là biểu đồ dự phòng Recharts với cùng số liệu |
| 2 | Chỉ thẻ **"1. Hồ sơ đã nộp"** (khoảng 50) và thẻ **"1b. Tỷ lệ được tuyển"** | — |
| 3 | Chỉ lần lượt: **biểu đồ 2** "Top 15 kỹ năng theo số ứng viên", **biểu đồ 3** "Cung so với cầu theo kỹ năng", **biểu đồ 4** "Lương trung bình theo tháng và cấp bậc", **biểu đồ 5** "Lương trung bình theo địa điểm", **biểu đồ 6** "Phễu tuyển dụng", **biểu đồ 7** "Số tin đang mở theo nhóm nghề" | 3 chỉ số của đề (kỹ năng, lương, chuyển đổi) |
| 4 | Bấm mũi tên mở thanh **bộ lọc** bên trái (Cấp bậc, Địa điểm, Nhóm nghề, Nhóm kỹ năng), chọn một **Cấp bậc** | Các biểu đồ lương đổi theo |
| 5 | **Đăng xuất** → đăng nhập `hr5@smartcareer.vn` → Dashboard | Thẻ "Hồ sơ đã nộp" khoảng 39 và phễu **khác** `hr1` → minh chứng lọc theo công ty |
| 6 | Terminal tại `<repo>`: `python scripts/check_bi_views.py` | `view_checks` bốn view đều `true` |
| 7 | **Dự phòng nếu Superset không lên:** nói rõ "Superset chưa sẵn sàng nên trang dùng biểu đồ dự phòng", hoặc mở `docs\report\figures\ui_11_dashboard_bi.png` và nói rõ "đây là ảnh chụp" | — |

**Lời thoại:**
> "Mục 3: dashboard BI. Đây là dashboard Superset nhúng ngay trong trang nhà tuyển dụng, nối với bốn view SQL, dựng tự động bằng script và có bốn bộ lọc chung. Ba chỉ số của đề: số ứng viên theo kỹ năng, đặt cạnh số tin đang cần, cho thấy kỹ năng nào khan hiếm; xu hướng lương theo tháng và cấp bậc, cộng thêm lương theo địa điểm; và tỷ lệ chuyển đổi tuyển dụng qua các bước từ nộp hồ sơ đến được nhận. Phễu đếm số hồ sơ từng đạt mỗi bước theo lịch sử trạng thái, nên một hồ sơ đã được nhận vẫn được tính ở bước phỏng vấn. Số hồ sơ đã nộp và phễu chỉ gồm công ty của nhà tuyển dụng đang đăng nhập; khi đổi sang tài khoản công ty khác, số thay đổi, nhờ Row Level Security gắn điều kiện company_id vào token nhúng. Quản trị viên không bị lọc, ứng viên không được cấp token. Dữ liệu kỹ năng và lương là thị trường chung. Em chạy script đối chiếu: số liệu trên bốn view SQL khớp với API, và dashboard chỉ đọc được view bằng tài khoản BI chỉ đọc. Xin lưu ý: dữ liệu ứng tuyển và lương là mô phỏng, nên biểu đồ chỉ minh hoạ cách tính, không phản ánh thị trường thật."

**Lỗi thường gặp ở cảnh này:**
- Khung Superset trống → `docker compose logs bi-init`; chạy lại `docker compose up -d bi-init`; nếu đổi cổng web khác 8080 thì đặt `BI_EMBED_DOMAINS=http://localhost:<cổng>` trong `.env`.
- Cổng 8088 bị chiếm → đặt `SUPERSET_PORT` trong `.env` (và `SUPERSET_PUBLIC_URL` tương ứng), `docker compose up -d`.

---

## H. Cảnh 6 – Mục 04: Quản trị kỹ năng (5:30–6:10)

| Bước | Thao tác chi tiết | Kết quả mong đợi |
|---|---|---|
| 1 | **Đăng xuất** → đăng nhập `admin@smartcareer.vn` / `Demo@12345` | Vào giao diện quản trị |
| 2 | Menu trái → **Quản lý kỹ năng** | Bảng kỹ năng, nhóm, lộ trình học |
| 3 | Bấm tab **Alias**. Ô **Alias** gõ `reakt`, ô **Tên kỹ năng chuẩn** gõ `React` → **Thêm alias** | `reakt → React` xuất hiện trong "Alias hiện có" |
| 4 | **Đăng xuất** → đăng nhập `hr1` → **Đăng tin mới** → mô tả: `thành thạo reakt` → **Gợi ý kỹ năng từ mô tả** | Gợi ý ra **React** (nhận ra `reakt`) |
| 5 | (Tuỳ chọn, để dọn) quay lại admin, tab **Alias**, bấm **Xoá** cạnh `reakt` | Xoá alias |

**Lời thoại:**
> "Chức năng F10: quản trị viên quản lý danh mục kỹ năng và từ đồng nghĩa. Em thêm từ đồng nghĩa 'reakt' cho kỹ năng React. Quay lại form đăng tin, bộ gợi ý nhận ra 'reakt' là React ngay lập tức, vì danh mục này là nền của bộ đọc CV, điểm khớp và biểu đồ BI. Tài khoản ứng viên không vào được các API quản trị, backend trả lỗi bốn trăm lẻ ba."

---

## I. Cảnh 7 – Mục 05: Kiểm thử và đánh giá (6:10–7:30)

| Bước | Thao tác chi tiết | Kết quả mong đợi |
|---|---|---|
| 0 | Bên trái bấm phím **5** | Mục 05 sáng lên |
| 1 | Terminal tại `<repo>\backend`: `python -m pytest -q` (chờ khoảng 1 phút; cắt đoạn chờ khi dựng video) | `210 passed` |
| 2 | Mở `docs\testcases.md`, cuộn bảng 33 ca; chỉ cột "Kết quả thực tế" | 33 ca đều có kết quả thật (đạt) |
| 3 | Mở `docs\report\tables\model_comparison.csv` (hoặc mục 8.3 trong `docs\report\chuong_ai.md`). Chỉ cột `ndcg@10` và `roc_auc` | M3 0,995 / 0,980; M4 0,994 / 0,981; M5 0,992 / 0,990; M6 0,989 / 0,990; M0 0,976; M1 0,960; M2 0,945 |
| 4 | Mở `docs\report\tables\ndcg_bootstrap.csv` | M3, M4, M5 khác nhau không có ý nghĩa (khoảng tin cậy của chênh lệch chứa 0); M0, M1, M2 kém M3 có ý nghĩa |
| 5 | Mở `docs\report\tables\kappa.csv` (hoặc mục 8.1 `chuong_ai.md`) | kappa ≈ 0,934; ghi rõ "nhãn do agent AI gán" |
| 6 | Mở `BaoCao_TH3.md` mục 7 (Hạn chế) | Danh sách hạn chế |

**Lời thoại:**
> "Mục 5: kiểm thử và đánh giá. Hệ thống có hai trăm mười kiểm thử tự động: parser CV, đặc trưng, bảy mô hình, phân quyền, luật trạng thái, phễu BI, seed có kèm năm mươi file CV và migration trên cơ sở dữ liệu trống; trong đó M0 bản Python khớp một trăm phần trăm bản TypeScript của bài trước. Ngoài ra có ba mươi ba test case theo mười chức năng, chạy qua HTTP và trình duyệt tự động trên stack Docker thật, tất cả đều đạt. Để đánh giá mô hình gợi ý, nhóm chọn ba mươi ứng viên với mười tin mỗi người, tổng ba trăm cặp, gán nhãn mức phù hợp từ không đến ba. Xin nói rõ: nhãn do agent AI gán, hai lượt độc lập, không phải do người gán. Hệ số kappa giữa hai lượt là không phẩy chín ba bốn, nhưng vì cùng một họ mô hình nên con số này chỉ cho thấy agent gán nhất quán, chưa phải độ tin cậy như hai người. Kết quả: mô hình lai M3 có nDCG@10 cao nhất, khoảng không phẩy chín chín năm; M4 và M5 gần tương đương và không khác M3 có ý nghĩa thống kê theo khoảng tin cậy bootstrap; ba mô hình đơn giản M0, M1, M2 kém hơn rõ. Học máy không vượt mô hình lai đặt tay về thứ hạng; điểm cộng là ROC-AUC của M5 và M6 cao hơn, khoảng không phẩy chín chín so với không phẩy chín tám. Do chỉ có ba mươi ứng viên và nhãn dựa trên đúng loại thông tin mà các mô hình dùng, các con số có xu hướng lạc quan. Hạn chế còn lại: dữ liệu và đơn ứng tuyển là mô phỏng; trích kỹ năng chủ yếu dựa trên từ điển, so khớp mờ và embedding chứ chưa có mô hình nhận dạng thực thể riêng; CV dạng ảnh scan chưa đọc được."

---

## J. Cảnh 8 – Kết (7:30–8:00)

Bên trái bấm phím **0** (cả 5 mục); bên phải mở `BaoCao_TH3.md` mục 7 (Hạn chế) hoặc trang `/login`; nói link repo.

**Lời thoại:**
> "Tóm lại, nhóm đã xây hệ thống đủ năm mục của checklist: thiết kế cơ sở dữ liệu, mô hình AI chấm điểm có giải thích, dashboard BI nhúng, giao diện cho ba vai trò, và kiểm thử cùng đánh giá. Hạn chế chính: dữ liệu mô phỏng, nhãn do agent AI gán và quy mô nhỏ. Hướng phát triển: học từ phản hồi thật của nhà tuyển dụng, đối chiếu nhãn với con người, bổ sung nhận dạng thực thể cho CV, và thêm bộ lọc thời gian cho dashboard. Mã nguồn ở GitHub tbill111 TimKiemViecLam. Cảm ơn thầy cô đã xem."

---

## K. Xử lý sự cố khi quay

| Sự cố | Cách xử lý |
|---|---|
| Docker chưa chạy (`failed to connect to the docker API`) | Mở Docker Desktop, chờ xanh, `docker compose up -d` |
| Superset không lên / dashboard trống | `docker compose logs bi-init`; `docker compose up -d bi-init`; hoặc nói rõ trang đang dùng biểu đồ dự phòng; hoặc chiếu `docs\report\figures\ui_11_dashboard_bi.png` và nói là ảnh chụp |
| Cổng 8088/8080 bị chiếm | Đặt `SUPERSET_PORT`, `WEB_PORT`, `SUPERSET_PUBLIC_URL` trong `.env`; `BI_EMBED_DOMAINS=http://localhost:<WEB_PORT>`; `docker compose up -d` lại |
| Đơn ứng tuyển báo đã nộp | `docker compose exec api python -m seed.load_seed --reset` hoặc chọn tin khác |
| `hr1` không thấy ứng viên | Tin đã ứng tuyển không thuộc Sao Mai Software; chọn lại |
| Bấm tin mà không thấy điểm | Đợi hộp "Đang tính điểm khớp…" biến mất rồi bấm |
| Không có Docker | `VITE_OFFLINE_DEMO=true npm run dev` (email bắt đầu `hr…` → nhà tuyển dụng, `admin…` → quản trị); nói rõ đây là chế độ demo, không gọi API |

## L. Sau khi quay

1. Ghép các cảnh, kiểm tra âm thanh nghe rõ.
2. Nén: `ffmpeg -i demo.mp4 -vcodec libx264 -crf 28 -b:a 96k demo_small.mp4`. Phải ≤ 100 MB; vượt thì tăng `-crf` lên 30–32 hoặc hạ 1280×720.
3. Xem lại toàn video: đủ 5 mục theo thứ tự 01 → 05, không lộ thông tin cá nhân.
4. Đặt link repo và tên nhóm ở cảnh cuối; hỏi giảng viên có kênh nộp thêm báo cáo hay slide không.
5. **Nộp đúng 1 lần** trước 06:28 ngày 08/11/2026.

## M. Không được nói trong video

- Không nói nhãn do người gán; phải nói do agent AI gán.
- Không nói dữ liệu là thật hay lấy từ TopCV/LinkedIn; dữ liệu là mô phỏng.
- Không nói "học máy tốt hơn" hay "mô hình tốt hơn rõ rệt" khi M3, M4, M5 không khác nhau có ý nghĩa và chỉ có 30 ứng viên.
- Không đọc số nào không có trong `docs\report\tables\` hoặc lệnh vừa chạy trên màn hình.

## N. Đã chạy thử trước khi viết

Ngày 06/11/2026, nhánh này được build và chạy bằng `docker compose` ở cổng mặc định; các thao tác sau chạy thật bằng trình duyệt tự động: tải CV khi chưa và đã tích đồng ý (đúng hai thông báo ở cảnh 3), gõ `Sao Mai` ở Tìm việc (chỉ còn tin Sao Mai Software), ứng tuyển ("Ứng tuyển thành công!"), đơn hiện "Đã ứng tuyển" và không có ô chọn trạng thái, `hr1` thấy ứng viên ở Ứng viên xếp hạng và Kanban có nút "→ Đang xem xét" / "Từ chối". Cùng lần chạy: `run_testcases.py` 10/10, `e2e_ui.py` 16/16, `check_bi_views.py` bốn view `true`. Chữ trên giao diện có thể khác chút nếu bạn sửa code; hãy chạy thử một lượt trước khi quay.
