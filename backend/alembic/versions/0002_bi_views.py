"""View BI cho Superset và quyền đọc cho role bi_reader (chỉ chạy trên PostgreSQL)

Revision ID: 0002
Revises: 0001
"""
from alembic import op

from app.bi_sql import apply_views, drop_views

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    apply_views(op.get_bind())  # SQLite (test) không có bool_or/FILTER: bỏ qua; backend dùng truy vấn ORM tương đương


def downgrade() -> None:
    drop_views(op.get_bind())
