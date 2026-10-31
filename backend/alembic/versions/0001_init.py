"""15 bảng của CSDL tác nghiệp

Revision ID: 0001
Revises:
"""
from alembic import op

from app import models  # noqa: F401
from app.db import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Schema được khai báo một nơi duy nhất ở app/models.py; migration tạo đúng schema đó.
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
