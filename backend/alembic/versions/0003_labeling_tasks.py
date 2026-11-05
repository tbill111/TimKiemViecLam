"""Persist AI labeling scores and reasons for resume/job pairs."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_labeling_tasks"
down_revision = "0002_views"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "labeling_tasks",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), autoincrement=True, nullable=False),
        sa.Column("resume_id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), nullable=False),
        sa.Column("job_id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), nullable=False),
        sa.Column("matching_score", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(length=20), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "matching_score IS NULL OR matching_score BETWEEN 0 AND 100",
            name="ck_labeling_tasks_matching_score",
        ),
        sa.CheckConstraint(
            "status IN ('pending','completed','failed')",
            name="ck_labeling_tasks_status",
        ),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resume_id", "job_id", name="uq_labeling_tasks_resume_job"),
    )
    op.create_index("ix_labeling_tasks_status", "labeling_tasks", ["status"])


def downgrade() -> None:
    op.drop_index("ix_labeling_tasks_status", table_name="labeling_tasks")
    op.drop_table("labeling_tasks")
