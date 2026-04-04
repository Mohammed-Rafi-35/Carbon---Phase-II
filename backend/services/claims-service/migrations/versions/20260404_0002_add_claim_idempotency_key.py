"""add idempotency key to claims

Revision ID: 20260404_0002
Revises: 20260403_0001
Create Date: 2026-04-04 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260404_0002"
down_revision = "20260403_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("claims", sa.Column("idempotency_key", sa.String(length=128), nullable=True))
    op.create_index(op.f("ix_claims_idempotency_key"), "claims", ["idempotency_key"], unique=False)
    op.create_unique_constraint("uq_claims_idempotency_key", "claims", ["idempotency_key"])


def downgrade() -> None:
    op.drop_constraint("uq_claims_idempotency_key", "claims", type_="unique")
    op.drop_index(op.f("ix_claims_idempotency_key"), table_name="claims")
    op.drop_column("claims", "idempotency_key")
