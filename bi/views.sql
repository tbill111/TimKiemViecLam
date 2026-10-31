-- Ba view cho dashboard BI (PostgreSQL). Superset chỉ đọc các view này qua role bi_reader.
-- Định nghĩa chỉ số khớp với backend/app/routers/bi.py (phương án dự phòng Recharts đọc cùng số liệu).

-- 1) Số ứng viên theo kỹ năng, cầu kỹ năng và chỉ số thiếu hụt (> 1 nghĩa là thiếu người)
CREATE OR REPLACE VIEW v_skill_supply_demand AS
SELECT
    s.id AS skill_id,
    s.name AS skill,
    s.category,
    COUNT(DISTINCT cs.candidate_id) FILTER (WHERE cs.confirmed) AS so_ung_vien,
    COUNT(DISTINCT js.job_id) FILTER (WHERE j.status = 'open') AS so_tin_yeu_cau,
    ROUND(
        (COUNT(DISTINCT js.job_id) FILTER (WHERE j.status = 'open'))::numeric
        / NULLIF(COUNT(DISTINCT cs.candidate_id) FILTER (WHERE cs.confirmed), 0),
        3
    ) AS thieu_hut
FROM skills s
LEFT JOIN candidate_skills cs ON cs.skill_id = s.id
LEFT JOIN job_skills js ON js.skill_id = s.id
LEFT JOIN jobs j ON j.id = js.job_id
GROUP BY s.id, s.name, s.category;

-- 2) Lương trung bình của tin theo tháng đăng, cấp bậc, địa điểm (triệu VNĐ/tháng); bỏ tin thoả thuận (lương NULL)
CREATE OR REPLACE VIEW v_salary AS
SELECT
    j.id AS job_id,
    date_trunc('month', j.posted_at)::date AS thang,
    j.level,
    j.category,
    l.name AS dia_diem,
    c.industry,
    (j.salary_min + j.salary_max) / 2.0 AS luong_tb
FROM jobs j
JOIN companies c ON c.id = j.company_id
LEFT JOIN locations l ON l.id = j.location_id
WHERE j.salary_min IS NOT NULL AND j.salary_max IS NOT NULL;

-- 3) Phễu tuyển dụng: mỗi hồ sơ một dòng, cờ "từng đạt" từng bước tính từ LỊCH SỬ trạng thái
--    (đếm theo trạng thái hiện tại sẽ làm phễu sai: hồ sơ đã hired không còn được đếm ở bước interview).
CREATE OR REPLACE VIEW v_funnel AS
SELECT
    a.id AS application_id,
    a.job_id,
    j.company_id,
    j.category,
    j.level,
    a.match_score,
    CASE
        WHEN a.match_score IS NULL THEN NULL
        WHEN a.match_score < 40 THEN '0-40'
        WHEN a.match_score < 60 THEN '40-60'
        WHEN a.match_score < 80 THEN '60-80'
        ELSE '80-100'
    END AS nhom_diem,
    date_trunc('month', a.applied_at)::date AS thang_nop,
    a.applied_at,
    a.status AS trang_thai_hien_tai,
    TRUE AS applied,
    COALESCE(bool_or(h.to_status IN ('screening', 'interview', 'offer', 'hired')), FALSE) AS screening,
    COALESCE(bool_or(h.to_status IN ('interview', 'offer', 'hired')), FALSE) AS interview,
    COALESCE(bool_or(h.to_status IN ('offer', 'hired')), FALSE) AS offer,
    COALESCE(bool_or(h.to_status = 'hired'), FALSE) AS hired,
    EXTRACT(EPOCH FROM (MAX(h.changed_at) FILTER (WHERE h.to_status = 'hired') - a.applied_at)) / 86400.0 AS ngay_den_khi_tuyen
FROM applications a
JOIN jobs j ON j.id = a.job_id
LEFT JOIN application_status_history h ON h.application_id = a.id
GROUP BY a.id, a.job_id, j.company_id, j.category, j.level, a.match_score, a.applied_at, a.status;

-- 3b) Dạng "dài" của phễu để vẽ Funnel Chart trực tiếp (giai đoạn x số hồ sơ), vẫn có company_id cho RLS
CREATE OR REPLACE VIEW v_funnel_stages AS
SELECT company_id, category, level, thang_nop, nhom_diem, 1 AS buoc, '1. Ứng tuyển' AS giai_doan,
       COUNT(*) FILTER (WHERE applied) AS so_ho_so
FROM v_funnel GROUP BY company_id, category, level, thang_nop, nhom_diem
UNION ALL
SELECT company_id, category, level, thang_nop, nhom_diem, 2, '2. Sàng lọc', COUNT(*) FILTER (WHERE screening)
FROM v_funnel GROUP BY company_id, category, level, thang_nop, nhom_diem
UNION ALL
SELECT company_id, category, level, thang_nop, nhom_diem, 3, '3. Phỏng vấn', COUNT(*) FILTER (WHERE interview)
FROM v_funnel GROUP BY company_id, category, level, thang_nop, nhom_diem
UNION ALL
SELECT company_id, category, level, thang_nop, nhom_diem, 4, '4. Đề nghị', COUNT(*) FILTER (WHERE offer)
FROM v_funnel GROUP BY company_id, category, level, thang_nop, nhom_diem
UNION ALL
SELECT company_id, category, level, thang_nop, nhom_diem, 5, '5. Tuyển dụng', COUNT(*) FILTER (WHERE hired)
FROM v_funnel GROUP BY company_id, category, level, thang_nop, nhom_diem;
