"""Cho phép lưu kết quả của mô hình M5 (Random Forest) và M6 (Gradient Boosting) trong match_results."""
from __future__ import annotations

from alembic import op


revision = "0007_match_models_m5_m6"
down_revision = "0006_fix_bi_views"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE match_results DROP CONSTRAINT IF EXISTS ck_match_results_model")
    op.execute("ALTER TABLE match_results ADD CONSTRAINT ck_match_results_model "
               "CHECK (model IN ('m0','m1','m2','m3','m4','m5','m6'))")


def downgrade() -> None:
    op.execute("DELETE FROM match_results WHERE model IN ('m5','m6')")
    op.execute("ALTER TABLE match_results DROP CONSTRAINT IF EXISTS ck_match_results_model")
    op.execute("ALTER TABLE match_results ADD CONSTRAINT ck_match_results_model "
               "CHECK (model IN ('m0','m1','m2','m3','m4'))")
