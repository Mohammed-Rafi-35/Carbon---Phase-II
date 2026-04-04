from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import COVERAGE_RATE_MAP, PolicyStatus
from app.core.exceptions import AppError
from app.events.publisher import publish_policy_event
from app.integrations.ai_risk_client import AIRiskServiceClient
from app.integrations.fraud_client import FraudServiceClient
from app.integrations.identity_client import IdentityServiceClient
from app.models.policy import Policy
from app.repositories.policy_log_repository import PolicyLogRepository
from app.repositories.policy_repository import PolicyRepository
from app.schemas.policy import CreatePolicyRequest, PolicyResponseData, ValidatePolicyData
from app.services.pricing_service import PricingService


class PolicyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.policy_repo = PolicyRepository(db)
        self.log_repo = PolicyLogRepository(db)
        self.pricing_service = PricingService()
        self.identity_client = IdentityServiceClient()
        self.fraud_client = FraudServiceClient()
        self.ai_risk_client = AIRiskServiceClient()

    def _resolve_zone_and_activity(self, payload: CreatePolicyRequest, token: str, request_id: str) -> tuple[str, int]:
        zone = payload.zone
        activity_days = payload.activity_days if payload.activity_days is not None else 0

        if zone is not None and payload.activity_days is not None:
            return zone, activity_days

        profile = self.identity_client.get_worker_profile(str(payload.user_id), token=token, request_id=request_id)
        profile_data = profile.get("data", {}) if isinstance(profile, dict) else {}

        resolved_zone = zone or profile_data.get("zone")
        if not resolved_zone:
            raise AppError("Unable to resolve worker zone.", "IDENTITY_DATA_MISSING", 502)

        resolved_activity = activity_days
        if payload.activity_days is None:
            resolved_activity = int(profile_data.get("activity_days", 0))

        return resolved_zone, resolved_activity

    @staticmethod
    def _daily_income(weekly_income: Decimal) -> Decimal:
        return (weekly_income / Decimal("7")).quantize(Decimal("0.01"))

    @staticmethod
    def _as_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def _to_response(self, policy: Policy) -> PolicyResponseData:
        return PolicyResponseData(
            policy_id=policy.id,
            user_id=policy.user_id,
            premium=policy.total_premium,
            start_date=policy.created_at,
            iwi=policy.insured_weekly_income,
            idi=policy.insured_daily_income,
            zone=policy.zone,
            coverage_rate=policy.coverage_rate,
            base_premium=policy.base_premium,
            stabilization_factor=policy.stabilization_factor,
            gst=policy.gst,
            total_premium=policy.total_premium,
            waiting_period_end=policy.waiting_period_end,
            status=policy.status,
            activity_days=policy.activity_days,
        )

    def create_policy(self, payload: CreatePolicyRequest, token: str, request_id: str) -> PolicyResponseData:
        zone, activity_days = self._resolve_zone_and_activity(payload, token=token, request_id=request_id)
        risk_multiplier = self.ai_risk_client.get_premium_multiplier(zone=zone, token=token, request_id=request_id)

        premium = self.pricing_service.calculate(
            weekly_income=payload.weekly_income,
            zone=zone,
            policy_week=payload.policy_week,
            risk_multiplier=risk_multiplier,
        )

        waiting_period_end = datetime.now(tz=timezone.utc) + timedelta(hours=self.settings.waiting_period_hours)
        policy = self.policy_repo.create(
            user_id=payload.user_id,
            zone=zone,
            status=PolicyStatus.WAITING_PERIOD,
            insured_weekly_income=payload.weekly_income,
            insured_daily_income=self._daily_income(payload.weekly_income),
            coverage_rate=COVERAGE_RATE_MAP[zone],
            base_premium=premium.base_premium,
            gst=premium.gst,
            total_premium=premium.total_premium,
            stabilization_factor=premium.stabilization_factor,
            waiting_period_end=waiting_period_end,
            activity_days=activity_days,
            premium_paid=payload.premium_paid,
        )
        self.log_repo.create(policy_id=policy.id, status=policy.status, reason="Policy created")
        publish_policy_event(
            "POLICY_CREATED",
            {
                "policy_id": str(policy.id),
                "user_id": str(policy.user_id),
                "status": policy.status,
                "zone": policy.zone,
                "total_premium": float(policy.total_premium),
            },
        )
        return self._to_response(policy)

    def get_policy_by_user(self, user_id: UUID) -> PolicyResponseData:
        policy = self.policy_repo.get_latest_by_user(user_id)
        if not policy:
            raise AppError("Policy not found.", "POLICY_NOT_FOUND", 404)

        self._refresh_status_if_eligible(policy)
        return self._to_response(policy)

    def _refresh_status_if_eligible(self, policy: Policy) -> None:
        waiting_period_end = self._as_utc(policy.waiting_period_end)
        if (
            policy.status == PolicyStatus.WAITING_PERIOD
            and policy.premium_paid
            and datetime.now(tz=timezone.utc) >= waiting_period_end
        ):
            policy.status = PolicyStatus.ACTIVE
            self.policy_repo.save(policy)
            self.log_repo.create(policy_id=policy.id, status=policy.status, reason="Waiting period completed")

    def validate_policy(self, user_id: UUID, policy_id: UUID, token: str, request_id: str) -> ValidatePolicyData:
        policy = self.policy_repo.get_by_id(policy_id)
        if not policy or policy.user_id != user_id:
            raise AppError("Policy not found.", "POLICY_NOT_FOUND", 404)

        self._refresh_status_if_eligible(policy)

        if policy.activity_days < 3:
            return ValidatePolicyData(valid=False, reason="Insufficient activity days in last 7 days")

        waiting_period_end = self._as_utc(policy.waiting_period_end)
        if datetime.now(tz=timezone.utc) < waiting_period_end:
            return ValidatePolicyData(valid=False, reason="Waiting period has not completed")

        is_fraudulent = self.fraud_client.is_user_flagged(
            user_id=str(user_id),
            policy_id=str(policy_id),
            token=token,
            request_id=request_id,
        )
        if is_fraudulent:
            return ValidatePolicyData(valid=False, reason="Fraud flag detected")

        if not policy.premium_paid:
            return ValidatePolicyData(valid=False, reason="Premium is not paid")

        if policy.status not in {PolicyStatus.ACTIVE, PolicyStatus.WAITING_PERIOD}:
            return ValidatePolicyData(valid=False, reason="Policy is not active")

        if policy.status == PolicyStatus.WAITING_PERIOD:
            policy.status = PolicyStatus.ACTIVE
            self.policy_repo.save(policy)
            self.log_repo.create(policy_id=policy.id, status=policy.status, reason="Policy validated and activated")

        return ValidatePolicyData(valid=True, reason=None)