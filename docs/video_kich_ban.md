# Kịch bản video TH3 – SmartCareer v2 (8 phút)

Đề: **TH3 – Xây dựng Hệ thống Tìm việc Thông minh tích hợp AI và BI**. Video phải cho thấy cả 5 mục checklist theo thứ tự 01 → 05.
**Ràng buộc nộp:** chỉ nhận MP4/MOV/MKV/AVI/WEBM, ≤ 101 MB, **nộp 1 lần**, hạn **08/11/2026 06:28** (ân hạn 15 phút). Nhóm nộp nội bộ trước 22:00 07/11.

> Kịch bản này dựng cho hệ thống chạy trọn bằng `docker compose up` (nhánh có đủ backend, giao diện, Superset, dữ liệu và nhãn). Nếu quay từ nhánh khác, các số ở mục 3 (Seed) và mục 7 (Đánh giá) phải đổi theo đúng file kết quả của nhánh đó.

---

## 0. Chuẩn bị trước khi quay (làm xong 1 giờ trước)

**Nếu máy vừa khởi động lại:** mở **Docker Desktop** và chờ biểu tượng cá voi chuyển xanh (khoảng 1–2 phút) rồi mới chạy lệnh dưới.

```bash
cp .env.example .env                        # nhớ WITH_ST=1 (model embedding thật)
docker compose up -d --build
docker compose exec api python -m seed.load_seed --reset     # dữ liệu sạch: ứng viên demo chỉ ứng tuyển được 1 lần mỗi tin
python scripts/check_bi_views.py            # phải in "TẤT CẢ ĐẠT"
cd backend && python -m pytest -q           # chạy sẵn một lần để biết kết quả (235 passed)
```

**Mở sẵn các tab / cửa sổ (theo thứ tự quay):**

| # | Tab | Địa chỉ hoặc file |
|---|---|---|
| 1 | Slide (≤ 12 trang) | `docs/report/Slide_TH3.pptx` |
| 2 | Ảnh Use Case | `docs/usecase/usecase.png` |
| 3 | Ảnh ERD | `docs/erd/erd.png` |
| 4 | Ứng dụng | http://localhost:8080 (đã **đăng xuất**) |
| 5 | Swagger (dự phòng) | http://localhost:8000/docs |
| 6 | Terminal đã `cd` vào `backend` | để chạy `pytest` |
| 7 | Bảng kết quả | `docs/report/tables/model_comparison.csv` và `docs/report/BaoCao_TH3.md` mục 6 |
| 8 | Trình xem file | `public/cv-mau.pdf` (CV mẫu để tải lên) |

**Tài khoản (mật khẩu chung `Demo@12345`):** ứng viên `tung.demo@smartcareer.vn`; nhà tuyển dụng `hr01@smartcareer.vn` (Sao Mai Software) và `hr05@smartcareer.vn` (công ty khác, dùng để so sánh); quản trị `admin@smartcareer.vn`.

**Mẹo quay:** độ phân giải 1920×1080, thu nhỏ trình duyệt 90–100%, tắt thông báo, mở sẵn các tab để không phải tìm. Thu tiếng bằng micro rời. Quay từng cảnh riêng rồi ghép, mỗi cảnh có thể quay lại nếu vấp.

---

## 1. Bảng thời gian

| Thời gian | Mục | Cảnh | Người gợi ý đọc |
|---|---|---|---|
| 0:00 – 0:30 | Mở đầu | Slide 1–2 | Tùng |
| 0:30 – 1:30 | **01** CSDL và phân tích | Use Case, ERD, dữ liệu | Hoàng Anh |
| 1:30 – 3:30 | **02** AI/ML và **04** giao diện ứng viên | Ứng dụng: ứng viên | Tùng |
| 3:30 – 4:30 | **04** luồng ứng tuyển và nhà tuyển dụng | Ứng dụng: Kanban | Ngọc Anh |
| 4:30 – 5:30 | **03** BI | Dashboard | Hưng |
| 5:30 – 6:10 | **04** quản trị | Quản lý kỹ năng | Thái Anh |
| 6:10 – 7:30 | **05** kiểm thử và đánh giá | Terminal, bảng kết quả | Tùng, Hoàng Anh |
| 7:30 – 8:00 | Kết | Slide cuối | Tùng |

Một người đọc hết cũng được; chia người chỉ để đa dạng giọng. Lời thoại bên dưới khoảng 1.100 chữ, đọc chậm vừa phải là đủ 8 phút.

---

## 2. Mở đầu (0:00 – 0:30)

**Màn hình:** `Slide_TH3.pptx` slide 1 (tên đề, nhóm 3), rồi slide 2 (bài toán và kiến trúc 4 dịch vụ).

**Lời thoại:**
> "Xin chào, đây là bài thực hành TH3 của nhóm 3: Xây dựng hệ thống tìm việc thông minh tích hợp AI và BI, tên SmartCareer v2.
> Bài toán: sinh viên mới ra trường khó biết mình hợp vị trí nào và còn thiếu kỹ năng gì, còn nhà tuyển dụng phải sàng lọc rất nhiều hồ sơ. Hệ thống của nhóm dùng AI để tính điểm khớp giữa CV và mô tả công việc, kèm giải thích, và dùng dashboard BI để phân tích thị trường tuyển dụng.
> Hệ thống chạy bằng một lệnh docker compose gồm bốn dịch vụ: cơ sở dữ liệu PostgreSQL, backend FastAPI có tầng AI, Apache Superset cho BI, và giao diện React. Video đi theo năm mục của checklist."

---

## 3. Mục 01 – Phân tích yêu cầu và thiết kế CSDL (0:30 – 1:30)

**Thao tác:**
1. Mở `docs/usecase/usecase.png`: chỉ 4 tác nhân (ứng viên, nhà tuyển dụng, quản trị, dịch vụ AI) và 10 chức năng F01–F10; chỉ vào 3 mũi tên `<<include>>`.
2. Mở `docs/erd/erd.png`: chỉ 3 nhóm màu "Ứng viên", "Nhà tuyển dụng", "Tin tuyển dụng"; đếm 15 bảng.
3. Mở Swagger http://localhost:8000/docs (cuộn qua danh sách endpoint, 3–4 giây) hoặc chỉ vào terminal `psql \dt`.

**Lời thoại:**
> "Mục 1: phân tích yêu cầu và thiết kế cơ sở dữ liệu. Hệ thống có bốn tác nhân và mười chức năng từ F01 đến F10: tài khoản, hồ sơ, tải CV, đăng tin, điểm khớp, gợi ý, ứng tuyển, Skill Gap, dashboard và quản lý danh mục kỹ năng. Quan hệ include chính: tải CV gọi trích kỹ năng; xem việc gợi ý gọi tính điểm khớp; đổi trạng thái gọi ghi lịch sử.
> Cơ sở dữ liệu có mười lăm bảng, chia theo ba đối tượng của đề bài: ứng viên, nhà tuyển dụng và tin tuyển dụng, cộng nhóm tuyển dụng và danh mục. Đơn ứng tuyển có ràng buộc không nộp trùng và sáu trạng thái; mỗi lần đổi trạng thái ghi một dòng lịch sử, và phễu BI được tính từ lịch sử đó.
> Dữ liệu mẫu hoàn toàn hư cấu, sinh bằng script với seed cố định: một trăm linh tám kỹ năng, ba mươi công ty, một trăm năm mươi tin tuyển dụng rải đều mười hai tháng, hơn ba trăm ứng viên và khoảng một nghìn hai trăm đơn ứng tuyển. Nhóm không lấy dữ liệu từ TopCV hay LinkedIn vì điều khoản không cho phép."

*(Các số kỹ năng, ứng viên, đơn lấy từ lần seed của bạn; nếu `load_seed` in số khác thì đọc theo số đó.)*

---

## 4. Mục 02 + 04 – AI/ML và giao diện ứng viên (1:30 – 3:30)

**Thao tác (theo thứ tự):**
1. http://localhost:8080 → đăng nhập `tung.demo@smartcareer.vn` / `Demo@12345`. Dừng ở **Tổng quan** 3 giây.
2. **Tìm việc**: cuộn, chỉ điểm khớp trên mỗi thẻ (chờ vài giây cho điểm tải xong); mở một tin, chỉ kỹ năng có / thiếu.
3. **Hồ sơ của tôi → khung "Nhập kỹ năng từ CV"**: chọn `public/cv-mau.pdf`, **tích ô đồng ý**, bấm tải; chỉ danh sách kỹ năng đề xuất; bỏ chọn một kỹ năng, bấm xác nhận.
4. **Phân tích CV–JD**: chọn một tin; đổi mô hình **M0 → M3**; chỉ **6 thành phần** và câu giải thích; chọn **M4** (nếu đã huấn luyện sẽ chạy; nhớ chỉ dòng ghi chú về nguồn nhãn).
5. **Skill Gap**: chỉ kỹ năng bắt buộc đứng trước và mở một lộ trình học 3 bước.

**Lời thoại:**
> "Mục 2 và 4: mô hình AI và giao diện. Em đăng nhập bằng tài khoản ứng viên. Mỗi tin ở trang Tìm việc có điểm khớp từ 0 đến 100, tính bằng mô hình AI chứ không phải số cố định.
> Khi ứng viên tải CV, phải tích đồng ý xử lý dữ liệu. Hệ thống đọc CV, trích kỹ năng theo ba tầng: tra từ điển và từ đồng nghĩa, so khớp mờ để bắt lỗi gõ, và embedding để gợi ý kỹ năng gần nghĩa. Kỹ năng từ embedding chỉ là gợi ý, ứng viên tự xác nhận, nên điểm chỉ dựa trên kỹ năng đã xác nhận. Phần đầu CV, gồm tên và thông tin liên hệ, bị loại khỏi văn bản dùng để chấm, nên điểm không phụ thuộc nhân thân.
> Trang Phân tích CV–JD cho đổi giữa năm mô hình: M0 là quy tắc sáu mươi, hai lăm, mười lăm của bài trước; M1 dùng TF-IDF; M2 dùng embedding; M3 là mô hình lai sáu đặc trưng với luật chặn khi thiếu hơn một nửa kỹ năng bắt buộc; M4 là hồi quy logistic học trọng số. Mỗi điểm đều có sáu thành phần và một câu giải thích: đã có gì, còn thiếu gì.
> Trang Skill Gap liệt kê kỹ năng còn thiếu, kỹ năng bắt buộc xếp trước, kèm lộ trình học ba bước. Về tốc độ, chấm một cặp mất khoảng sáu mươi mili giây, lấy điểm cho cả một trăm năm mươi tin mất chưa đến một giây, đo qua HTTP với model embedding thật."

**Nếu M4 báo chưa huấn luyện:** chỉ vào thông báo lỗi tại chỗ và nói: "M4 cần huấn luyện bằng nhãn; khi chưa có thì giao diện báo rõ và các mô hình khác vẫn dùng được."

---

## 5. Mục 04 – Ứng tuyển và nhà tuyển dụng (3:30 – 4:30)

**Thao tác:**
1. Ứng viên: ở **Tìm việc** gõ "Sao Mai" vào ô tìm kiếm và **chọn một tin của công ty Sao Mai Software** (bắt buộc: `hr01` chỉ thấy đơn nộp vào tin của công ty mình) → **Ứng tuyển** → xác nhận → thấy "Ứng tuyển thành công". Vào **Việc đã lưu & Ứng tuyển**, tab theo dõi: chỉ trạng thái (chỉ xem).
2. **Đăng xuất** → đăng nhập `hr01@smartcareer.vn` (vào thẳng **Dashboard BI**) → bấm menu **Ứng viên xếp hạng**.
3. **Ứng viên xếp hạng** (`/employer/candidates`): chọn tin vừa ứng tuyển; chỉ danh sách xếp theo điểm khớp, kèm lý do và kỹ năng thiếu. Trang này đồng thời là **bảng Kanban 6 cột** (không có trang Kanban riêng).
4. Trên Kanban: bấm nút chuyển sang bước kế tiếp cho ứng viên demo ("Tung" / Giang Thanh Tùng). Để cho thấy lỗi **nhảy cóc**, giao diện chỉ hiện nút hợp lệ nên dùng Swagger (http://localhost:8000/docs → chạy `POST /api/auth/login` với `hr01@smartcareer.vn` / `Demo@12345`, copy `access_token` rồi bấm Authorize; **làm trước khi quay** để thao tác nhanh): `PATCH /api/applications/{id}/status` với `{"status":"offer"}` khi đơn đang `applied` → thấy `invalid_transition` (HTTP 409).
5. **Đăng tin mới → Gợi ý kỹ năng từ mô tả**: dán một mô tả có "React", "Docker"; chọn từng kỹ năng là bắt buộc hay ưu tiên (không cần bấm đăng).

**Lời thoại:**
> "Ứng viên bấm ứng tuyển, đơn được lưu kèm điểm khớp tại thời điểm nộp. Ứng viên chỉ xem được trạng thái, không tự đổi.
> Sang vai trò nhà tuyển dụng của công ty Sao Mai. Trang Ứng viên xếp hạng sắp xếp theo điểm khớp, kèm lý do khớp và kỹ năng thiếu, và là bảng Kanban sáu cột; nhà tuyển dụng chỉ chuyển sang bước kế tiếp hoặc từ chối. Nếu cố nhảy cóc bước, backend trả lỗi bốn trăm lẻ chín và giao diện báo rõ. Mỗi lần chuyển được ghi vào lịch sử trạng thái, và nhà tuyển dụng của công ty khác không đổi được đơn này.
> Khi đăng tin, nút Gợi ý kỹ năng đọc mô tả công việc và đề xuất kỹ năng; nhà tuyển dụng chọn kỹ năng nào là bắt buộc, kỹ năng nào là ưu tiên."

---

## 6. Mục 03 – Dashboard BI (4:30 – 5:30)

**Thao tác:**
1. Đăng nhập `hr01@smartcareer.vn` (vào thẳng **Dashboard BI**, http://localhost:8080/employer/dashboard); **chờ 5–8 giây** cho Superset nhúng tải xong. Bốn thẻ trên cùng (301 ứng viên, 150 tin, hồ sơ đã nộp, tỷ lệ tuyển) là số **toàn thị trường**; các biểu đồ Superset bên dưới (ví dụ "Hồ sơ đã nộp" khoảng 20) đã **lọc theo công ty** — nói rõ điều này để không bị hiểu là số lệch nhau.
2. Chỉ lần lượt **3 chỉ số của đề**: (a) biểu đồ 2 và 3 (ứng viên theo kỹ năng, cung so với cầu); (b) biểu đồ 4 (lương theo tháng và cấp bậc); (c) biểu đồ 6 (phễu). **Bỏ qua biểu đồ 8** (tỷ lệ tuyển theo nhóm điểm): với một công ty nhỏ nó thường hiện 0%, dễ gây hiểu nhầm.
3. Đăng xuất → đăng nhập `hr05@smartcareer.vn` → mở lại dashboard: **phễu khác** công ty trước (RLS).
4. Terminal: `python scripts/check_bi_views.py` → dừng ở dòng **"TẤT CẢ ĐẠT"**.
5. (Dự phòng nếu Superset không lên) chiếu `bi/screenshots/dashboard_superset_embedded.png` và `bi/screenshots/dashboard_recharts_fallback.png`.

**Lời thoại:**
> "Mục 3: dashboard BI. Đây là dashboard Superset nhúng ngay trong trang nhà tuyển dụng, nối với bốn view SQL. Ba chỉ số của đề: số lượng ứng viên theo kỹ năng, so với số tin đang cần, cho thấy kỹ năng nào khan hiếm; xu hướng lương theo tháng và cấp bậc; và tỷ lệ chuyển đổi tuyển dụng qua các bước từ nộp hồ sơ đến được nhận.
> Phễu đếm số hồ sơ từng đạt mỗi bước theo lịch sử trạng thái, nên một hồ sơ đã được nhận vẫn được tính ở bước phỏng vấn. Mỗi nhà tuyển dụng chỉ thấy số của công ty mình: khi đổi sang tài khoản công ty khác, phễu thay đổi. Điều này được thực hiện bằng Row Level Security trong token nhúng của Superset.
> Em chạy script đối chiếu: số liệu trên view SQL khớp với API ở mọi chỉ số, và tài khoản BI chỉ đọc được view, không đọc được bảng người dùng.
> Xin lưu ý: dữ liệu ứng tuyển và lương là mô phỏng, nên biểu đồ chỉ minh hoạ cách tính, không phản ánh thị trường thật."

---

## 7. Mục 04 – Quản trị kỹ năng (5:30 – 6:10)

**Thao tác:**
1. Đăng xuất → đăng nhập `admin@smartcareer.vn` (vào Dashboard BI) → bấm menu **Quản lý kỹ năng**.
2. Thêm một **từ đồng nghĩa** (alias): ví dụ `reakt` → `React`.
3. Đăng nhập lại `hr01@…` → **Đăng tin mới** → mô tả "thành thạo reakt" → **Gợi ý kỹ năng** → ra **React**.

**Lời thoại:**
> "Chức năng F10: quản trị viên quản lý danh mục kỹ năng. Em thêm từ đồng nghĩa 'reakt' cho kỹ năng React. Quay lại form đăng tin, bộ gợi ý kỹ năng nhận ra 'reakt' là React ngay lập tức, vì danh mục này là nền của bộ đọc CV, điểm khớp và biểu đồ BI."

---

## 8. Mục 05 – Kiểm thử và đánh giá (6:10 – 7:30)

**Thao tác:**
1. Terminal: `cd backend && python -m pytest -q` → chờ ra **235 passed** (cắt đoạn chờ khi dựng video).
2. Mở `docs/testcases.md`: cuộn qua bảng 46 ca; chỉ cột "Kết quả thực tế".
3. Mở `docs/report/tables/model_comparison.csv` (hoặc bảng 6.4 trong `BaoCao_TH3.md`): chỉ hàng M0–M4, cột `ndcg@10`, `roc_auc`.
4. Mở `docs/report/tables/kappa.csv` hoặc mục 6.1 của báo cáo: chỉ kappa và dòng "nhãn do agent AI gán".
5. Mở `docs/report/BaoCao_TH3.md` mục 7 (hạn chế).

**Lời thoại:**
> "Mục 5: kiểm thử và đánh giá. Hệ thống có hai trăm ba mươi lăm kiểm thử tự động: parser CV, đặc trưng, năm mô hình, phân quyền, luật trạng thái, phễu BI, seed và migration; trong đó có kiểm tra M0 bản Python khớp một trăm phần trăm bản TypeScript của bài trước. Ngoài ra có bốn mươi sáu test case theo mười chức năng và kiểm thử trình duyệt tự động trên stack Docker thật, mười bốn bước đều đạt.
> Để đánh giá mô hình gợi ý, nhóm chọn ba mươi ứng viên với mười tin mỗi người, tổng ba trăm cặp, gán nhãn mức phù hợp từ không đến ba. Xin nói rõ: nhãn do **agent AI** gán, hai lượt độc lập, không phải do người gán. Hệ số kappa giữa hai lượt là 0,959, nhưng vì cùng một họ mô hình nên con số này chỉ cho thấy agent gán nhất quán, chưa phải độ tin cậy như hai người.
> Kết quả: mô hình lai M3 có nDCG@10 cao nhất, khoảng 0,988 và ROC-AUC khoảng 0,984; M4 gần tương đương nhưng không vượt M3; mô hình quy tắc M0 đứng sát phía sau. Do chỉ có ba mươi ứng viên và nhãn dựa trên đúng loại thông tin mà các mô hình dùng, chênh lệch nhỏ giữa các mô hình không có ý nghĩa thống kê, và các con số này có xu hướng lạc quan.
> Hạn chế còn lại: dữ liệu và đơn ứng tuyển là mô phỏng; trích kỹ năng chủ yếu dựa trên từ điển, so khớp mờ và embedding chứ chưa có mô hình nhận dạng thực thể riêng; CV dạng ảnh scan chưa đọc được."

*(Các số nDCG@10 0,988, ROC-AUC 0,984, kappa 0,959 lấy từ `docs/report/tables/`. Nếu chạy lại notebook thì đọc theo số mới. **Không đọc số nào không có trong file kết quả.**)*

---

## 9. Kết (7:30 – 8:00)

**Màn hình:** slide cuối "Hạn chế và hướng phát triển", hiện link repo và tên nhóm.

**Lời thoại:**
> "Tóm lại, nhóm đã xây hệ thống đủ năm mục của checklist: thiết kế cơ sở dữ liệu, mô hình AI chấm điểm có giải thích, dashboard BI nhúng, giao diện cho ba vai trò, và kiểm thử cùng đánh giá. Hướng phát triển: học từ phản hồi thật của nhà tuyển dụng, đối chiếu nhãn với con người, bổ sung nhận dạng thực thể cho CV, và thêm bộ lọc nâng cao cho dashboard. Cảm ơn thầy cô đã xem."

---

## 10. Dự phòng khi quay (nếu có sự cố)

| Sự cố | Cách xử lý |
|---|---|
| Superset không lên hoặc dashboard trống | Giao diện tự dùng biểu đồ dự phòng; chiếu thêm `bi/screenshots/dashboard_superset_embedded.png`; nói rõ "đây là ảnh chụp" |
| Cổng 8088 bị chiếm | Đặt `SUPERSET_PORT` trong `.env` (xem `bi/README.md`), `docker compose up -d` lại |
| Tải CV báo lỗi | Kiểm tra đã tích đồng ý; dùng đúng `public/cv-mau.pdf`; xem `docker compose logs api` |
| Ứng tuyển báo "đã ứng tuyển" | Chạy lại `docker compose exec api python -m seed.load_seed --reset` hoặc chọn tin khác |
| Mất mạng / máy không có Docker | Chạy chế độ demo không backend: `VITE_OFFLINE_DEMO=true npm run dev` (đăng nhập email bất kỳ, `hr…` để xem màn nhà tuyển dụng, `admin…` cho quản trị); nói rõ đây là chế độ demo |
| Điểm khớp chưa hiện khi mở tin | Đợi trang tải xong điểm (vài giây) rồi mới bấm vào tin |

---

## 11. Sau khi quay

1. Ghép các cảnh, thêm phụ đề tiếng Việt nếu cần; kiểm tra âm thanh nghe rõ.
2. Xuất H.264 rồi nén để ≤ 100 MB:
   ```bash
   ffmpeg -i demo.mp4 -vcodec libx264 -crf 28 -b:a 96k demo_small.mp4
   ```
   Kiểm tra dung lượng: nếu vượt 100 MB thì tăng `-crf` lên 30–32 hoặc giảm độ phân giải xuống 1280×720.
3. Xem lại toàn bộ video một lần: có đủ **5 mục theo thứ tự 01 → 05**, không lộ mật khẩu thật hay thông tin cá nhân ngoài tài khoản demo.
4. Đặt link repo và tên nhóm ở cảnh cuối (và ở mô tả nếu nền tảng cho phép). Hỏi giảng viên có kênh nộp thêm báo cáo hay slide không.
5. **Nộp đúng 1 lần** trước 06:28 ngày 08/11/2026; nhóm nộp nội bộ trước 22:00 ngày 07/11 để còn thời gian sửa.

## 12. Dàn slide (≤ 12 trang, `docs/report/Slide_TH3.pptx`)

1. Đề và mục tiêu · 2. Kiến trúc 4 dịch vụ · 3. Use Case và 10 chức năng · 4. ERD 15 bảng · 5. Parser CV và 6 đặc trưng · 6. Năm mô hình M0–M4 · 7. Kết quả đánh giá (bảng 6.4, ghi rõ nhãn do agent AI gán) · 8. Dashboard BI · 9. Luồng ứng viên và nhà tuyển dụng (ảnh chụp) · 10. Kiểm thử và hiệu năng · 11. Hạn chế · 12. Hướng phát triển.

## 13. Những điều **không** được nói trong video

- Không nói nhãn do người gán; phải nói rõ do agent AI gán.
- Không nói dữ liệu là thật hay lấy từ TopCV/LinkedIn; dữ liệu là mô phỏng.
- Không nói "mô hình tốt hơn rõ rệt" khi chênh lệch giữa M0–M4 nhỏ và chỉ có 30 ứng viên.
- Không đọc con số nào không có trong `docs/report/tables/` hoặc trong lệnh vừa chạy trên màn hình.
