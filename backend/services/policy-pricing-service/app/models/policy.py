from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    zone: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    insured_weekly_income: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    insured_daily_income: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    coverage_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    base_premium: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    gst: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_premium: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    stabilization_factor: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    waiting_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    activity_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    premium_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    logs: Mapped[list[PolicyLog]] = relationship(
        "PolicyLog",
        back_populates="policy",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class PolicyLog(Base):
    __tablename__ = "policy_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    policy: Mapped[Policy] = relationship("Policy", back_populates="logs")