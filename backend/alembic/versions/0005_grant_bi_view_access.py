"""Grant the Superset read-only role access to the three dashboard views."""
from __future__ import annotations

from alembic import op


revision = "0005_grant_bi_view_access"
down_revision = "0004_bi_views"
branch_labels = None
depends_on = None


BI_VIEWS = (
    "vw_candidate_skills",
    "vw_salary_trends",
    "vw_ai_matching_stats",
)


def upgrade() -> None:
    op.execute("GRANT USAGE ON SCHEMA public TO bi_reader")
    for view in BI_VIEWS:
        op.execute(f"GRANT SELECT ON {view} TO bi_reader")


def downgrade() -> None:
    for view in BI_VIEWS:
        op.execute(f"REVOKE SELECT ON {view} FROM bi_reader")
