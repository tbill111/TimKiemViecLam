"""Create BI views for candidate skills, salary trends, and AI labels."""
from __future__ import annotations

from alembic import op


revision = "0004_bi_views"
down_revision = "0003_labeling_tasks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE VIEW vw_candidate_skills AS
        SELECT
            s.id AS skill_id,
            s.name AS skill_name,
            COUNT(DISTINCT cs.candidate_id) AS candidate_count
        FROM skills AS s
        JOIN candidate_skills AS cs ON cs.skill_id = s.id
        JOIN candidates AS c ON c.id = cs.candidate_id
        GROUP BY s.id, s.name
        """
    )
    op.execute(
        """
        CREATE VIEW vw_salary_trends AS
        SELECT
            j.title,
            j.level,
            COUNT(*) FILTER (
                WHERE j.salary_min IS NOT NULL OR j.salary_max IS NOT NULL
            ) AS salary_posting_count,
            AVG(
                (COALESCE(j.salary_min, j.salary_max)
                 + COALESCE(j.salary_max, j.salary_min)) / 2.0
            ) AS average_salary
        FROM jobs AS j
        GROUP BY j.title, j.level
        """
    )
    op.execute(
        """
        CREATE VIEW vw_ai_matching_stats AS
        WITH buckets AS (
            SELECT bucket_order, score_bucket
            FROM (VALUES
                (1, 'Kém'),
                (2, 'Khá'),
                (3, 'Tốt')
            ) AS bucket_names(bucket_order, score_bucket)
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
            GROUP BY 1
        ),
        totals AS (
            SELECT COALESCE(SUM(pair_count), 0) AS total_count
            FROM scored
        )
        SELECT
            b.score_bucket,
            COALESCE(s.pair_count, 0) AS pair_count,
            COALESCE(
                ROUND(100.0 * COALESCE(s.pair_count, 0) / NULLIF(t.total_count, 0), 2),
                0
            ) AS percentage
        FROM buckets AS b
        LEFT JOIN scored AS s ON s.score_bucket = b.score_bucket
        CROSS JOIN totals AS t
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS vw_ai_matching_stats")
    op.execute("DROP VIEW IF EXISTS vw_salary_trends")
    op.execute("DROP VIEW IF EXISTS vw_candidate_skills")
