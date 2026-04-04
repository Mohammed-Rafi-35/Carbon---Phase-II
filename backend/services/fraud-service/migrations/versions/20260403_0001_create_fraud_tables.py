"""create fraud tables

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
        "fraud_checks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("claim_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("fraud_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=12), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False, server_default="api"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('PASS','FAIL')", name="ck_fraud_checks_status"),
        sa.CheckConstraint("fraud_score >= 0 AND fraud_score <= 1", name="ck_fraud_checks_score_range"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_fraud_checks_claim_id"), "fraud_checks", ["claim_id"], unique=False)
    op.create_index(op.f("ix_fraud_checks_user_id"), "fraud_checks", ["user_id"], unique=False)
    op.create_index(op.f("ix_fraud_checks_status"), "fraud_checks", ["status"], unique=False)

    op.create_table(
        "fraud_audit_trail",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("claim_id", sa.Uuid(), nullable=False),
        sa.Column("actor", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("decision_status", sa.String(length=12), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_fraud_audit_trail_claim_id"), "fraud_audit_trail", ["claim_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_fraud_audit_trail_claim_id"), table_name="fraud_audit_trail")
    op.drop_table("fraud_audit_trail")

    op.drop_index(op.f("ix_fraud_checks_status"), table_name="fraud_checks")
    op.drop_index(op.f("ix_fraud_checks_user_id"), table_name="fraud_checks")
    op.drop_index(op.f("ix_fraud_checks_claim_id"), table_name="fraud_checks")
    op.drop_table("fraud_checks")
