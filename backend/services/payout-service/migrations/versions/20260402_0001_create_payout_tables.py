"""create payout and ledger tables

Revision ID: 20260402_0001
Revises:
Create Date: 2026-04-02 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260402_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payouts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("claim_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("transaction_ref", sa.String(length=120), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("claim_id", name="uq_payouts_claim_id"),
        sa.UniqueConstraint("idempotency_key", name="uq_payouts_idempotency_key"),
    )
    op.create_index(op.f("ix_payouts_claim_id"), "payouts", ["claim_id"], unique=False)
    op.create_index(op.f("ix_payouts_user_id"), "payouts", ["user_id"], unique=False)
    op.create_index(op.f("ix_payouts_status"), "payouts", ["status"], unique=False)
    op.create_index(op.f("ix_payouts_idempotency_key"), "payouts", ["idempotency_key"], unique=False)

    op.create_table(
        "ledger",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("transaction_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("balance", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["transaction_id"], ["payouts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transaction_id"),
    )
    op.create_index(op.f("ix_ledger_user_id"), "ledger", ["user_id"], unique=False)
    op.create_index(op.f("ix_ledger_transaction_id"), "ledger", ["transaction_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ledger_transaction_id"), table_name="ledger")
    op.drop_index(op.f("ix_ledger_user_id"), table_name="ledger")
    op.drop_table("ledger")

    op.drop_index(op.f("ix_payouts_idempotency_key"), table_name="payouts")
    op.drop_index(op.f("ix_payouts_status"), table_name="payouts")
    op.drop_index(op.f("ix_payouts_user_id"), table_name="payouts")
    op.drop_index(op.f("ix_payouts_claim_id"), table_name="payouts")
    op.drop_table("payouts")
