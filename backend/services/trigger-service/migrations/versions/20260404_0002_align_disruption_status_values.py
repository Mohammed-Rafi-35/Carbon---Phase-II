"""align disruption status values with runtime

Revision ID: 20260404_0002
Revises: 20260403_0001
Create Date: 2026-04-04 00:00:00
"""

from __future__ import annotations

from alembic import op


revision = "20260404_0002"
down_revision = "20260403_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("disruptions") as batch_op:
        batch_op.drop_constraint("ck_disruptions_status", type_="check")
        batch_op.create_check_constraint(
            "ck_disruptions_status",
            "status IN ('active','stopped')",
        )


def downgrade() -> None:
    with op.batch_alter_table("disruptions") as batch_op:
        batch_op.drop_constraint("ck_disruptions_status", type_="check")
        batch_op.create_check_constraint(
            "ck_disruptions_status",
            "status IN ('active','resolved')",
        )
