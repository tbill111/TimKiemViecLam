# PROMPT 3 – Ngọc Anh (Frontend React + tích hợp API)

> Dán nội dung dưới `---` vào Claude Code mở tại thư mục gốc repo `TkiemViecLam`.

---

Bạn là kỹ sư frontend của nhóm 3, đề bài **TH3 – Xây dựng Hệ thống Tìm việc Thông minh tích hợp AI và BI**. Tôi là **Ngọc Anh**, phụ trách mục checklist **04 (giao diện + tích hợp API AI/BI)**. Hạn chốt code 16:00 05/11/2026. Hôm nay là chiều 31/10 nên mọi việc tính từ bây giờ.

## Đọc trước khi làm (bắt buộc)
1. `docs/00_KE_HOACH_KY_THUAT_TH3.md` – mục 1 (sửa so với repo), 3 (hợp đồng, bảng adapter 3.2, trạng thái 3.3, API 3.4), 4 (Mục 04), 5.
2. Code frontend: `src/App.tsx`, `src/types/index.ts`, `src/hooks/useAppState.ts`, `src/utils/index.ts`, các trang trong `src/pages/`, `src/components/` (`layout/Sidebar.tsx`, `profile/CvImport.tsx`, `jobs/*`), `vite.config.ts`, `tsconfig.app.json`.

## Quy tắc cứng (đặc thù repo)
- React 19 + Vite + **TypeScript** + Tailwind 4 + react-router-dom 7 + lucide-react + recharts. Giữ phong cách code, class CSS (`badge-*`, `card`…) và tiếng Việt hiện có trong giao diện.
- `tsconfig`: `erasableSyntaxOnly` (**cấm** `enum`, `namespace`, parameter properties), `verbatimModuleSyntax` (dùng `import type { … }`), `noUnusedLocals/Parameters`. Phải qua `npm run build` và `npm run lint` sau mỗi cụm việc.
- Không đổi tên/kiểu trường của `Job`, `StudentProfile`, `SkillMatchResult` hiện có (chỉ **thêm trường tùy chọn**). Dùng adapter ở `src/api/adapters.ts` để chuyển từ JSON backend (mục 3.2 của 00_). `id` ở frontend luôn là `string`.
- `useAppState` giữ nguyên **chữ ký trả về** (`UseAppState`) để các trang gọi `applyToJob`, `saveJob`, `updateProfile`… không phải đổi.
- `VITE_OFFLINE_DEMO=true` phải chạy được **toàn bộ** như bản hiện tại (không cần backend); đây là phương án cứu khi demo. Chế độ mặc định là online.
- Không động tới `backend/**`, `bi/**`. Cần đổi API → báo Tùng/Thái Anh.
- Trong khi API chưa sẵn sàng, dùng fixture JSON của Tùng (MatchDTO mẫu từ Tùng lúc 20:00 31/10) và mock bằng `msw` hoặc một lớp `mock` đơn giản trong `src/api/mock/` – không để mock lọt vào chế độ mặc định khi API đã chạy.

## Ghi chú từ API AI đã viết sẵn (nhánh `feat/tung-ai-ml`: `backend/app/routers/ai.py`, `resumes.py`)

Hình dạng response thật (đã có test), dùng để làm mock chính xác:
- `POST /ai/match` → MatchDTO: `{model, model_version, total_score, components{skill_req,skill_pref,semantic,exp,edu,pref}, matched_required, missing_required, matched_preferred, missing_preferred, location_match, work_type_match, explanation}`. Với `m0`, `components.semantic/exp/edu` là `null`; điểm 0–100 là số nguyên.
- `GET /candidates/me/matches?model=` → `{items:[{job_id, match}]}`; `GET /candidates/me/recommendations?top=&model=` cùng dạng, đã xếp giảm dần.
- `GET /candidates/me/skill-gap?job_id=` → `{job_id, match_score, missing:[{skill, required, jobs_demanding, learning_steps[]}]}`; kỹ năng bắt buộc đứng trước.
- `GET /jobs/{id}/ranked-candidates?top=&model=` → `{job_id, items:[{candidate_id, full_name, application_id, status, applied_at, match}]}`; chỉ ứng viên đã nộp; không phải chủ tin → 403.
- `POST /resumes/upload` (multipart `file`, `consent`) → `{resume_id, skills:[{name, source, confidence}], years_exp, education_level, sections_found[]}` với `source` ∈ `dict | fuzzy | embedding`. Nguồn `embedding` là đề xuất độ tin cậy thấp: hiển thị khác biệt (ví dụ nhãn "gợi ý") và không tự tick. Lỗi: 400 `consent_required`, 413, 415, 422 (`no_text` hoặc `corrupt`).
- `POST /ai/extract-skills {text}` → `{skills:[{name, source, confidence}]}`.
- Model `m4` có thể trả **503 `model_not_trained`** cho tới khi huấn luyện xong: ô chọn model cần xử lý lỗi này (hiện thông báo, không vỡ trang) và mặc định là `m3`.
- `status` trong ranked-candidates là chuỗi tiếng Anh (`applied`…`rejected`), cần adapter sang nhãn tiếng Việt ở mục 3.3 của `00_`.
- Mọi lỗi theo FastAPI: `{"detail": "..."}` hoặc `{"detail": {...}}`.

## Việc cần làm (theo thứ tự)

### A. Hạ tầng API (31/10 chiều–tối, dùng mock)
1. `src/api/client.ts`: axios (`axios` thêm vào `dependencies`), `baseURL = import.meta.env.VITE_API_URL ?? '/api'`, interceptor gắn `Authorization: Bearer <token>` từ `localStorage['smartcareer_token']`; 401 → xoá token và điều hướng `/login`. Khai báo kiểu `ImportMetaEnv` cho `VITE_API_URL`, `VITE_OFFLINE_DEMO` trong `src/vite-env.d.ts`.
2. `src/api/adapters.ts` + `src/api/{auth,jobs,candidates,ai,applications,savedJobs,bi}.ts`: hàm gọi API trả đúng kiểu frontend (mục 3.2, 3.4). Thêm DTO types trong `src/api/dto.ts`. Adapter MatchDTO → `SkillMatchResult` đúng ánh xạ ở 00_ mục 3.4; thêm trường tùy chọn `semanticScore?`, `expScore?`, `eduScore?`, `explanation?`, `model?` vào `SkillMatchResult`.
3. `src/context/AuthContext.tsx` (user, role, login/logout/register) và `src/context/JobsContext.tsx` (`jobs`, `matchScores: Map<string, SkillMatchResult>`, trạng thái tải/lỗi). Offline: cấp `sampleJobs` + `getAllMatchScores` như cũ.
4. `src/pages/LoginPage.tsx`, `RegisterPage.tsx` (chọn vai trò ứng viên/nhà tuyển dụng, tên công ty nếu recruiter); `ProtectedRoute` chặn route theo vai trò trong `App.tsx` (`/employer/*` chỉ recruiter/admin; các trang ứng viên chỉ candidate). Ở offline: bỏ qua đăng nhập.

### B. Gỡ dữ liệu cứng và nối API (1–2/11; API AI sẵn sàng 18:00 2/11)
5. Sửa `src/utils/index.ts`: `countSuitableJobs`, `countJobsWithSkill`, `getAllMatchScores` nhận `jobs` làm tham số (thay vì đọc `sampleJobs`); cập nhật nơi gọi (`Sidebar`, `DashboardPage`, `JobsPage`, `SkillGapPage`…). `ETLPage`, `DFDPage`, `AboutPage` giữ nguyên dùng dữ liệu mẫu.
6. Các trang chuyển sang `useJobs()` / `JobsContext`: `DashboardPage`, `JobsPage` (lọc phía server, phân trang, hiện điểm khớp mỗi tin), `MatchPage` (6 thành phần + `explanation` + ô chọn model M0–M4 gọi `/ai/match`), `SkillGapPage` (`/candidates/me/skill-gap`), `ApplicationsPage`.
7. `useAppState`: thêm chế độ online (gọi `/saved-jobs`, `/applications`, `/candidates/me`) nhưng giữ cùng chữ ký trả về. Trạng thái đơn đổi sang 6 giá trị (mục 3.3): sửa `ApplicationStatus` trong `src/types/index.ts`, `ApplicationsPage.tsx` (`statusColors`, `allStatuses`, điều kiện "đang xử lý", màu select) và `EmployerPage.tsx`. Select chỉ liệt kê bước hợp lệ; khi backend trả 409 hiển thị thông báo, không im lặng.
8. Upload CV: `ProfilePage` + `components/profile/CvImport.tsx` gửi file tới `POST /resumes/upload` (kèm ô đồng ý `consent`), hiện màn xác nhận/sửa kỹ năng (giữ UX cũ), rồi `PUT /candidates/me/skills`. Xử lý lỗi 413/415/422 bằng thông báo tiếng Việt. Giữ `src/utils/cvParser.ts` chỉ dùng khi `VITE_OFFLINE_DEMO=true` (không chạy cùng lúc với API).
9. Mọi màn có 3 trạng thái tải / lỗi / rỗng: dùng `LoadingBlock.tsx` có sẵn, thêm `components/ui/ErrorBlock.tsx` (có nút thử lại) và `EmptyBlock.tsx`.

### C. Màn nhà tuyển dụng (1–4/11; guest token sẵn sàng 18:00 3/11)
10. **Đăng tin** `/employer/jobs/new`: form (tiêu đề, mô tả, cấp bậc, loại hình, địa điểm, lương, kinh nghiệm, danh mục `JobCategory`); nút "Gợi ý kỹ năng từ mô tả" → `POST /ai/extract-skills`; mỗi kỹ năng đánh dấu **bắt buộc/ưu tiên**; `POST /jobs`.
11. **Quản lý tin** `/employer/jobs`: danh sách tin của công ty, sửa/đóng tin.
12. **Ứng viên xếp hạng** `/employer/candidates`: chọn tin → `GET /jobs/{id}/ranked-candidates`; **Kanban 6 cột** theo 3.3 (kéo/thả hoặc nút chuyển) gọi `PATCH /applications/{id}/status`; hiện điểm + lý do khớp/thiếu kỹ năng. `/employer` cũ redirect sang trang này. Cập nhật mục trong `Sidebar.tsx`.
13. **Dashboard** `/employer/dashboard`: `GET /bi/guest-token` → `@superset-ui/embedded-sdk` (`embedDashboard({id, supersetDomain, mountPoint, fetchGuestToken})`); nếu lỗi/timeout → fallback Recharts với `/bi/skills|salary|funnel`. Tách thành chunk riêng trong `vite.config.ts` (`manualChunks`).
14. `DashboardPage` (Tổng quan) lấy KPI từ `/bi/summary` và "Việc làm phù hợp nhất" từ `/candidates/me/recommendations`.

### D. Chốt (4–5/11, chốt code 16:00 5/11)
15. Chế độ offline demo kiểm tra lại toàn bộ trang với `VITE_OFFLINE_DEMO=true`.
16. Dọn: không còn import `sampleJobs` ở trang chạy online (trừ ETL/DFD/About); không còn `console.log`; `npm run build` + `npm run lint` sạch.
17. Chụp ảnh màn hình các trang chính (`docs/report/figures/ui_*.png`) và viết chương "giao diện" của báo cáo (nộp markdown 12:00 6/11 cho Hoàng Anh).

## Đầu ra phải có
`src/api/*`, `src/context/*`, các trang mới (Login, Register, EmployerJobs, PostJob, EmployerCandidates, EmployerDashboard), trạng thái 6 giá trị, 3 trạng thái tải/lỗi/rỗng, chế độ offline demo, ảnh giao diện.

## Cách làm việc với tôi
- Sau mỗi cụm việc chạy `npm run build` và `npm run lint`; báo kết quả thật.
- Khi chạy online, dùng DevTools/`curl` kiểm tra request đi đúng đường dẫn mục 3.4; nếu response khác hợp đồng, **không sửa adapter cho khớp ngầm** – báo Tùng/Thái Anh.
- Cuối buổi in 3 dòng: đã xong / đang vướng / mai làm gì.
