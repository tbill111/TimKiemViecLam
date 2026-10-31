-- SmartCareer v2: CSDL tác nghiệp (PostgreSQL 16). Sinh tự động từ app/models.py bằng scripts/dump_schema.py.

CREATE TABLE locations (
	id SERIAL NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	region VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE skills (
	id SERIAL NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	category VARCHAR(50) NOT NULL, 
	learning_steps JSONB, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE users (
	id SERIAL NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	full_name VARCHAR(255) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_users_role CHECK (role IN ('candidate', 'recruiter', 'admin')), 
	UNIQUE (email)
);

CREATE TABLE candidates (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	external_id VARCHAR(50), 
	full_name VARCHAR(255) NOT NULL, 
	phone VARCHAR(50) NOT NULL, 
	location_id INTEGER, 
	years_exp NUMERIC(3, 1) NOT NULL, 
	education_level INTEGER NOT NULL, 
	major VARCHAR(255) NOT NULL, 
	expected_salary_min NUMERIC(6, 1), 
	expected_salary_max NUMERIC(6, 1), 
	work_mode VARCHAR(20) NOT NULL, 
	consent_at TIMESTAMP WITHOUT TIME ZONE, 
	profile_json JSONB NOT NULL, 
	embedding BYTEA, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	UNIQUE (external_id), 
	FOREIGN KEY(location_id) REFERENCES locations (id)
);

CREATE TABLE companies (
	id SERIAL NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	industry VARCHAR(100) NOT NULL, 
	size_range VARCHAR(50) NOT NULL, 
	location_id INTEGER, 
	verified BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	FOREIGN KEY(location_id) REFERENCES locations (id)
);

CREATE TABLE skill_aliases (
	alias VARCHAR(100) NOT NULL, 
	skill_id INTEGER NOT NULL, 
	PRIMARY KEY (alias), 
	FOREIGN KEY(skill_id) REFERENCES skills (id) ON DELETE CASCADE
);

CREATE TABLE candidate_skills (
	candidate_id INTEGER NOT NULL, 
	skill_id INTEGER NOT NULL, 
	source VARCHAR(10) NOT NULL, 
	confirmed BOOLEAN NOT NULL, 
	PRIMARY KEY (candidate_id, skill_id), 
	CONSTRAINT ck_candidate_skills_source CHECK (source IN ('cv', 'manual')), 
	FOREIGN KEY(candidate_id) REFERENCES candidates (id) ON DELETE CASCADE, 
	FOREIGN KEY(skill_id) REFERENCES skills (id) ON DELETE CASCADE
);

CREATE TABLE recruiters (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	company_id INTEGER NOT NULL, 
	position VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(company_id) REFERENCES companies (id)
);

CREATE TABLE resumes (
	id SERIAL NOT NULL, 
	candidate_id INTEGER NOT NULL, 
	filename VARCHAR(255) NOT NULL, 
	file_path VARCHAR(500) NOT NULL, 
	raw_text TEXT NOT NULL, 
	parsed_json JSONB NOT NULL, 
	embedding BYTEA, 
	is_active BOOLEAN NOT NULL, 
	uploaded_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(candidate_id) REFERENCES candidates (id) ON DELETE CASCADE
);

CREATE TABLE jobs (
	id SERIAL NOT NULL, 
	external_id VARCHAR(50), 
	company_id INTEGER NOT NULL, 
	recruiter_id INTEGER, 
	title VARCHAR(255) NOT NULL, 
	description TEXT NOT NULL, 
	responsibilities JSONB NOT NULL, 
	category VARCHAR(60) NOT NULL, 
	level VARCHAR(20) NOT NULL, 
	job_type VARCHAR(20) NOT NULL, 
	work_mode VARCHAR(20) NOT NULL, 
	location_id INTEGER, 
	salary_min NUMERIC(6, 1), 
	salary_max NUMERIC(6, 1), 
	min_years_exp NUMERIC(3, 1) NOT NULL, 
	min_education INTEGER NOT NULL, 
	status VARCHAR(10) NOT NULL, 
	posted_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	deadline TIMESTAMP WITHOUT TIME ZONE, 
	embedding BYTEA, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_jobs_level CHECK (level IN ('intern', 'fresher', 'junior', 'middle', 'senior')), 
	CONSTRAINT ck_jobs_job_type CHECK (job_type IN ('full_time', 'part_time', 'internship')), 
	CONSTRAINT ck_jobs_work_mode CHECK (work_mode IN ('onsite', 'hybrid', 'remote')), 
	CONSTRAINT ck_jobs_status CHECK (status IN ('open', 'closed')), 
	CONSTRAINT ck_jobs_salary CHECK (salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max), 
	UNIQUE (external_id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	FOREIGN KEY(recruiter_id) REFERENCES recruiters (id), 
	FOREIGN KEY(location_id) REFERENCES locations (id)
);
CREATE INDEX ix_jobs_company_id ON jobs (company_id);
CREATE INDEX ix_jobs_status ON jobs (status);

CREATE TABLE applications (
	id SERIAL NOT NULL, 
	candidate_id INTEGER NOT NULL, 
	job_id INTEGER NOT NULL, 
	resume_id INTEGER, 
	match_score INTEGER, 
	status VARCHAR(15) NOT NULL, 
	applied_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_applications_candidate_job UNIQUE (candidate_id, job_id), 
	CONSTRAINT ck_applications_status CHECK (status IN ('applied', 'screening', 'interview', 'offer', 'hired', 'rejected')), 
	FOREIGN KEY(candidate_id) REFERENCES candidates (id) ON DELETE CASCADE, 
	FOREIGN KEY(job_id) REFERENCES jobs (id) ON DELETE CASCADE, 
	FOREIGN KEY(resume_id) REFERENCES resumes (id) ON DELETE SET NULL
);
CREATE INDEX ix_applications_job_id ON applications (job_id);

CREATE TABLE job_skills (
	job_id INTEGER NOT NULL, 
	skill_id INTEGER NOT NULL, 
	is_required BOOLEAN NOT NULL, 
	PRIMARY KEY (job_id, skill_id), 
	FOREIGN KEY(job_id) REFERENCES jobs (id) ON DELETE CASCADE, 
	FOREIGN KEY(skill_id) REFERENCES skills (id) ON DELETE CASCADE
);
CREATE INDEX ix_job_skills_skill_id ON job_skills (skill_id);

CREATE TABLE match_results (
	candidate_id INTEGER NOT NULL, 
	job_id INTEGER NOT NULL, 
	model_version VARCHAR(60) NOT NULL, 
	total_score INTEGER NOT NULL, 
	skill_req_score INTEGER, 
	skill_pref_score INTEGER, 
	semantic_score INTEGER, 
	exp_score INTEGER, 
	edu_score INTEGER, 
	location_score INTEGER, 
	matched_skills JSONB NOT NULL, 
	missing_skills JSONB NOT NULL, 
	computed_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (candidate_id, job_id, model_version), 
	FOREIGN KEY(candidate_id) REFERENCES candidates (id) ON DELETE CASCADE, 
	FOREIGN KEY(job_id) REFERENCES jobs (id) ON DELETE CASCADE
);

CREATE TABLE saved_jobs (
	candidate_id INTEGER NOT NULL, 
	job_id INTEGER NOT NULL, 
	saved_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (candidate_id, job_id), 
	FOREIGN KEY(candidate_id) REFERENCES candidates (id) ON DELETE CASCADE, 
	FOREIGN KEY(job_id) REFERENCES jobs (id) ON DELETE CASCADE
);

CREATE TABLE application_status_history (
	id SERIAL NOT NULL, 
	application_id INTEGER NOT NULL, 
	from_status VARCHAR(15), 
	to_status VARCHAR(15) NOT NULL, 
	changed_by INTEGER, 
	changed_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	note TEXT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(application_id) REFERENCES applications (id) ON DELETE CASCADE, 
	FOREIGN KEY(changed_by) REFERENCES users (id)
);
CREATE INDEX ix_application_status_history_application_id ON application_status_history (application_id);

-- ===== View BI (bi/views.sql) =====

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
