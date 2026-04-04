"""create prediction logs table

Revision ID: 20260403_0001
Revises:
Create Date: 2026-04-03 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260403_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "prediction_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("zone", sa.String(length=50), nullable=False),
        sa.Column("input_features", sa.JSON(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_category", sa.String(length=16), nullable=False),
        sa.Column("premium_multiplier", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(length=32), nullable=False),
        sa.Column("top_factors", sa.JSON(), nullable=False),
        sa.Column("actual_outcome", sa.Float(), nullable=True),
        sa.Column("corrected_label", sa.String(length=16), nullable=True),
        sa.Column("review_status", sa.String(length=16), server_default="pending", nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("corrected_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("risk_score >= 0 AND risk_score <= 1", name="ck_prediction_logs_risk_score_range"),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_prediction_logs_confidence_range"),
        sa.CheckConstraint("review_status IN ('pending','reviewed')", name="ck_prediction_logs_review_status"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_prediction_logs_review_status"), "prediction_logs", ["review_status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_prediction_logs_review_status"), table_name="prediction_logs")
    op.drop_table("prediction_logs")
