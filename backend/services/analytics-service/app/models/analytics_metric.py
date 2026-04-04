from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Index, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class AnalyticsMetric(Base):
    __tablename__ = "analytics_metrics"
    __table_args__ = (
        Index("ix_analytics_metrics_type_time_zone", "metric_type", "timestamp", "zone"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    value: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    zone: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
