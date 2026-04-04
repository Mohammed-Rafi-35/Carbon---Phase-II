from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.constants import LedgerEntryType, PayoutStatus
from app.core.exceptions import AppError
from app.events.publisher import publish_payout_event
from app.integrations.payment_gateway import PaymentGatewayClient
from app.repositories.ledger_repository import LedgerRepository
from app.repositories.payout_repository import PayoutRepository
from app.schemas.payout import PayoutHistoryItem, ProcessPayoutData, ProcessPayoutRequest, RetryPayoutData
from app.services.metrics_service import PAYOUT_FAILURE_TOTAL, PAYOUT_RETRY_TOTAL, PAYOUT_SUCCESS_TOTAL


class PayoutService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.payout_repository = PayoutRepository(db)
        self.ledger_repository = LedgerRepository(db)
        self.gateway = PaymentGatewayClient()

    def process_payout(self, payload: ProcessPayoutRequest, idempotency_key: str) -> ProcessPayoutData:
        existing_by_key = self.payout_repository.get_by_idempotency_key(idempotency_key)
        if existing_by_key:
            if (
                existing_by_key.claim_id != payload.claim_id
                or existing_by_key.user_id != payload.user_id
                or existing_by_key.amount != payload.amount
            ):
                raise AppError(
                    "Idempotency key is already used with a different payout request.",
                    "IDEMPOTENCY_KEY_REUSED",
                    409,
                )
            return ProcessPayoutData(transaction_id=existing_by_key.id, status=existing_by_key.status)

        existing_claim = self.payout_repository.get_by_claim_id(payload.claim_id)
        if existing_claim:
            raise AppError("Duplicate payout for claim.", "DUPLICATE_PAYOUT", 409)

        try:
            payout = self.payout_repository.create(
                claim_id=payload.claim_id,
                user_id=payload.user_id,
                amount=payload.amount,
                status=PayoutStatus.PENDING,
                idempotency_key=idempotency_key,
                transaction_ref=None,
            )
        except IntegrityError as exc:
            self.db.rollback()
            raced_by_key = self.payout_repository.get_by_idempotency_key(idempotency_key)
            if raced_by_key and raced_by_key.claim_id == payload.claim_id and raced_by_key.user_id == payload.user_id:
                return ProcessPayoutData(transaction_id=raced_by_key.id, status=raced_by_key.status)

            raced_by_claim = self.payout_repository.get_by_claim_id(payload.claim_id)
            if raced_by_claim:
                raise AppError("Duplicate payout for claim.", "DUPLICATE_PAYOUT", 409) from exc

            raise AppError("Duplicate payout detected.", "DUPLICATE_PAYOUT", 409) from exc

        gateway_result = self.gateway.process_payout(
            payout_id=payout.id,
            user_id=payload.user_id,
            amount=payload.amount,
        )

        processed_at = datetime.now(tz=timezone.utc)

        if gateway_result.success:
            payout = self.payout_repository.save(
                payout,
                status=PayoutStatus.COMPLETED,
                transaction_ref=gateway_result.transaction_ref,
                processed_at=processed_at,
            )
            self._create_ledger_entry_if_missing(payout.id)
            publish_payout_event(
                "PAYOUT_COMPLETED",
                {
                    "transaction_id": str(payout.id),
                    "user_id": str(payout.user_id),
                    "claim_id": str(payout.claim_id),
                    "amount": float(payout.amount),
                    "status": payout.status,
                },
            )
            PAYOUT_SUCCESS_TOTAL.inc()
            return ProcessPayoutData(transaction_id=payout.id, status=payout.status)

        self.payout_repository.save(
            payout,
            status=PayoutStatus.FAILED,
            transaction_ref=gateway_result.transaction_ref,
            processed_at=processed_at,
        )
        publish_payout_event(
            "PAYOUT_FAILED",
            {
                "transaction_id": str(payout.id),
                "user_id": str(payout.user_id),
                "claim_id": str(payout.claim_id),
                "amount": float(payout.amount),
                "status": PayoutStatus.FAILED,
                "reason": gateway_result.reason,
            },
        )
        PAYOUT_FAILURE_TOTAL.inc()
        raise AppError("Transaction failed", "PAYOUT_FAILED", 500)

    def get_payout_history(self, user_id: UUID) -> list[PayoutHistoryItem]:
        rows = self.payout_repository.list_for_user(user_id)
        return [
            PayoutHistoryItem(
                transaction_id=row.id,
                claim_id=row.claim_id,
                user_id=row.user_id,
                amount=row.amount,
                status=row.status,
                timestamp=row.created_at,
                processed_at=row.processed_at,
                transaction_ref=row.transaction_ref,
            )
            for row in rows
        ]

    def retry_failed_payout(self, transaction_id: UUID) -> RetryPayoutData:
        payout = self.payout_repository.get_by_id(transaction_id)
        if payout is None:
            raise AppError("Transaction not found.", "TRANSACTION_NOT_FOUND", 404)

        if payout.status != PayoutStatus.FAILED:
            raise AppError("Retry is allowed only for failed payouts.", "RETRY_NOT_ALLOWED", 409)

        PAYOUT_RETRY_TOTAL.inc()

        gateway_result = self.gateway.process_payout(
            payout_id=payout.id,
            user_id=payout.user_id,
            amount=payout.amount,
        )

        if gateway_result.success:
            self.payout_repository.save(
                payout,
                status=PayoutStatus.COMPLETED,
                transaction_ref=gateway_result.transaction_ref,
                processed_at=datetime.now(tz=timezone.utc),
            )
            self._create_ledger_entry_if_missing(payout.id)
            publish_payout_event(
                "PAYOUT_COMPLETED",
                {
                    "transaction_id": str(payout.id),
                    "user_id": str(payout.user_id),
                    "claim_id": str(payout.claim_id),
                    "amount": float(payout.amount),
                    "status": PayoutStatus.COMPLETED,
                    "retry": True,
                },
            )
            PAYOUT_SUCCESS_TOTAL.inc()
            return RetryPayoutData(status="retry_initiated")

        self.payout_repository.save(
            payout,
            status=PayoutStatus.FAILED,
            transaction_ref=gateway_result.transaction_ref,
            processed_at=datetime.now(tz=timezone.utc),
        )
        PAYOUT_FAILURE_TOTAL.inc()
        raise AppError("Transaction failed", "PAYOUT_FAILED", 500)

    def _create_ledger_entry_if_missing(self, transaction_id: UUID) -> None:
        payout = self.payout_repository.get_by_id(transaction_id)
        if payout is None:
            return

        existing = self.ledger_repository.get_by_transaction_id(transaction_id)
        if existing:
            return

        self.ledger_repository.create_entry(
            user_id=payout.user_id,
            transaction_id=payout.id,
            type_=LedgerEntryType.CREDIT,
            amount=payout.amount,
        )
