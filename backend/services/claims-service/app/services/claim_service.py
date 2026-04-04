from __future__ import annotations

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import ClaimStatus
from app.core.exceptions import AppError
from app.core.security import create_access_token
from app.events.publisher import ClaimsEventPublisher
from app.integrations.ai_risk_client import AIRiskServiceClient
from app.integrations.fraud_client import FraudCheckResult, FraudServiceClient
from app.integrations.payout_client import PayoutServiceClient
from app.integrations.policy_client import PolicyServiceClient
from app.models.claim import Claim
from app.repositories.claim_log_repository import ClaimLogRepository
from app.repositories.claim_repository import ClaimRepository
from app.schemas.claims import ClaimDetailData, ClaimHistoryItem, ClaimLogItem, ProcessClaimData


logger = logging.getLogger(__name__)


class ClaimService:
    def __init__(
        self,
        db: Session,
        *,
        policy_client: PolicyServiceClient | None = None,
        risk_client: AIRiskServiceClient | None = None,
        fraud_client: FraudServiceClient | None = None,
        payout_client: PayoutServiceClient | None = None,
        publisher: ClaimsEventPublisher | None = None,
    ) -> None:
        self.settings = get_settings()
        self.repo = ClaimRepository(db)
        self.log_repo = ClaimLogRepository(db)
        self.policy_client = policy_client or PolicyServiceClient()
        self.risk_client = risk_client or AIRiskServiceClient()
        self.fraud_client = fraud_client or FraudServiceClient()
        self.payout_client = payout_client or PayoutServiceClient()
        self.publisher = publisher or ClaimsEventPublisher()

    def auto_create_claim(
        self,
        *,
        user_id: UUID,
        event_id: UUID,
        event_payload: dict | None = None,
        idempotency_key: str | None = None,
    ) -> Claim:
        if idempotency_key:
            existing_by_key = self.repo.get_by_idempotency_key(idempotency_key)
            if existing_by_key:
                if existing_by_key.user_id != user_id or existing_by_key.event_id != event_id:
                    raise AppError(
                        "Idempotency key is already used with a different claim request.",
                        "IDEMPOTENCY_KEY_REUSED",
                        409,
                    )
                return existing_by_key

        existing = self.repo.get_by_user_event(user_id=user_id, event_id=event_id)
        if existing:
            return existing

        try:
            claim = self.repo.create(
                user_id=user_id,
                event_id=event_id,
                status=ClaimStatus.INITIATED,
                idempotency_key=idempotency_key,
            )
        except IntegrityError:
            self.repo.db.rollback()
            if idempotency_key:
                race_by_key = self.repo.get_by_idempotency_key(idempotency_key)
                if race_by_key:
                    return race_by_key
            race_by_event = self.repo.get_by_user_event(user_id=user_id, event_id=event_id)
            if race_by_event:
                return race_by_event
            raise

        self._log(
            claim,
            stage=ClaimStatus.INITIATED,
            message="Claim created from disruption event.",
            details=event_payload,
        )
        self.publisher.publish_claim_initiated(
            {
                "claim_id": str(claim.id),
                "user_id": str(claim.user_id),
                "event_id": str(claim.event_id),
            }
        )
        return claim

    def list_claims_for_user(self, user_id: UUID) -> list[ClaimHistoryItem]:
        rows = self.repo.list_for_user(user_id)
        return [
            ClaimHistoryItem(
                claim_id=row.id,
                event_id=row.event_id,
                status=row.status,
                payout_amount=row.payout_amount,
                created_at=row.created_at,
            )
            for row in rows
        ]

    def get_claim_detail(self, claim_id: UUID) -> ClaimDetailData:
        claim = self.repo.get_by_id(claim_id)
        if claim is None:
            raise AppError("Claim not found.", "CLAIM_NOT_FOUND", 404)

        logs = self.log_repo.list_for_claim(claim.id)
        return ClaimDetailData(
            claim_id=claim.id,
            user_id=claim.user_id,
            policy_id=claim.policy_id,
            event_id=claim.event_id,
            status=claim.status,
            risk_score=claim.risk_score,
            fraud_score=claim.fraud_score,
            payout_amount=claim.payout_amount,
            rejection_reason=claim.rejection_reason,
            created_at=claim.created_at,
            updated_at=claim.updated_at,
            logs=[
                ClaimLogItem(
                    stage=item.stage,
                    message=item.message,
                    timestamp=item.created_at,
                    details=item.details,
                )
                for item in logs
            ],
        )

    def process_claim(self, *, claim_id: UUID, token: str, request_id: str | None = None) -> ProcessClaimData:
        claim = self.repo.get_by_id(claim_id)
        if claim is None:
            raise AppError("Claim not found.", "CLAIM_NOT_FOUND", 404)

        if claim.status == ClaimStatus.PAID:
            return ProcessClaimData(status=ClaimStatus.APPROVED, payout_amount=claim.payout_amount)
        if claim.status == ClaimStatus.APPROVED:
            self.publisher.publish_claim_processing(
                {
                    "claim_id": str(claim.id),
                    "request_id": request_id,
                }
            )
            self._log(
                claim,
                stage=ClaimStatus.APPROVED,
                message="Approved claim queued for payout retry.",
                details={"request_id": request_id},
            )
            return ProcessClaimData(status=ClaimStatus.PROCESSING, payout_amount=claim.payout_amount)
        if claim.status == ClaimStatus.REJECTED:
            return ProcessClaimData(status=ClaimStatus.REJECTED, payout_amount=None)
        if claim.status == ClaimStatus.PROCESSING:
            return ProcessClaimData(status=ClaimStatus.PROCESSING, payout_amount=claim.payout_amount)

        claim = self.repo.save_status(claim, status=ClaimStatus.PROCESSING)
        self._log(
            claim,
            stage=ClaimStatus.PROCESSING,
            message="Claim queued for asynchronous processing.",
            details={"request_id": request_id},
        )
        self.publisher.publish_claim_processing(
            {
                "claim_id": str(claim.id),
                "request_id": request_id,
            }
        )
        logger.info(
            "[%s] [claims-service] [claim_processing_queued] claim_id=%s",
            request_id or "-",
            claim.id,
        )
        return ProcessClaimData(status=ClaimStatus.PROCESSING, payout_amount=claim.payout_amount)

    def process_claim_async(
        self,
        *,
        claim_id: UUID,
        request_id: str | None = None,
        token: str | None = None,
    ) -> ProcessClaimData:
        claim = self.repo.get_by_id(claim_id)
        if claim is None:
            raise AppError("Claim not found.", "CLAIM_NOT_FOUND", 404)

        if claim.status == ClaimStatus.PAID:
            return ProcessClaimData(status=ClaimStatus.APPROVED, payout_amount=claim.payout_amount)
        if claim.status == ClaimStatus.APPROVED:
            service_token = token or create_access_token(subject=str(claim.user_id), role="service", expires_hours=1)
            return self._finalize_approved_claim(claim=claim, request_id=request_id, service_token=service_token)
        if claim.status == ClaimStatus.REJECTED:
            return ProcessClaimData(status=ClaimStatus.REJECTED, payout_amount=None)

        try:
            if claim.status != ClaimStatus.PROCESSING:
                claim = self.repo.save_status(claim, status=ClaimStatus.PROCESSING)

            service_token = token or create_access_token(subject=str(claim.user_id), role="service", expires_hours=1)
            logger.info(
                "[%s] [claims-service] [claim_processing_started] claim_id=%s",
                request_id or "-",
                claim.id,
            )
            policy_result = self.policy_client.validate_for_claim(
                user_id=str(claim.user_id),
                token=service_token,
                request_id=request_id,
            )
            if policy_result.degraded:
                raise RuntimeError("Policy service degraded")

            policy_id = self._to_uuid(policy_result.policy_id)

            if not policy_result.valid:
                self.repo.save_decision(
                    claim,
                    status=ClaimStatus.REJECTED,
                    policy_id=policy_id,
                    payout_amount=None,
                    rejection_reason=policy_result.reason or "Policy validation failed.",
                )
                self._log(
                    claim,
                    stage=ClaimStatus.REJECTED,
                    message="Policy validation failed.",
                    details={"reason": policy_result.reason},
                )
                return ProcessClaimData(status=ClaimStatus.REJECTED, payout_amount=None)

            claim = self.repo.save_progress(
                claim,
                status=ClaimStatus.VALIDATED,
                policy_id=policy_id,
            )
            self._log(
                claim,
                stage=ClaimStatus.VALIDATED,
                message="Policy validated for claim.",
                details={"policy_id": policy_result.policy_id, "zone": policy_result.zone},
            )

            risk_result = self.risk_client.evaluate_claim(
                zone=policy_result.zone,
                severity=None,
                event_type=None,
                token=service_token,
                request_id=request_id,
            )
            if risk_result.degraded:
                raise RuntimeError("AI risk service degraded")

            risk_score = Decimal(str(risk_result.risk_score))
            claim = self.repo.save_progress(
                claim,
                status=ClaimStatus.EVALUATED,
                risk_score=risk_score,
            )
            self._log(
                claim,
                stage=ClaimStatus.EVALUATED,
                message="AI risk evaluated.",
                details={
                    "risk_score": risk_result.risk_score,
                    "risk_category": risk_result.risk_category,
                    "premium_multiplier": risk_result.premium_multiplier,
                },
            )

            if risk_result.risk_score >= self.settings.risk_reject_threshold:
                self.repo.save_decision(
                    claim,
                    status=ClaimStatus.REJECTED,
                    policy_id=policy_id,
                    risk_score=risk_score,
                    payout_amount=None,
                    rejection_reason="Risk score exceeds allowed threshold.",
                )
                self._log(
                    claim,
                    stage=ClaimStatus.REJECTED,
                    message="Claim rejected due to high risk score.",
                    details={"risk_score": risk_result.risk_score},
                )
                return ProcessClaimData(status=ClaimStatus.REJECTED, payout_amount=None)

            fraud_result: FraudCheckResult = self.fraud_client.check_claim(
                claim_id=str(claim.id),
                user_id=str(claim.user_id),
                token=service_token,
                event_context={"zone": policy_result.zone} if policy_result.zone else None,
                request_id=request_id,
            )
            if fraud_result.degraded:
                raise RuntimeError("Fraud service degraded")

            fraud_score = Decimal(str(fraud_result.fraud_score))
            if fraud_result.status == "FAIL":
                self.repo.save_decision(
                    claim,
                    status=ClaimStatus.REJECTED,
                    policy_id=policy_id,
                    risk_score=risk_score,
                    fraud_score=fraud_score,
                    payout_amount=None,
                    rejection_reason=fraud_result.reason or f"Fraud risk too high ({float(fraud_score):.2f}).",
                )
                self._log(
                    claim,
                    stage=ClaimStatus.REJECTED,
                    message="Claim rejected by fraud checks.",
                    details={"fraud_score": float(fraud_score), "reason": fraud_result.reason},
                )
                return ProcessClaimData(status=ClaimStatus.REJECTED, payout_amount=None)

            payout_amount = Decimal(str(self.settings.default_payout_amount))
            claim = self.repo.save_decision(
                claim,
                status=ClaimStatus.APPROVED,
                policy_id=policy_id,
                risk_score=risk_score,
                fraud_score=fraud_score,
                payout_amount=payout_amount,
                rejection_reason=None,
            )
            self._log(
                claim,
                stage=ClaimStatus.APPROVED,
                message="Claim approved after policy, risk, and fraud evaluation.",
                details={"payout_amount": float(payout_amount)},
            )

            self.publisher.publish_claim_approved(
                {
                    "claim_id": str(claim.id),
                    "user_id": str(claim.user_id),
                    "amount": float(payout_amount),
                }
            )
            result = self._finalize_approved_claim(claim=claim, request_id=request_id, service_token=service_token)
            logger.info(
                "[%s] [claims-service] [claim_processing_completed] claim_id=%s status=%s",
                request_id or "-",
                claim.id,
                claim.status,
            )
            return result
        except Exception as exc:
            self._log(
                claim,
                stage=ClaimStatus.PROCESSING,
                message="Claim processing attempt failed; queued for retry.",
                details={"error": str(exc), "request_id": request_id},
            )
            logger.exception(
                "[%s] [claims-service] [claim_processing_failed] claim_id=%s error=%s",
                request_id or "-",
                claim.id,
                exc,
            )
            raise

    def create_claims_from_disruption(self, event_payload: dict) -> int:
        raw_event_id = event_payload.get("event_id")
        if not raw_event_id:
            return 0

        try:
            event_id = UUID(str(raw_event_id))
        except ValueError:
            return 0

        raw_users = event_payload.get("user_ids")
        if isinstance(raw_users, list) and raw_users:
            user_ids = [str(item) for item in raw_users]
        else:
            user_ids = self.settings.default_claim_users

        created_count = 0
        for user_id_str in user_ids:
            try:
                user_id = UUID(user_id_str)
            except ValueError:
                continue
            existing = self.repo.get_by_user_event(user_id=user_id, event_id=event_id)
            if existing is not None:
                continue

            self.auto_create_claim(user_id=user_id, event_id=event_id, event_payload=event_payload)
            created_count += 1
        return created_count

    def _log(self, claim: Claim, *, stage: str, message: str, details: dict | None = None) -> None:
        self.log_repo.create(claim_id=claim.id, stage=stage, message=message, details=details)

    def _finalize_approved_claim(self, *, claim: Claim, request_id: str | None, service_token: str) -> ProcessClaimData:
        payout_amount = claim.payout_amount or Decimal(str(self.settings.default_payout_amount))
        payout_result = self.payout_client.process_payout(
            claim_id=str(claim.id),
            user_id=str(claim.user_id),
            amount=float(payout_amount),
            token=service_token,
            request_id=request_id or f"claim-{claim.id}",
            idempotency_key=f"claim-{claim.id}",
        )
        if payout_result.success:
            claim = self.repo.save_status(claim, status=ClaimStatus.PAID)
            self._log(
                claim,
                stage=ClaimStatus.PAID,
                message="Payout processed successfully.",
                details={
                    "transaction_id": payout_result.transaction_id,
                    "payout_status": payout_result.status,
                },
            )
            return ProcessClaimData(status=ClaimStatus.APPROVED, payout_amount=payout_amount)

        self._log(
            claim,
            stage=ClaimStatus.APPROVED,
            message="Claim approved but payout processing failed.",
            details={
                "error_code": payout_result.error_code,
                "error_message": payout_result.error_message,
            },
        )
        if payout_result.error_code == "PAYOUT_REQUEST_FAILED":
            raise RuntimeError("Payout service degraded")
        return ProcessClaimData(status=ClaimStatus.APPROVED, payout_amount=payout_amount)

    @staticmethod
    def _to_uuid(value: str | None) -> UUID | None:
        if not value:
            return None
        try:
            return UUID(str(value))
        except ValueError:
            return None
