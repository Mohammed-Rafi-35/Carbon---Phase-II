from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ledger import LedgerEntry


class LedgerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_latest_balance(self, user_id: UUID) -> Decimal:
        stmt = (
            select(LedgerEntry)
            .where(LedgerEntry.user_id == user_id)
            .order_by(LedgerEntry.created_at.desc())
            .limit(1)
        )
        row = self.db.execute(stmt).scalar_one_or_none()
        if row is None:
            return Decimal("0.00")
        return Decimal(str(row.balance))

    def get_by_transaction_id(self, transaction_id: UUID) -> LedgerEntry | None:
        stmt = select(LedgerEntry).where(LedgerEntry.transaction_id == transaction_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_entry(
        self,
        *,
        user_id: UUID,
        transaction_id: UUID,
        type_: str,
        amount: Decimal,
    ) -> LedgerEntry:
        current_balance = self.get_latest_balance(user_id)
        new_balance = (current_balance + amount).quantize(Decimal("0.01"))

        entry = LedgerEntry(
            user_id=user_id,
            transaction_id=transaction_id,
            type=type_,
            amount=amount,
            balance=new_balance,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry
