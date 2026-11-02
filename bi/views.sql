CREATE OR REPLACE VIEW v_skill_supply_demand AS
SELECT
    s.id AS skill_id,
    s.name AS skill_name,
    s.category,
    COALESCE(supply.candidate_count, 0)::BIGINT AS candidate_count,
    COALESCE(demand.open_job_count, 0)::BIGINT AS open_job_count
FROM skills s
LEFT JOIN (
    SELECT cs.skill_id, COUNT(DISTINCT cs.candidate_id) AS candidate_count
    FROM candidate_skills cs
    JOIN candidates c ON c.id = cs.candidate_id
    WHERE cs.confirmed = TRUE
    GROUP BY cs.skill_id
) supply ON supply.skill_id = s.id
LEFT JOIN (
    SELECT js.skill_id, COUNT(DISTINCT j.id) AS open_job_count
    FROM job_skills js
    JOIN jobs j ON j.id = js.job_id AND j.status = 'open'
    GROUP BY js.skill_id
) demand ON demand.skill_id = s.id
WHERE s.is_active = TRUE;

CREATE OR REPLACE VIEW v_salary AS
SELECT
    COALESCE(l.name, 'Không xác định') AS location,
    j.category,
    j.level,
    DATE_TRUNC('month', j.posted_at)::DATE AS posted_month,
    COUNT(*)::BIGINT AS job_count,
    AVG(j.salary_min)::NUMERIC(10,2) AS average_salary_min,
    AVG(j.salary_max)::NUMERIC(10,2) AS average_salary_max,
    MIN(j.salary_min)::NUMERIC(10,2) AS minimum_salary,
    MAX(j.salary_max)::NUMERIC(10,2) AS maximum_salary
FROM jobs j
LEFT JOIN locations l ON l.id = j.location_id
WHERE j.status = 'open'
GROUP BY COALESCE(l.name, 'Không xác định'), j.category, j.level, DATE_TRUNC('month', j.posted_at)::DATE;

CREATE OR REPLACE VIEW v_funnel AS
SELECT
    j.company_id,
    COUNT(DISTINCT CASE WHEN h.to_status = 'applied' THEN a.id END)::BIGINT AS applied,
    COUNT(DISTINCT CASE WHEN h.to_status = 'screening' THEN a.id END)::BIGINT AS screening,
    COUNT(DISTINCT CASE WHEN h.to_status = 'interview' THEN a.id END)::BIGINT AS interview,
    COUNT(DISTINCT CASE WHEN h.to_status = 'offer' THEN a.id END)::BIGINT AS offer,
    COUNT(DISTINCT CASE WHEN h.to_status = 'hired' THEN a.id END)::BIGINT AS hired,
    COUNT(DISTINCT CASE WHEN h.to_status = 'rejected' THEN a.id END)::BIGINT AS rejected,
    COUNT(DISTINCT a.id)::BIGINT AS total_applications
FROM jobs j
LEFT JOIN applications a ON a.job_id = j.id
LEFT JOIN application_status_history h ON h.application_id = a.id
GROUP BY j.company_id;

CREATE OR REPLACE VIEW v_funnel_stages AS
WITH stages(stage, stage_order) AS (
    VALUES ('applied', 1), ('screening', 2), ('interview', 3), ('offer', 4), ('hired', 5), ('rejected', 6)
), counts AS (
    SELECT j.company_id, h.to_status AS stage, COUNT(DISTINCT a.id)::BIGINT AS applications
    FROM jobs j
    JOIN applications a ON a.job_id = j.id
    JOIN application_status_history h ON h.application_id = a.id
    GROUP BY j.company_id, h.to_status
)
SELECT j.company_id, stages.stage, stages.stage_order,
       COALESCE(counts.applications, 0)::BIGINT AS applications,
       CASE WHEN stages.stage_order = 1 THEN 100.0
            WHEN stages.stage = 'rejected' THEN ROUND(100.0 * COALESCE(counts.applications, 0) / NULLIF(FIRST_VALUE(counts.applications) OVER (PARTITION BY j.company_id ORDER BY stages.stage_order), 0), 2)
            WHEN LAG(COALESCE(counts.applications, 0)) OVER (PARTITION BY j.company_id ORDER BY stages.stage_order) = 0 THEN 0.0
            ELSE ROUND(100.0 * counts.applications / LAG(counts.applications) OVER (PARTITION BY j.company_id ORDER BY stages.stage_order), 2)
       END AS conversion_rate
FROM (SELECT DISTINCT company_id FROM jobs) j
CROSS JOIN stages
LEFT JOIN counts ON counts.company_id = j.company_id AND counts.stage = stages.stage;
