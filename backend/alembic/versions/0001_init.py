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


def upgrade():
    Base.metadata.create_all(bind=op.get_bind())


def downgrade():
    Base.metadata.drop_all(bind=op.get_bind())
