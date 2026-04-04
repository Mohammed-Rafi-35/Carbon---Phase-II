"""create claims and claim_logs tables

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
        "claims",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("policy_id", sa.Uuid(), nullable=True),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("risk_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("fraud_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("payout_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("rejection_reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "event_id", name="uq_claims_user_event"),
    )
    op.create_index(op.f("ix_claims_user_id"), "claims", ["user_id"], unique=False)
    op.create_index(op.f("ix_claims_policy_id"), "claims", ["policy_id"], unique=False)
    op.create_index(op.f("ix_claims_event_id"), "claims", ["event_id"], unique=False)
    op.create_index(op.f("ix_claims_status"), "claims", ["status"], unique=False)

    op.create_table(
        "claim_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("claim_id", sa.Uuid(), nullable=False),
        sa.Column("stage", sa.String(length=30), nullable=False),
        sa.Column("message", sa.String(length=255), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_claim_logs_claim_id"), "claim_logs", ["claim_id"], unique=False)
    op.create_index(op.f("ix_claim_logs_stage"), "claim_logs", ["stage"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_claim_logs_stage"), table_name="claim_logs")
    op.drop_index(op.f("ix_claim_logs_claim_id"), table_name="claim_logs")
    op.drop_table("claim_logs")

    op.drop_index(op.f("ix_claims_status"), table_name="claims")
    op.drop_index(op.f("ix_claims_event_id"), table_name="claims")
    op.drop_index(op.f("ix_claims_policy_id"), table_name="claims")
    op.drop_index(op.f("ix_claims_user_id"), table_name="claims")
    op.drop_table("claims")
