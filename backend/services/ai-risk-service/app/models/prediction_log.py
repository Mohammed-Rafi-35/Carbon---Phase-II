from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    zone: Mapped[str] = mapped_column(String(50), nullable=False)
    input_features: Mapped[dict] = mapped_column(JSON, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_category: Mapped[str] = mapped_column(String(16), nullable=False)
    premium_multiplier: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    top_factors: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    actual_outcome: Mapped[float | None] = mapped_column(Float, nullable=True)
    corrected_label: Mapped[str | None] = mapped_column(String(16), nullable=True)
    review_status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending", server_default="pending", index=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
