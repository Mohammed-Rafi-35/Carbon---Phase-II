from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.policy import Policy


class PolicyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        user_id: UUID,
        zone: str,
        status: str,
        insured_weekly_income: Decimal,
        insured_daily_income: Decimal,
        coverage_rate: Decimal,
        base_premium: Decimal,
        gst: Decimal,
        total_premium: Decimal,
        stabilization_factor: Decimal,
        waiting_period_end: datetime,
        activity_days: int,
        premium_paid: bool,
    ) -> Policy:
        policy = Policy(
            user_id=user_id,
            zone=zone,
            status=status,
            insured_weekly_income=insured_weekly_income,
            insured_daily_income=insured_daily_income,
            coverage_rate=coverage_rate,
            base_premium=base_premium,
            gst=gst,
            total_premium=total_premium,
            stabilization_factor=stabilization_factor,
            waiting_period_end=waiting_period_end,
            activity_days=activity_days,
            premium_paid=premium_paid,
        )
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        return policy

    def get_by_id(self, policy_id: UUID) -> Policy | None:
        stmt = select(Policy).where(Policy.id == policy_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_latest_by_user(self, user_id: UUID) -> Policy | None:
        stmt = select(Policy).where(Policy.user_id == user_id).order_by(Policy.created_at.desc())
        return self.db.execute(stmt).scalars().first()

    def save(self, policy: Policy) -> Policy:
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        return policy