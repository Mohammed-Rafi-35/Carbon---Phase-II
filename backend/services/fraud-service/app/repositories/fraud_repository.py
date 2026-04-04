from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.fraud_audit import FraudAuditTrail
from app.models.fraud_check import FraudCheckLog


class FraudRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_log(
        self,
        *,
        claim_id: UUID,
        user_id: UUID,
        fraud_score: float,
        status: str,
        reason: str | None,
        source: str,
    ) -> FraudCheckLog:
        row = FraudCheckLog(
            claim_id=claim_id,
            user_id=user_id,
            fraud_score=fraud_score,
            status=status,
            reason=reason,
            source=source,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def latest_for_user(self, user_id: UUID, limit: int = 5) -> list[FraudCheckLog]:
        stmt = (
            select(FraudCheckLog)
            .where(FraudCheckLog.user_id == user_id)
            .order_by(desc(FraudCheckLog.created_at))
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def latest_for_claim(self, claim_id: UUID) -> FraudCheckLog | None:
        stmt = (
            select(FraudCheckLog)
            .where(FraudCheckLog.claim_id == claim_id)
            .order_by(desc(FraudCheckLog.created_at))
            .limit(1)
        )
        return self.db.execute(stmt).scalars().first()

    def count_for_claim(self, claim_id: UUID) -> int:
        stmt = select(func.count(FraudCheckLog.id)).where(FraudCheckLog.claim_id == claim_id)
        value = self.db.execute(stmt).scalar_one()
        return int(value)

    def exists_recent_fail_for_user(self, user_id: UUID, since: datetime) -> bool:
        stmt = select(FraudCheckLog.id).where(
            FraudCheckLog.user_id == user_id,
            FraudCheckLog.status == "FAIL",
            FraudCheckLog.created_at >= since,
        )
        return self.db.execute(stmt).first() is not None

    def create_audit(
        self,
        *,
        claim_id: UUID,
        actor: str,
        action: str,
        decision_status: str | None,
        reason: str | None,
    ) -> FraudAuditTrail:
        row = FraudAuditTrail(
            claim_id=claim_id,
            actor=actor,
            action=action,
            decision_status=decision_status,
            reason=reason,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row
