"""create analytics tables

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
        "analytics_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_key", sa.String(length=128), nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("routing_key", sa.String(length=128), nullable=True),
        sa.Column("zone", sa.String(length=64), nullable=True),
        sa.Column("user_id", sa.String(length=64), nullable=True),
        sa.Column("amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=True),
        sa.Column("risk_category", sa.String(length=16), nullable=True),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_key", name="uq_analytics_events_event_key"),
    )
    op.create_index(op.f("ix_analytics_events_event_key"), "analytics_events", ["event_key"], unique=True)
    op.create_index(op.f("ix_analytics_events_event_id"), "analytics_events", ["event_id"], unique=False)
    op.create_index(op.f("ix_analytics_events_event_type"), "analytics_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_analytics_events_routing_key"), "analytics_events", ["routing_key"], unique=False)
    op.create_index(op.f("ix_analytics_events_zone"), "analytics_events", ["zone"], unique=False)
    op.create_index(op.f("ix_analytics_events_user_id"), "analytics_events", ["user_id"], unique=False)
    op.create_index(op.f("ix_analytics_events_risk_category"), "analytics_events", ["risk_category"], unique=False)
    op.create_index(op.f("ix_analytics_events_event_timestamp"), "analytics_events", ["event_timestamp"], unique=False)
    op.create_index("ix_analytics_events_type_time", "analytics_events", ["event_type", "event_timestamp"], unique=False)
    op.create_index("ix_analytics_events_zone_time", "analytics_events", ["zone", "event_timestamp"], unique=False)

    op.create_table(
        "analytics_metrics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("metric_type", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Numeric(14, 4), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("zone", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analytics_metrics_metric_type"), "analytics_metrics", ["metric_type"], unique=False)
    op.create_index(op.f("ix_analytics_metrics_timestamp"), "analytics_metrics", ["timestamp"], unique=False)
    op.create_index(op.f("ix_analytics_metrics_zone"), "analytics_metrics", ["zone"], unique=False)
    op.create_index(
        "ix_analytics_metrics_type_time_zone",
        "analytics_metrics",
        ["metric_type", "timestamp", "zone"],
        unique=False,
    )

    op.create_table(
        "aggregated_stats",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("metric_name", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Numeric(14, 4), nullable=False),
        sa.Column("last_updated", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_aggregated_stats_metric_name"), "aggregated_stats", ["metric_name"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_aggregated_stats_metric_name"), table_name="aggregated_stats")
    op.drop_table("aggregated_stats")

    op.drop_index("ix_analytics_metrics_type_time_zone", table_name="analytics_metrics")
    op.drop_index(op.f("ix_analytics_metrics_zone"), table_name="analytics_metrics")
    op.drop_index(op.f("ix_analytics_metrics_timestamp"), table_name="analytics_metrics")
    op.drop_index(op.f("ix_analytics_metrics_metric_type"), table_name="analytics_metrics")
    op.drop_table("analytics_metrics")

    op.drop_index("ix_analytics_events_zone_time", table_name="analytics_events")
    op.drop_index("ix_analytics_events_type_time", table_name="analytics_events")
    op.drop_index(op.f("ix_analytics_events_event_timestamp"), table_name="analytics_events")
    op.drop_index(op.f("ix_analytics_events_risk_category"), table_name="analytics_events")
    op.drop_index(op.f("ix_analytics_events_user_id"), table_name="analytics_events")
    op.drop_index(op.f("ix_analytics_events_zone"), table_name="analytics_events")
    op.drop_index(op.f("ix_analytics_events_routing_key"), table_name="analytics_events")
    op.drop_index(op.f("ix_analytics_events_event_type"), table_name="analytics_events")
    op.drop_index(op.f("ix_analytics_events_event_id"), table_name="analytics_events")
    op.drop_index(op.f("ix_analytics_events_event_key"), table_name="analytics_events")
    op.drop_table("analytics_events")
