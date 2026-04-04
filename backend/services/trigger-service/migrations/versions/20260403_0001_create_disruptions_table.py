"""create disruptions table

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
        "disruptions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("zone", sa.String(length=128), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("severity IN ('LOW','MEDIUM','HIGH')", name="ck_disruptions_severity"),
        sa.CheckConstraint("status IN ('active','resolved')", name="ck_disruptions_status"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_disruptions_zone"), "disruptions", ["zone"], unique=False)
    op.create_index(op.f("ix_disruptions_type"), "disruptions", ["type"], unique=False)
    op.create_index(op.f("ix_disruptions_status"), "disruptions", ["status"], unique=False)
    op.create_index("ix_disruptions_zone_type_status", "disruptions", ["zone", "type", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_disruptions_zone_type_status", table_name="disruptions")
    op.drop_index(op.f("ix_disruptions_status"), table_name="disruptions")
    op.drop_index(op.f("ix_disruptions_type"), table_name="disruptions")
    op.drop_index(op.f("ix_disruptions_zone"), table_name="disruptions")
    op.drop_table("disruptions")
