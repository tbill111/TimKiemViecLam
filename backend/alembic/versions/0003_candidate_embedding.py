"""Thêm candidates.embedding (embedding hồ sơ tính sẵn khi lưu)

Revision ID: 0003
Revises: 0002
"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Cài mới: 0001 (create_all theo models hiện tại) đã có cột này; chỉ thêm khi nâng cấp CSDL cũ.
    cols = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("candidates")}
    if "embedding" not in cols:
        op.add_column("candidates", sa.Column("embedding", sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    cols = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("candidates")}
    if "embedding" in cols:
        op.drop_column("candidates", "embedding")
