from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payout import Payout


class PayoutRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        claim_id: UUID,
        user_id: UUID,
        amount: Decimal,
        status: str,
        idempotency_key: str,
        transaction_ref: str | None = None,
    ) -> Payout:
        payout = Payout(
            claim_id=claim_id,
            user_id=user_id,
            amount=amount,
            status=status,
            idempotency_key=idempotency_key,
            transaction_ref=transaction_ref,
        )
        self.db.add(payout)
        self.db.commit()
        self.db.refresh(payout)
        return payout

    def get_by_id(self, payout_id: UUID) -> Payout | None:
        stmt = select(Payout).where(Payout.id == payout_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_claim_id(self, claim_id: UUID) -> Payout | None:
        stmt = select(Payout).where(Payout.claim_id == claim_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_idempotency_key(self, key: str) -> Payout | None:
        stmt = select(Payout).where(Payout.idempotency_key == key)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_user(self, user_id: UUID) -> list[Payout]:
        stmt = select(Payout).where(Payout.user_id == user_id).order_by(Payout.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def save(
        self,
        payout: Payout,
        *,
        status: str,
        transaction_ref: str | None,
        processed_at: datetime | None,
    ) -> Payout:
        payout.status = status
        payout.transaction_ref = transaction_ref
        payout.processed_at = processed_at
        self.db.add(payout)
        self.db.commit()
        self.db.refresh(payout)
        return payout
