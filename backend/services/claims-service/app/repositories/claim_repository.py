from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.claim import Claim


class ClaimRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, user_id: UUID, event_id: UUID, status: str, idempotency_key: str | None = None) -> Claim:
        claim = Claim(
            user_id=user_id,
            event_id=event_id,
            status=status,
            idempotency_key=idempotency_key,
        )
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)
        return claim

    def get_by_id(self, claim_id: UUID) -> Claim | None:
        stmt = select(Claim).where(Claim.id == claim_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_user_event(self, *, user_id: UUID, event_id: UUID) -> Claim | None:
        stmt = select(Claim).where(Claim.user_id == user_id, Claim.event_id == event_id).limit(1)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_idempotency_key(self, key: str) -> Claim | None:
        stmt = select(Claim).where(Claim.idempotency_key == key).limit(1)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_user(self, user_id: UUID) -> list[Claim]:
        stmt = select(Claim).where(Claim.user_id == user_id).order_by(Claim.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def save_decision(
        self,
        claim: Claim,
        *,
        status: str,
        policy_id: UUID | None = None,
        risk_score: Decimal | None = None,
        fraud_score: Decimal | None = None,
        payout_amount: Decimal | None,
        rejection_reason: str | None,
    ) -> Claim:
        claim.status = status
        if policy_id is not None:
            claim.policy_id = policy_id
        if risk_score is not None:
            claim.risk_score = risk_score
        if fraud_score is not None:
            claim.fraud_score = fraud_score
        claim.payout_amount = payout_amount
        claim.rejection_reason = rejection_reason
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)
        return claim

    def save_status(self, claim: Claim, *, status: str) -> Claim:
        claim.status = status
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)
        return claim

    def save_progress(
        self,
        claim: Claim,
        *,
        status: str,
        policy_id: UUID | None = None,
        risk_score: Decimal | None = None,
        fraud_score: Decimal | None = None,
        rejection_reason: str | None = None,
    ) -> Claim:
        claim.status = status
        if policy_id is not None:
            claim.policy_id = policy_id
        if risk_score is not None:
            claim.risk_score = risk_score
        if fraud_score is not None:
            claim.fraud_score = fraud_score
        if rejection_reason is not None:
            claim.rejection_reason = rejection_reason
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)
        return claim
