"""create policy and policy log tables

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
        "policies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("zone", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("insured_weekly_income", sa.Numeric(12, 2), nullable=False),
        sa.Column("insured_daily_income", sa.Numeric(12, 2), nullable=False),
        sa.Column("coverage_rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("base_premium", sa.Numeric(12, 2), nullable=False),
        sa.Column("gst", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_premium", sa.Numeric(12, 2), nullable=False),
        sa.Column("stabilization_factor", sa.Numeric(5, 2), nullable=False),
        sa.Column("waiting_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activity_days", sa.Integer(), nullable=False),
        sa.Column("premium_paid", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_policies_user_id"), "policies", ["user_id"], unique=False)
    op.create_index(op.f("ix_policies_status"), "policies", ["status"], unique=False)

    op.create_table(
        "policy_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("policy_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["policy_id"], ["policies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_policy_logs_timestamp"), "policy_logs", ["timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_policy_logs_timestamp"), table_name="policy_logs")
    op.drop_table("policy_logs")
    op.drop_index(op.f("ix_policies_status"), table_name="policies")
    op.drop_index(op.f("ix_policies_user_id"), table_name="policies")
    op.drop_table("policies")
