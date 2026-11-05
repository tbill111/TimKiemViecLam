"""Sửa các view BI: nhất quán với view cũ, có chiều thời gian, loại điểm mock."""
from __future__ import annotations

from alembic import op


revision = "0006_fix_bi_views"
down_revision = "0005_grant_bi_view_access"
branch_labels = None
depends_on = None

BI_VIEWS = ("vw_candidate_skills", "vw_salary_trends", "vw_ai_matching_stats")


def upgrade() -> None:
    for view in BI_VIEWS:
        op.execute(f"DROP VIEW IF EXISTS {view}")
    # Cùng quy ước với v_skill_supply_demand: chỉ kỹ năng đang dùng và đã xác nhận; có cả phía cầu.
    op.execute(
        """
        CREATE VIEW vw_candidate_skills AS
        SELECT
            s.id AS skill_id,
            s.name AS skill_name,
            s.category,
            COALESCE(supply.candidate_count, 0)::BIGINT AS candidate_count,
            COALESCE(demand.open_job_count, 0)::BIGINT AS open_job_count
        FROM skills AS s
        LEFT JOIN (
            SELECT skill_id, COUNT(DISTINCT candidate_id) AS candidate_count
            FROM candidate_skills
            WHERE confirmed = TRUE
            GROUP BY skill_id
        ) AS supply ON supply.skill_id = s.id
        LEFT JOIN (
            SELECT js.skill_id, COUNT(DISTINCT j.id) AS open_job_count
            FROM job_skills AS js
            JOIN jobs AS j ON j.id = js.job_id AND j.status = 'open'
            GROUP BY js.skill_id
        ) AS demand ON demand.skill_id = s.id
        WHERE s.is_active = TRUE
        """
    )
    # Lương theo tháng đăng (triệu VNĐ/tháng) để vẽ xu hướng.
    op.execute(
        """
        CREATE VIEW vw_salary_trends AS
        SELECT
            j.title,
            j.level,
            DATE_TRUNC('month', j.posted_at)::DATE AS posted_month,
            COUNT(*) AS salary_posting_count,
            AVG((COALESCE(j.salary_min, j.salary_max) + COALESCE(j.salary_max, j.salary_min)) / 2.0)
                AS average_salary
        FROM jobs AS j
        WHERE j.salary_min IS NOT NULL OR j.salary_max IS NOT NULL
        GROUP BY j.title, j.level, DATE_TRUNC('month', j.posted_at)
        """
    )
    # Bỏ nhãn mock (điểm ngẫu nhiên) khỏi thống kê.
    op.execute(
        """
        CREATE VIEW vw_ai_matching_stats AS
        WITH buckets AS (
            SELECT bucket_order, score_bucket
            FROM (VALUES (1, 'Kém'), (2, 'Khá'), (3, 'Tốt')) AS b(bucket_order, score_bucket)
        ),
        scored AS (
            SELECT
                CASE
                    WHEN matching_score < 50 THEN 'Kém'
                    WHEN matching_score <= 75 THEN 'Khá'
                    ELSE 'Tốt'
                END AS score_bucket,
                COUNT(*) AS pair_count
            FROM labeling_tasks
            WHERE status = 'completed'
              AND matching_score IS NOT NULL
              AND COALESCE(provider, '') <> 'mock'
            GROUP BY 1
        ),
        totals AS (SELECT COALESCE(SUM(pair_count), 0) AS total_count FROM scored)
        SELECT
            b.score_bucket,
            COALESCE(s.pair_count, 0) AS pair_count,
            COALESCE(ROUND(100.0 * COALESCE(s.pair_count, 0) / NULLIF(t.total_count, 0), 2), 0) AS percentage
        FROM buckets AS b
        LEFT JOIN scored AS s ON s.score_bucket = b.score_bucket
        CROSS JOIN totals AS t
        """
    )
    for view in BI_VIEWS:
        op.execute(f"GRANT SELECT ON {view} TO bi_reader")


def downgrade() -> None:
    # Khôi phục dạng tối thiểu để 0005/0004 downgrade tiếp tục chạy được.
    for view in BI_VIEWS:
        op.execute(f"DROP VIEW IF EXISTS {view}")
    op.execute("CREATE VIEW vw_candidate_skills AS SELECT s.id AS skill_id, s.name AS skill_name, "
               "COUNT(DISTINCT cs.candidate_id) AS candidate_count FROM skills s "
               "JOIN candidate_skills cs ON cs.skill_id = s.id GROUP BY s.id, s.name")
    op.execute("CREATE VIEW vw_salary_trends AS SELECT j.title, j.level, "
               "COUNT(*) FILTER (WHERE j.salary_min IS NOT NULL OR j.salary_max IS NOT NULL) AS salary_posting_count, "
               "AVG((COALESCE(j.salary_min, j.salary_max) + COALESCE(j.salary_max, j.salary_min)) / 2.0) AS average_salary "
               "FROM jobs j GROUP BY j.title, j.level")
    op.execute("CREATE VIEW vw_ai_matching_stats AS SELECT 'Kém'::text AS score_bucket, 0::bigint AS pair_count, 0::numeric AS percentage")
    for view in BI_VIEWS:
        op.execute(f"GRANT SELECT ON {view} TO bi_reader")
