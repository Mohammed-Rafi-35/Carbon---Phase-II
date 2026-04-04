from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.constants import EventType, RiskLevel
from app.models.analytics_event import AnalyticsEvent
from app.models.analytics_metric import AnalyticsMetric
from app.repositories.analytics_repository import AnalyticsRepository
from app.services.cache_service import analytics_cache


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    if isinstance(value, str) and value:
        text = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            return _now_utc()

    return _now_utc()


def _to_decimal(value: Any, default: str = "0") -> Decimal:
    try:
        if value is None:
            return Decimal(default)
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


class AnalyticsIngestionService:
    def __init__(self, db: Session, repository: AnalyticsRepository | None = None) -> None:
        self.db = db
        self.repository = repository or AnalyticsRepository(db)

    def process_event(self, body: dict[str, Any], routing_key: str | None = None) -> bool:
        raw_payload = body.get("payload", body)
        payload = raw_payload if isinstance(raw_payload, dict) else {"raw_payload": raw_payload}

        event_type = str(body.get("event_type", body.get("event", ""))).upper()
        if not event_type:
            return False

        event_timestamp = _parse_datetime(body.get("timestamp") or payload.get("timestamp"))
        event_id = self._as_string(body.get("event_id") or payload.get("event_id"))
        zone = self._as_string(payload.get("zone") or body.get("zone"))
        user_id = self._as_string(payload.get("user_id") or body.get("user_id"))
        amount = self._extract_amount(payload, event_type)
        status = self._as_string(payload.get("status") or payload.get("severity"))
        risk_category = self._extract_risk_category(payload, event_type)

        event_key = self._build_event_key(
            event_type=event_type,
            event_id=event_id,
            timestamp=event_timestamp,
            payload=payload,
        )

        if self.repository.event_key_exists(event_key):
            return False

        event = AnalyticsEvent(
            event_key=event_key,
            event_id=event_id,
            event_type=event_type,
            routing_key=routing_key,
            zone=zone,
            user_id=user_id,
            amount=amount,
            status=status,
            risk_category=risk_category,
            event_timestamp=event_timestamp,
            payload=json.loads(json.dumps(payload, default=str)),
        )

        try:
            self.repository.create_event(event)
        except IntegrityError:
            self.db.rollback()
            return False

        metrics, increments = self._derive_metrics(
            event_type=event_type,
            event_timestamp=event_timestamp,
            zone=zone,
            amount=amount,
            status=status,
            risk_category=risk_category,
            payload=payload,
        )

        self.repository.create_metrics(metrics)
        self.repository.increment_aggregated_stats(increments, as_of=event_timestamp)
        analytics_cache.clear()
        return True

    @staticmethod
    def _as_string(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _extract_amount(self, payload: dict[str, Any], event_type: str) -> Decimal | None:
        if event_type == EventType.PAYOUT_COMPLETED:
            return _to_decimal(payload.get("amount"), default="0")
        if event_type == EventType.CLAIM_APPROVED:
            return _to_decimal(payload.get("amount"), default="0")
        if event_type == EventType.POLICY_CREATED:
            return _to_decimal(payload.get("total_premium"), default="0")
        return None

    def _extract_risk_category(self, payload: dict[str, Any], event_type: str) -> str | None:
        risk_category = self._as_string(payload.get("risk_category"))
        if risk_category:
            return risk_category.upper()

        if event_type == EventType.DISRUPTION_DETECTED:
            severity = self._as_string(payload.get("severity"))
            return self._severity_to_risk(severity)
        return None

    @staticmethod
    def _severity_to_risk(severity: str | None) -> str | None:
        if not severity:
            return None
        value = severity.upper()
        if value == RiskLevel.HIGH:
            return RiskLevel.HIGH
        if value == RiskLevel.MEDIUM:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    @staticmethod
    def _build_event_key(*, event_type: str, event_id: str | None, timestamp: datetime, payload: dict[str, Any]) -> str:
        if event_id:
            return f"{event_type}:{event_id}"

        digest_source = json.dumps(
            {
                "event_type": event_type,
                "timestamp": timestamp.isoformat(),
                "payload": payload,
            },
            sort_keys=True,
            default=str,
        )
        digest = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()
        return f"{event_type}:{digest}"

    def _derive_metrics(
        self,
        *,
        event_type: str,
        event_timestamp: datetime,
        zone: str | None,
        amount: Decimal | None,
        status: str | None,
        risk_category: str | None,
        payload: dict[str, Any],
    ) -> tuple[list[AnalyticsMetric], dict[str, Decimal]]:
        metrics: list[AnalyticsMetric] = []
        increments: dict[str, Decimal] = {}

        def add_metric(metric_type: str, value: Decimal, metric_zone: str | None = None) -> None:
            metrics.append(
                AnalyticsMetric(
                    metric_type=metric_type,
                    value=value,
                    timestamp=event_timestamp,
                    zone=metric_zone,
                )
            )
            increments[metric_type] = increments.get(metric_type, Decimal("0")) + value

        add_metric("event_volume_total", Decimal("1"))
        if zone:
            add_metric("zone_event_count", Decimal("1"), metric_zone=zone)

        if event_type == EventType.CLAIM_INITIATED:
            add_metric("claims_total", Decimal("1"), metric_zone=zone)

        if event_type == EventType.CLAIM_APPROVED:
            add_metric("claims_approved", Decimal("1"), metric_zone=zone)
            if amount is not None:
                add_metric("claims_approved_amount", amount, metric_zone=zone)

        if event_type == EventType.PAYOUT_COMPLETED:
            add_metric("payout_total_count", Decimal("1"), metric_zone=zone)
            if amount is not None:
                add_metric("payout_total_amount", amount, metric_zone=zone)

        if event_type == EventType.FRAUD_DETECTED:
            add_metric("fraud_detected_count", Decimal("1"), metric_zone=zone)

        if event_type == EventType.POLICY_CREATED:
            add_metric("policy_created_count", Decimal("1"), metric_zone=zone)
            premium = _to_decimal(payload.get("total_premium"), default="0")
            add_metric("policy_premium_total", premium, metric_zone=zone)

        if event_type == EventType.DISRUPTION_DETECTED:
            add_metric("disruption_total_count", Decimal("1"), metric_zone=zone)

            resolved_risk = risk_category or self._severity_to_risk(status)
            if resolved_risk == RiskLevel.HIGH:
                add_metric("risk_high_count", Decimal("1"), metric_zone=zone)
            elif resolved_risk == RiskLevel.MEDIUM:
                add_metric("risk_medium_count", Decimal("1"), metric_zone=zone)
            elif resolved_risk == RiskLevel.LOW:
                add_metric("risk_low_count", Decimal("1"), metric_zone=zone)

        return metrics, increments
