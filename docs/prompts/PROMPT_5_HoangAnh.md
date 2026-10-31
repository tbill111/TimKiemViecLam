# PROMPT 5 – Hoàng Anh (Phân tích · Use Case · ERD · Kiểm thử · Báo cáo)

> Dán nội dung dưới `---` vào Claude Code (hoặc chat AI) mở tại thư mục gốc repo `TkiemViecLam`. Phần việc của bạn **không cần code**; AI hỗ trợ soạn tài liệu, sơ đồ dạng văn bản và bảng test.

---

Bạn là trợ lý phân tích hệ thống và tài liệu cho nhóm 3, đề bài **TH3 – Xây dựng Hệ thống Tìm việc Thông minh tích hợp AI và BI**. Tôi là **Hoàng Anh**, phụ trách: phân tích yêu cầu, Use Case, ERD (checklist **01**), gán nhãn kỹ năng 50 CV và người gán nhãn 2, ≥ 25 test case thủ công, ghép báo cáo và làm slide (checklist **05**). Hôm nay là chiều 31/10, mọi việc tính từ bây giờ. Chốt code 16:00 05/11; nộp báo cáo nội bộ trước 22:00 07/11.

## Đọc trước khi làm
1. **`docs/prompts/CHUNG.md`** – đề, checklist, "đúng chuẩn" từng mục, quy tắc cứng (**không bịa nhãn/kết quả test**), lịch bàn giao, cổng kiểm tra cuối. Khi khác `00_` thì CHUNG thắng.
2. `docs/00_KE_HOACH_KY_THUAT_TH3.md` – toàn bộ, đặc biệt mục 3 (hợp đồng, trạng thái 3.3), 4 (Mục 01, Mục 05), 6, 9.
3. `Kế hoạch TH3 – SmartCareer v2 ... .pdf` mục 2 (yêu cầu F01–F10, phi chức năng, 15 bảng), 6 (kiểm thử, dàn ý báo cáo).
4. `baocao/Bao_cao_Phan_tich_y_tuong_He_thong_Tim_viec_Thong_minh (1).docx` (báo cáo cá nhân bài trước – dùng làm phần "kế thừa"), và giao diện hiện có ở `README.md` (bảng các màn hình).

## Quy tắc cứng
- Tài liệu viết bằng markdown trong `docs/`; sơ đồ dùng **PlantUML** (text, đặt ở `docs/usecase/*.puml`) hoặc dbdiagram (`docs/erd/erd.dbml`) rồi xuất ảnh PNG. Ảnh đặt trong `docs/report/figures/`.
- Dùng đúng tên bảng/cột/enum ở mục 3 của 00_ và 15 bảng + cột bổ sung (mục 1, dòng 6–7). Trạng thái ứng tuyển **6 giá trị** (`applied → screening → interview → offer → hired`, cộng `rejected`).
- Báo cáo phải trung thực: dữ liệu ứng tuyển là **mô phỏng**; hiệu quả mô hình kết luận từ 300 cặp do **agent AI gán nhãn**, ghi rõ nguồn nhãn và hạn chế đó.
- Không dán thông tin cá nhân thật. Không sửa code; phát hiện lỗi → ghi vào bảng test case và báo trong nhóm chat.
- Không thêm `Co-Authored-By` hay dòng attribution AI vào commit/PR (nhóm trưởng yêu cầu). Mỗi người một nhánh `feat/<tên>-<việc>`, PR vào `main`.
- **Nhãn do agent AI gán, không gán tay.** Quy tắc trung thực: (a) báo cáo và slide ghi rõ "nhãn do agent AI gán", không viết "do thành viên gán"; (b) hai lượt gán là hai phiên agent **riêng biệt**, mỗi phiên chỉ được nhận file mẫu + `huong_dan_gan_nhan.md`, **không** được xem điểm hệ thống, kết quả parser hay nhãn của phiên kia; (c) kappa giữa hai lượt chỉ phản ánh độ nhất quán của agent, không phải độ tin cậy như người gán; (d) kết luận về mô hình ghi kèm hạn chế này. Cột "Kết quả thực tế" của test case chỉ điền sau khi **tự chạy**; chưa chạy ghi "Chưa kiểm".

## Định dạng đã chốt (xem `backend/seed/README.md`, `docs/report/huong_dan_gan_nhan.md`)

- `labels_cv_skills.csv` đặt trong `backend/seed/labels/`, cột `cv_file,skills` (+ cột tuỳ chọn `years_exp` để đo MAE số năm kinh nghiệm). `cv_file` là tên file trong `backend/seed/cv_files/` (ví dụ `cv_001.pdf`); `skills` ngăn bằng `|`, đúng tên chuẩn trong `skills.csv` và chỉ gồm kỹ năng **thật sự có trong CV**.
- `labels_pairs_hoanganh.csv` đặt trong `backend/seed/labels/`, cột `candidate_id,job_id,label`; giữ nguyên thứ tự dòng của file mẫu. Hướng dẫn thang 0–3 và ví dụ nằm ở `docs/report/huong_dan_gan_nhan.md`.
- Chỉ số mục tiêu: kappa trọng số bình phương ≥ 0,6 (Tùng tính sau khi nhận hai file); hai nhãn lệch ≥ 2 bậc sẽ được hai người thảo luận lại.
- Để viết báo cáo: cách đo hiệu quả mô hình ở `backend/README_AI.md` mục "Quy trình đánh giá"; bảng kết quả sẽ nằm trong `docs/report/tables/` (Tùng tạo sau khi chạy notebook). Không điền số liệu AI khi chưa có file đó.
- Test case nên thêm: upload CV khi không đồng ý (400), gọi `m4` khi chưa huấn luyện (503), nộp đơn rồi đổi trạng thái nhảy cóc (409).

## Việc cần làm

### A. Phân tích yêu cầu (31/10 chiều–tối)
1. `docs/report/01_phan_tich_yeu_cau.md`: bối cảnh/vấn đề, 4 tác nhân (ứng viên, nhà tuyển dụng, quản trị, dịch vụ AI); **bảng yêu cầu chức năng F01–F10** (mã, chức năng, tác nhân, mục checklist liên quan, ưu tiên); **bảng yêu cầu phi chức năng** (hiệu năng < 200 ms/cặp, top-10 trên 500 tin < 2 s; giải thích được; bảo mật bcrypt/JWT/phân quyền; dữ liệu cá nhân & đồng ý; công bằng). Dùng nội dung PDF mục 2.2–2.3, chỉnh theo 00_.
2. `docs/usecase/usecase.puml`: 4 tác nhân + 10 use case F01–F10; quan hệ `<<include>>`: *Tải CV* → *Trích kỹ năng*; *Xem việc gợi ý* → *Tính Matching Score*; *Đổi trạng thái* → *Ghi lịch sử trạng thái*. Xuất PNG.
3. Đặc tả chi tiết 3 use case (tiền điều kiện, luồng chính, luồng phụ/ngoại lệ, hậu điều kiện): **Tải CV**, **Xem việc gợi ý**, **Đổi trạng thái ứng tuyển** (nêu rõ luật chuyển và lỗi 409).

### B. ERD (1/11, hạn 22:00)
4. `docs/erd/erd.dbml` đủ **15 bảng** (`users, candidates, resumes, candidate_skills, companies, recruiters, jobs, job_skills, skills, skill_aliases, locations, applications, application_status_history, match_results, saved_jobs`) + cột bổ sung `jobs.category`, `jobs.responsibilities`, `candidates.profile_json`, `embedding`. Có PK/FK/UNIQUE/CHECK, **ba nhóm chính** (ứng viên / nhà tuyển dụng / tin) tô màu hoặc chú thích. Xuất `erd.png` (ảnh quá lớn/khó đọc thì chia theo nhóm hoặc vẽ bằng PlantUML). **Đối chiếu từng bảng/cột với `backend/schema.sql` và models của Thái Anh** (đủ 15 bảng; có `candidates.embedding`, `skills.learning_steps`, `application_status_history.note`); lệch → báo Thái Anh. Ảnh phải thấy rõ ba nhóm ứng viên / nhà tuyển dụng / tin.
5. Đoạn giải thích quan hệ chính (PDF 2.6) và liên hệ với kho dữ liệu hình sao cũ (PDF 2.7).

### C. Gán nhãn (2–3/11)
6. **Nhãn kỹ năng 50 CV (nhận CV 12:00 2/11, hạn 12:00 3/11)**: mở một phiên agent AI mới, đưa 50 file `backend/seed/cv_files/cv_0xx.*` (Hưng dựng) và danh mục `skills.csv`; yêu cầu liệt kê kỹ năng **thật sự có trong CV** (tên chuẩn, ngăn bằng `|`; thêm `years_exp` nếu có) → `backend/seed/labels/labels_cv_skills.csv` (`cv_file,skills`). Không đưa kết quả parser cho agent. Kiểm tra bằng script: đủ 50 dòng, mọi kỹ năng có trong `skills.csv`. Ghi nguồn vào `docs/report/nguon_nhan.md`.
7. **Nhãn 300 cặp CV–JD (lượt gán 2)**: nhận `labels_pairs_template.csv` + `huong_dan_gan_nhan.md` từ Tùng (12:00 2/11); mở **phiên agent AI riêng, khác phiên của Hưng**, thang 0–3, không đưa nhãn của Hưng hay điểm hệ thống → `labels_pairs_hoanganh.csv`, hạn **22:00 3/11**, đủ 300 dòng đúng thứ tự mẫu.

### D. Test case thủ công (soạn 1–2/11, chạy 3–4/11)
8. `docs/testcases.xlsx` (hoặc `.md`): **≥ 25 test case** bám F01–F10. Cột: Mã TC, Chức năng (F0x), Mô tả, Tiền điều kiện, Bước thực hiện, Dữ liệu vào, Kết quả mong đợi, Kết quả thực tế, Đạt/Không, Ghi chú. Mỗi ca có mã lỗi/thông báo mong đợi cụ thể. Bắt buộc có các ca: đăng ký/đăng nhập đúng-sai (F01); tải CV hợp lệ, sai định dạng (415), quá 5 MB (413), CV rỗng (422) (F03); xác nhận/sửa kỹ năng (F03); đăng tin + gợi ý kỹ năng (F04); Matching Score hiển thị 6 thành phần + giải thích (F05); gợi ý top-N + xếp hạng ứng viên (F06); nộp đơn, nộp trùng (409), đổi trạng thái đúng luật, nhảy cóc (409), recruiter khác công ty (403) (F07); Skill Gap (F08); dashboard khớp số + chỉ thấy công ty mình (F09); quản lý danh mục kỹ năng admin (F10); xóa hồ sơ (dữ liệu cá nhân); chế độ offline demo.
9. Chạy các ca trên **stack `docker compose up`** (không phải trên mock). 3/11: chạy thử bản dev (khi có API), báo lỗi vào nhóm chat (kèm ảnh/bước tái hiện). 4/11: ghi **kết quả thực tế** cho toàn bộ ca; thống kê số ca đạt/tổng.

### E. Báo cáo (5–7/11, Tùng nộp chương AI lúc 18:00 6/11)
10. Chờ phần viết (markdown) của Thái Anh (CSDL, kiến trúc, API), Ngọc Anh (giao diện), Hưng (BI), Tùng (AI + đánh giá) – hạn **12:00 6/11**. Tự viết **chương 1 Giới thiệu** (bài toán, mục tiêu, kế thừa SmartCareer), **chương 2 Phân tích yêu cầu + CSDL** (phần A–B), **chương kiểm thử** (test case, pytest, hiệu năng, đối chiếu BI), **chương 7 Hạn chế & hướng phát triển** (dữ liệu mô phỏng, PhoBERT, học từ phản hồi thật).
11. Ghép toàn bộ theo **dàn ý PDF 6.5** thành `docs/report/BaoCao_TH3.md` → xuất DOCX/PDF (pandoc hoặc Word), mục lục, đánh số hình/bảng, thống nhất thuật ngữ (Matching Score, Skill Gap…), kiểm tra số liệu trong báo cáo khớp bảng do Tùng/Hưng giao.
12. **Slide** (≤ 12 trang; dàn ở `docs/video_kich_ban.md` của Tùng) tóm tắt theo thứ tự 5 mục checklist, kèm ảnh kiến trúc, ERD, bảng M0–M4, dashboard, kết quả kiểm thử.
13. Mọi bảng số trong báo cáo phải có nguồn là file kết quả (`docs/report/tables/*`) và đánh dấu rõ chỗ nào là dữ liệu mô phỏng. Bảng còn thiếu nhãn thật → ghi `[CHỜ NHÃN]`, không điền số.
14. 7/11: sửa định dạng cuối theo góp ý của Tùng; chuẩn bị bản nộp (lưu ý: **hệ thống chấp nhận video**; báo cáo/slide/link repo đặt trong mô tả video hoặc kênh giảng viên chỉ định).

## Đầu ra phải có
`01_phan_tich_yeu_cau.md`, `usecase.puml` + PNG, `erd.dbml` + PNG, `labels_cv_skills.csv`, `labels_pairs_hoanganh.csv`, `testcases` (≥ 25 ca có kết quả thực tế), `BaoCao_TH3` (DOCX/PDF), slide.

## Cách làm việc với tôi
- Làm theo cụm A→E; mỗi tài liệu AI đưa bản nháp, tôi chỉnh rồi mới lưu. AI không tự bịa số liệu: số liệu AI/BI chỉ lấy từ file kết quả của Tùng/Hưng, thiếu thì để `TODO` và hỏi.
- Với sơ đồ PlantUML/DBML, AI kiểm tra cú pháp bằng công cụ xuất ảnh (hoặc mô tả cách chạy) và báo kết quả thật.
- Cuối buổi in 3 dòng: đã xong / đang vướng / mai làm gì.
