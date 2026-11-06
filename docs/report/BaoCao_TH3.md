# TH3 – Xây dựng Hệ thống Tìm việc Thông minh tích hợp AI và BI (SmartCareer v2)

> Bản tổng hợp trên nhánh `fix/main-chuan-checklist`. Số liệu lấy từ các tệp trong `docs/report/tables/` và từ lần chạy thật ghi ở mục 6; chương chi tiết: `chuong_ai.md`, `chuong_bi.md`, `chuong_giao_dien.md`, `chuong_csdl_kien_truc_api.md`.
> Mọi dữ liệu ứng viên, CV, tin và đơn ứng tuyển là **mô phỏng** (seed cố định 42, tên hư cấu).

## 1. Giới thiệu

**Bài toán.** Sinh viên và người mới tốt nghiệp khó biết mình phù hợp vị trí nào và còn thiếu kỹ năng gì; nhà tuyển dụng phải sàng lọc nhiều hồ sơ chất lượng không đều và thiếu số liệu để tối ưu quy trình.

**Mục tiêu.** Xây một nền tảng (1) tự động khớp kỹ năng ứng viên với yêu cầu công việc bằng điểm Matching Score *có giải thích*; (2) cung cấp dashboard BI cho nhà tuyển dụng: số ứng viên theo kỹ năng, xu hướng lương, tỷ lệ chuyển đổi tuyển dụng; (3) kiểm thử và đánh giá hiệu quả mô hình gợi ý.

**Kế thừa SmartCareer.** Prototype React ở bài cá nhân (10 màn hình, dữ liệu mẫu, điểm khớp theo quy tắc 60/25/15) được giữ làm baseline M0 và chế độ demo (`VITE_OFFLINE_DEMO=true`). Bài này thêm backend FastAPI, PostgreSQL, mô hình AI/ML (M0–M6), dashboard Superset và đánh giá.

**Kiến trúc.** Bốn dịch vụ Docker Compose: `db` (PostgreSQL 16), `api` (FastAPI + tầng AI), `superset` (BI), `web` (React + nginx).

## 2. Phân tích yêu cầu và thiết kế CSDL (mục 01)

### 2.1. Yêu cầu
Bốn tác nhân (ứng viên, nhà tuyển dụng, quản trị, dịch vụ AI), mười chức năng F01–F10 và yêu cầu phi chức năng: xem `docs/report/01_phan_tich_yeu_cau.md` (bảng đầy đủ, đưa vào báo cáo bản cuối).

### 2.2. Use Case
![Sơ đồ Use Case](figures/usecase.png)

Ba quan hệ `<<include>>` chính: *Tải CV* → *Trích kỹ năng*; *Xem việc gợi ý* → *Tính Matching Score*; *Đổi trạng thái* → *Ghi lịch sử trạng thái*. Đặc tả chi tiết ba use case (Tải CV, Xem việc gợi ý, Đổi trạng thái ứng tuyển, gồm luật chuyển và lỗi 409): `docs/usecase/dac_ta_use_case.md`.

### 2.3. ERD
![ERD 15 bảng](figures/erd.png)

15 bảng chia theo ba đối tượng của đề (ứng viên, nhà tuyển dụng, tin tuyển dụng) cộng nhóm tuyển dụng (đơn ứng tuyển, kết quả khớp) và danh mục. Giải thích quan hệ và ràng buộc: `docs/erd/giai_thich_erd.md`. Chương CSDL, migration, seed do Thái Anh viết: `docs/report/chuong_csdl_kien_truc_api.md`.

## 3. Mô hình AI (mục 02)
Chi tiết: `docs/report/chuong_ai.md`. Tóm tắt:
- **Phân tích CV:** parser 3 tầng (từ điển + alias → so khớp mờ ≥ 90 → embedding chỉ gợi ý) đọc PDF/DOCX/TXT; trên 50 CV tổng hợp đạt precision 0,989, recall 0,989, F1 0,989 (tầng 1+2+3); MAE số năm kinh nghiệm 0,118.
- **Điểm tương thích CV–JD:** 6 đặc trưng (`skill_req`, `skill_pref`, `semantic`, `exp`, `edu`, `pref`) và 7 mô hình: M0 quy tắc 60/25/15, M1 TF-IDF, M2 embedding, M3 hybrid (mặc định), M4 Logistic Regression, M5 Random Forest, M6 Gradient Boosting. Điểm luôn kèm giải thích (kỹ năng thiếu, thành phần điểm). Đổi tên, giới tính, tuổi ở phần đầu CV không làm đổi điểm (test công bằng).
- **Đánh giá:** 300 cặp CV–JD (30 ứng viên × 10 tin) có nhãn 0–3 và 50 CV có nhãn kỹ năng, **do agent AI gán** (kappa trọng số bình phương 0,934, không phải nhãn của người). nDCG@10: M3 0,995; M4 0,994; M5 0,992; M6 0,989; M0 0,976; M1 0,960; M2 0,945. M3, M4, M5 không phân biệt được với nhau (khoảng tin cậy bootstrap của chênh lệch chứa 0); học máy **không vượt** hybrid đặt tay về nDCG, chỉ có ROC-AUC cao hơn (M5/M6 ≈ 0,990 so với 0,980).

## 4. Dashboard BI (mục 03)
Chi tiết: `docs/report/chuong_bi.md`. Dashboard "Thị trường tuyển dụng" dựng bằng Apache Superset (`bi/superset/bootstrap.py`, bản xuất `bi/superset/dashboard_export.zip`), nhúng vào trang nhà tuyển dụng bằng guest token và Row Level Security theo công ty. Tám biểu đồ và bốn Native Filter (cấp bậc, địa điểm, nhóm nghề, nhóm kỹ năng) trên bốn view `v_*`: hồ sơ đã nộp, tỷ lệ được tuyển, **số ứng viên theo kỹ năng** (top 15), cung so với cầu theo kỹ năng, **xu hướng lương** theo tháng và cấp bậc, **phễu/tỷ lệ chuyển đổi tuyển dụng**, lương theo địa điểm, số tin theo nhóm nghề. Trang còn có biểu đồ Recharts dự phòng khi Superset không chạy. Dữ liệu ứng tuyển là mô phỏng: biểu đồ phễu minh hoạ cách tính, không chứng minh mô hình tốt.

## 5. Kiến trúc, API và giao diện (mục 04)
API, kiến trúc: `docs/report/chuong_csdl_kien_truc_api.md`. Giao diện (12 màn hình, ảnh chụp từ hệ thống chạy thật): `docs/report/chuong_giao_dien.md`. Giao diện gọi API AI (`/ai/match`, `/candidates/me/matches`, `/candidates/me/skill-gap`, `/jobs/{id}/ranked-candidates`, `/ai/extract-skills`) và API BI (`/bi/*`, `/bi/guest-token`); trang "Phân tích CV–JD" cho chọn mô hình M0–M6.

## 6. Kiểm thử và đánh giá (mục 05)

### 6.1. Kiểm thử tự động
`cd backend && python -m pytest` trên PostgreSQL 16: **210 passed** (60 giây). Phủ: parser CV, đặc trưng, M0–M6, phân quyền (401/403), luật trạng thái (409), tải CV (400/413/415/422), phân trang tin, M0 khớp bản TypeScript trên 84 ca, công bằng khi đổi phần đầu CV, hiệu năng 500 tin < 2 giây, `alembic upgrade head` trên CSDL trống (kể cả nâng cấp 0006 → 0007), seed kèm 50 file CV, notebook chạy được.

### 6.2. Test case
33 ca: `docs/testcases.md`. Kết quả: xem bảng trong tệp đó (số ca đạt tự động, số ca đạt qua `scripts/run_testcases.py` và trình duyệt, số ca chưa chạy).

### 6.3. Đối chiếu BI
`scripts/check_bi_views.py`: bốn view `v_skill_supply_demand`, `v_salary`, `v_funnel`, `v_funnel_stages` khớp kết quả API (4/4). Cách ly công ty (TC27): hồ sơ đã nộp thấy được là 50 (hr1), 39 (hr5), 1201 (admin). Guest token của nhà tuyển dụng mang RLS `company_id = <công ty>` cho cả hai dataset, của admin không có RLS, của ứng viên bị từ chối 403 (TC28).

### 6.4. Đánh giá mô hình
Bảng đầy đủ (P/R/F1 parser, so sánh M0–M6, bootstrap, ablation, độ quan trọng đặc trưng, phân tích lỗi): `chuong_ai.md` mục 8 và các tệp trong `docs/report/tables/`. Kết luận phải đọc kèm hạn chế ở mục 7: nhãn do agent AI gán và cỡ mẫu nhỏ nên số liệu có xu hướng lạc quan.

## 7. Hạn chế và hướng phát triển
- Dữ liệu ứng viên, CV, tin và đơn ứng tuyển là mô phỏng; xu hướng lương và tỷ lệ tuyển chỉ minh hoạ cách tính.
- Nhãn đánh giá (300 cặp CV–JD, kỹ năng 50 CV) do **agent AI** gán, không phải người; hai lượt gán cùng họ mô hình nên độ đồng thuận cao chỉ phản ánh độ nhất quán của agent, và nhãn dựa trên đúng loại thông tin mô hình dùng nên số liệu có xu hướng lạc quan. Cần đối chiếu với nhãn của con người trước khi kết luận chắc chắn; cỡ mẫu nhỏ (30 ứng viên × 10 tin) nên chênh lệch nhỏ giữa các mô hình không có ý nghĩa thống kê.
- Trích kỹ năng chủ yếu là từ điển + so khớp mờ + embedding; chưa có mô hình nhận dạng thực thể huấn luyện riêng (hướng: PhoBERT/NER).
- CV dạng ảnh scan không đọc được (hệ thống báo lỗi `no_text`, không đoán).
- Hướng phát triển: học từ phản hồi thật của nhà tuyển dụng; thêm đặc trưng nhóm nghề; mở rộng danh mục kỹ năng; thêm bộ lọc thời gian và biểu đồ 8 (so sánh điểm khớp với kết quả tuyển) cho Superset.
