from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import FraudSource, FraudStatus
from app.core.exceptions import AppError
from app.events.publisher import FraudEventPublisher
from app.integrations.ai_risk_client import AIRiskServiceClient
from app.integrations.identity_client import IdentityServiceClient
from app.repositories.fraud_repository import FraudRepository
from app.schemas.fraud import (
    FraudCheckData,
    FraudCheckRequest,
    FraudEventContext,
    FraudLogData,
    FraudOverrideData,
    FraudOverrideRequest,
)
from app.services.ml_scorer import FraudMLScorer


class FraudService:
    def __init__(
        self,
        db: Session,
        publisher: FraudEventPublisher | None = None,
        identity_client: IdentityServiceClient | None = None,
        ai_risk_client: AIRiskServiceClient | None = None,
        ml_scorer: FraudMLScorer | None = None,
    ) -> None:
        self.settings = get_settings()
        self.repo = FraudRepository(db)
        self.publisher = publisher or FraudEventPublisher()
        self.identity_client = identity_client or IdentityServiceClient()
        self.ai_risk_client = ai_risk_client or AIRiskServiceClient()
        self.ml_scorer = ml_scorer or FraudMLScorer()

    def check_claim(
        self,
        payload: FraudCheckRequest,
        source: str = FraudSource.API,
        token: str | None = None,
        request_id: str | None = None,
    ) -> FraudCheckData:
        external_signals = self._collect_external_signals(payload, token=token, request_id=request_id)
        score, reason = self._score_payload(payload, external_signals)
        status = FraudStatus.FAIL if score >= self.settings.fraud_fail_threshold else FraudStatus.PASS

        self.repo.create_log(
            claim_id=payload.claim_id,
            user_id=payload.user_id,
            fraud_score=score,
            status=status,
            reason=reason,
            source=str(source),
        )

        if status == FraudStatus.FAIL:
            self.repo.create_audit(
                claim_id=payload.claim_id,
                actor=str(source),
                action="fraud_check_failed",
                decision_status=status,
                reason=reason,
            )

        if status == FraudStatus.FAIL:
            self.publisher.publish_fraud_detected(self._build_fail_event_payload(payload, score, reason, str(source)))

        return FraudCheckData(fraud_score=score, status=status, reason=reason)

    def get_claim_log(self, claim_id: UUID) -> FraudLogData:
        row = self.repo.latest_for_claim(claim_id)
        if row is None:
            raise AppError("Fraud log not found for claim.", "FRAUD_LOG_NOT_FOUND", 404)

        return FraudLogData(
            claim_id=row.claim_id,
            user_id=row.user_id,
            fraud_score=row.fraud_score,
            status=row.status,
            reason=row.reason,
            source=row.source,
            timestamp=row.created_at,
        )

    def override_claim(self, payload: FraudOverrideRequest, admin_subject: str) -> FraudOverrideData:
        latest = self.repo.latest_for_claim(payload.claim_id)
        if latest is None:
            raise AppError("Fraud log not found for claim.", "FRAUD_LOG_NOT_FOUND", 404)

        override_status = FraudStatus(payload.override_status)
        override_score = 1.0 if override_status == FraudStatus.FAIL else 0.0
        override_reason = f"manual_override:{payload.reason}"

        self.repo.create_log(
            claim_id=latest.claim_id,
            user_id=latest.user_id,
            fraud_score=override_score,
            status=override_status,
            reason=override_reason,
            source=FraudSource.OVERRIDE,
        )
        self.repo.create_audit(
            claim_id=latest.claim_id,
            actor=admin_subject,
            action="manual_override",
            decision_status=override_status,
            reason=override_reason,
        )

        if override_status == FraudStatus.FAIL:
            self.publisher.publish_fraud_detected(
                {
                    "claim_id": str(latest.claim_id),
                    "user_id": str(latest.user_id),
                    "fraud_score": override_score,
                    "reason": override_reason,
                    "source": FraudSource.OVERRIDE,
                    "admin_subject": admin_subject,
                }
            )

        return FraudOverrideData(
            status="updated",
            claim_id=latest.claim_id,
            override_status=override_status,
        )

    def check_claim_from_event(self, payload: dict) -> FraudCheckData | None:
        claim_id = payload.get("claim_id")
        user_id = payload.get("user_id")
        if not claim_id or not user_id:
            return None

        activity_payload = payload.get("activity") if isinstance(payload.get("activity"), dict) else {}
        event_payload = payload.get("event") if isinstance(payload.get("event"), dict) else {}

        event_context: FraudEventContext | None = None
        if event_payload:
            event_context = FraudEventContext(
                zone=event_payload.get("zone"),
                type=event_payload.get("type"),
                severity=event_payload.get("severity"),
            )

        request = FraudCheckRequest(
            claim_id=UUID(str(claim_id)),
            user_id=UUID(str(user_id)),
            activity={
                "gps_valid": bool(activity_payload.get("gps_valid", payload.get("gps_valid", True))),
                "activity_score": float(activity_payload.get("activity_score", payload.get("activity_score", 0.8))),
                "device_consistency": activity_payload.get("device_consistency", payload.get("device_consistency")),
            },
            event=event_context,
        )
        return self.check_claim(request, source=FraudSource.EVENT)

    def _score_payload(self, payload: FraudCheckRequest, external_signals: dict[str, Any]) -> tuple[float, str | None]:
        score = 0.0
        reason_parts: list[str] = []

        if not payload.activity.gps_valid:
            score += 0.6
            reason_parts.append("gps_invalid")

        if payload.activity.activity_score < 0.5:
            score += 0.5 - payload.activity.activity_score
            reason_parts.append("low_activity")

        if payload.activity.device_consistency is False:
            score += 0.2
            reason_parts.append("device_inconsistent")

        duplicate_count = self.repo.count_for_claim(payload.claim_id)
        if duplicate_count >= self.settings.max_duplicate_claims:
            score += 0.45
            reason_parts.append("duplicate_claim_pattern")

        recent = self.repo.latest_for_user(payload.user_id, limit=5)
        recent_fails = sum(1 for row in recent if row.status == FraudStatus.FAIL)
        if recent_fails >= 2:
            score += 0.2
            reason_parts.append("repeat_fail_pattern")

        event_penalty = self._event_consistency_penalty(payload)
        if event_penalty > 0:
            score += event_penalty
            reason_parts.append("event_consistency_mismatch")

        worker_profile = external_signals.get("worker_profile")
        if isinstance(worker_profile, dict) and payload.event is not None and payload.event.zone:
            profile_zone = worker_profile.get("zone")
            if isinstance(profile_zone, str) and profile_zone.strip().lower() != payload.event.zone.strip().lower():
                score += 0.1
                reason_parts.append("zone_mismatch")

        external_risk_score = external_signals.get("risk_score")
        if isinstance(external_risk_score, float) and external_risk_score >= 0.85:
            score += 0.1
            reason_parts.append("elevated_ai_risk")

        ml_score = self.ml_scorer.score(
            gps_valid=payload.activity.gps_valid,
            activity_score=payload.activity.activity_score,
            device_consistency=payload.activity.device_consistency,
            severity=payload.event.severity if payload.event else None,
            event_type=payload.event.type if payload.event else None,
            external_risk_score=external_risk_score if isinstance(external_risk_score, float) else None,
        )
        if isinstance(ml_score, float):
            score += max(0.0, min(1.0, ml_score)) * 0.25
            if ml_score >= 0.5:
                reason_parts.append("ml_anomaly")

        score = min(1.0, round(score, 3))
        reason = ",".join(dict.fromkeys(reason_parts)) if reason_parts else None
        return score, reason

    def _event_consistency_penalty(self, payload: FraudCheckRequest) -> float:
        if payload.event is None:
            return 0.0

        penalty = 0.0
        severity = (payload.event.severity or "").upper()
        event_type = (payload.event.type or "").lower()
        activity_score = payload.activity.activity_score

        if severity == "HIGH" and activity_score > 0.95:
            penalty += 0.1

        if severity == "LOW" and activity_score < 0.2:
            penalty += 0.05

        if event_type == "platform" and payload.activity.gps_valid is False:
            penalty += 0.05

        return round(min(0.2, penalty), 3)

    def _collect_external_signals(
        self,
        payload: FraudCheckRequest,
        *,
        token: str | None,
        request_id: str | None,
    ) -> dict[str, Any]:
        signals: dict[str, Any] = {
            "worker_profile": None,
            "risk_score": None,
        }

        if not token:
            return signals

        worker_profile = self.identity_client.get_worker_profile(
            user_id=str(payload.user_id),
            token=token,
            request_id=request_id,
        )
        signals["worker_profile"] = worker_profile

        if payload.event and payload.event.zone:
            risk_metrics = self._build_risk_metrics(payload)
            risk_score = self.ai_risk_client.evaluate_risk(
                zone=payload.event.zone,
                metrics=risk_metrics,
                token=token,
                request_id=request_id,
            )
            signals["risk_score"] = risk_score

        return signals

    def _build_risk_metrics(self, payload: FraudCheckRequest) -> dict[str, float]:
        severity_map = {
            "LOW": 0.33,
            "MEDIUM": 0.66,
            "HIGH": 1.0,
        }

        severity = "LOW"
        if payload.event and payload.event.severity:
            severity = payload.event.severity.upper()
        severity_score = severity_map.get(severity, 0.33)

        event_type = (payload.event.type or "").lower() if payload.event else ""
        return {
            "disruption_freq": severity_score,
            "duration": severity_score,
            "traffic": severity_score if event_type == "traffic" else 0.25,
            "order_drop": severity_score,
            "activity": max(0.0, min(1.0, 1.0 - payload.activity.activity_score)),
            "claims": min(1.0, self.repo.count_for_claim(payload.claim_id) / 5),
        }

    @staticmethod
    def _build_fail_event_payload(
        payload: FraudCheckRequest,
        score: float,
        reason: str | None,
        source: str,
    ) -> dict[str, Any]:
        return {
            "claim_id": str(payload.claim_id),
            "user_id": str(payload.user_id),
            "fraud_score": score,
            "reason": reason,
            "source": source,
        }
