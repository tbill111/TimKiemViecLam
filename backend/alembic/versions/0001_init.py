"""Create the 15-table SmartCareer schema.

Revision ID: 0001_init
Revises:
"""
from alembic import op

from app.db import Base
from app import models  # noqa: F401

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


# Bảng do các migration SAU tạo ra. 0001 dùng create_all trên metadata *hiện tại* của models, nên phải loại các bảng này;
# nếu không, `alembic upgrade head` trên PostgreSQL trống sẽ lỗi DuplicateTable khi migration sau tạo lại bảng đó.
LATER_TABLES = {"labeling_tasks"}


def _tables():
    return [table for table in Base.metadata.sorted_tables if table.name not in LATER_TABLES]


def upgrade():
    Base.metadata.create_all(bind=op.get_bind(), tables=_tables())


def downgrade():
    Base.metadata.drop_all(bind=op.get_bind(), tables=_tables())
