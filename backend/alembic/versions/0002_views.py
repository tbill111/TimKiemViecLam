"""Create the four BI views and grant read-only access to the BI role.

Revision ID: 0002_views
Revises: 0001_init
"""
from pathlib import Path
import os

from alembic import op
from sqlalchemy import text

revision = "0002_views"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def _statements():
    path = Path(__file__).resolve().parents[3] / "bi" / "views.sql"
    # Remove line comments before splitting: SQL comments may contain semicolons.
    sql = "\n".join(line for line in path.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("--"))
    return [statement.strip() for statement in sql.split(";") if statement.strip()]


def upgrade():
    password = os.getenv("BI_READER_PASSWORD", "smartcareer_bi_demo").replace("'", "''")
    op.execute(text(f"DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'bi_reader') THEN CREATE ROLE bi_reader LOGIN PASSWORD '{password}'; END IF; END $$"))
    for statement in _statements():
        op.execute(statement)
    op.execute("GRANT USAGE ON SCHEMA public TO bi_reader")
    for view in ("v_skill_supply_demand", "v_salary", "v_funnel", "v_funnel_stages"):
        op.execute(f"GRANT SELECT ON {view} TO bi_reader")


def downgrade():
    for view in ("v_funnel_stages", "v_funnel", "v_salary", "v_skill_supply_demand"):
        op.execute(f"DROP VIEW IF EXISTS {view}")
