from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import and_, distinct, func, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import EventType, RiskLevel, TimeSeriesMetric
from app.core.exceptions import AppError
from app.models.analytics_event import AnalyticsEvent
from app.services.cache_service import analytics_cache


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    def get_dashboard(self, *, start_date: datetime | None, end_date: datetime | None) -> dict:
        start, end = self._normalize_window(start_date=start_date, end_date=end_date, default_days=None)
        cache_key = f"dashboard:{start.isoformat()}:{end.isoformat()}"
        cached = analytics_cache.get(cache_key)
        if cached is not None:
            return cached

        filters = [AnalyticsEvent.event_timestamp >= start, AnalyticsEvent.event_timestamp <= end]

        total_claims = self._count_events(EventType.CLAIM_INITIATED, filters)
        approved_claims = self._count_events(EventType.CLAIM_APPROVED, filters)
        active_policies = self._count_events(EventType.POLICY_CREATED, filters)
        fraud_detected = self._count_events(EventType.FRAUD_DETECTED, filters)
        payout_transactions = self._count_events(EventType.PAYOUT_COMPLETED, filters)
        service_event_volume = self._count_all(filters)

        total_payout_stmt = (
            select(func.coalesce(func.sum(AnalyticsEvent.amount), 0))
            .where(*filters)
            .where(AnalyticsEvent.event_type == EventType.PAYOUT_COMPLETED)
        )
        total_payout = float(Decimal(str(self.db.execute(total_payout_stmt).scalar_one())))

        active_users_stmt = (
            select(func.count(distinct(AnalyticsEvent.user_id)))
            .where(*filters)
            .where(AnalyticsEvent.user_id.is_not(None))
        )
        active_users = int(self.db.execute(active_users_stmt).scalar_one())

        active_sessions_stmt = (
            select(func.count(distinct(AnalyticsEvent.user_id)))
            .where(AnalyticsEvent.event_timestamp >= datetime.now(tz=timezone.utc) - timedelta(hours=1))
            .where(AnalyticsEvent.user_id.is_not(None))
        )
        active_sessions_last_hour = int(self.db.execute(active_sessions_stmt).scalar_one())

        risk_distribution = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 0,
            RiskLevel.HIGH: 0,
        }
        risk_stmt = (
            select(AnalyticsEvent.risk_category, func.count())
            .where(*filters)
            .where(AnalyticsEvent.event_type == EventType.DISRUPTION_DETECTED)
            .group_by(AnalyticsEvent.risk_category)
        )
        for category, count in self.db.execute(risk_stmt).all():
            key = str(category or "").upper()
            if key in risk_distribution:
                risk_distribution[key] = int(count)

        claims_rate = round((approved_claims / total_claims), 4) if total_claims else 0.0

        top_impacted_zones = self._top_impacted_zones(start=start, end=end, limit=5)

        response = {
            "active_users": active_users,
            "active_sessions_last_hour": active_sessions_last_hour,
            "active_policies": active_policies,
            "total_claims": total_claims,
            "approved_claims": approved_claims,
            "claims_rate": claims_rate,
            "total_payout": round(total_payout, 2),
            "payout_transactions": payout_transactions,
            "fraud_detected": fraud_detected,
            "service_event_volume": service_event_volume,
            "risk_distribution": risk_distribution,
            "top_impacted_zones": top_impacted_zones,
            "window_start": start,
            "window_end": end,
        }
        ttl = self.settings.dashboard_cache_ttl_seconds or self.settings.cache_ttl_seconds
        analytics_cache.set(cache_key, response, ttl)
        return response

    def get_zone_analytics(self, *, lookback_days: int) -> list[dict]:
        start = datetime.now(tz=timezone.utc) - timedelta(days=lookback_days)
        end = datetime.now(tz=timezone.utc)
        cache_key = f"zones:{lookback_days}:{start.date().isoformat()}"
        cached = analytics_cache.get(cache_key)
        if cached is not None:
            return cached

        result = self._zone_analytics_in_window(start=start, end=end)
        result.sort(key=lambda item: (item["payout"], item["claims"], item["zone"]), reverse=True)
        ttl = self.settings.zones_cache_ttl_seconds or self.settings.cache_ttl_seconds
        analytics_cache.set(cache_key, result, ttl)
        return result

    def _zone_analytics_in_window(self, *, start: datetime, end: datetime) -> list[dict]:
        zone_data: dict[str, dict] = defaultdict(
            lambda: {
                "claims": 0,
                "payout": 0.0,
                "disruptions": 0,
                "fraud_flags": 0,
                "active_users": set(),
                "risk_low": 0,
                "risk_medium": 0,
                "risk_high": 0,
            }
        )

        event_rows = self.db.execute(
            select(
                AnalyticsEvent.zone,
                AnalyticsEvent.event_type,
                AnalyticsEvent.amount,
                AnalyticsEvent.user_id,
                AnalyticsEvent.risk_category,
            )
            .where(AnalyticsEvent.event_timestamp >= start)
            .where(AnalyticsEvent.event_timestamp <= end)
            .where(AnalyticsEvent.zone.is_not(None))
        ).all()

        for zone, event_type, amount, user_id, risk_category in event_rows:
            zone_key = str(zone)
            row = zone_data[zone_key]

            if user_id:
                row["active_users"].add(str(user_id))

            if event_type == EventType.CLAIM_INITIATED:
                row["claims"] += 1
            elif event_type == EventType.PAYOUT_COMPLETED:
                row["payout"] += float(amount or 0)
            elif event_type == EventType.DISRUPTION_DETECTED:
                row["disruptions"] += 1
                risk = str(risk_category or "").upper()
                if risk == RiskLevel.HIGH:
                    row["risk_high"] += 1
                elif risk == RiskLevel.MEDIUM:
                    row["risk_medium"] += 1
                else:
                    row["risk_low"] += 1
            elif event_type == EventType.FRAUD_DETECTED:
                row["fraud_flags"] += 1

        result: list[dict] = []
        for zone, row in zone_data.items():
            risk_level = self._resolve_zone_risk_level(
                low=row["risk_low"],
                medium=row["risk_medium"],
                high=row["risk_high"],
            )
            result.append(
                {
                    "zone": zone,
                    "risk_level": risk_level,
                    "claims": row["claims"],
                    "payout": round(row["payout"], 2),
                    "disruptions": row["disruptions"],
                    "fraud_flags": row["fraud_flags"],
                    "active_users": len(row["active_users"]),
                }
            )
        return result

    def get_timeseries(
        self,
        *,
        metric_type: str,
        interval: str,
        start_date: datetime | None,
        end_date: datetime | None,
    ) -> dict:
        metric = metric_type.strip().lower()
        valid_metrics = {item.value for item in TimeSeriesMetric}
        if metric not in valid_metrics:
            raise AppError("Unsupported metric_type.", "INVALID_METRIC_TYPE", 400)

        bucket_interval = interval.strip().lower()
        if bucket_interval not in {"day", "hour"}:
            raise AppError("Supported interval values: day, hour.", "INVALID_INTERVAL", 400)

        start, end = self._normalize_window(
            start_date=start_date,
            end_date=end_date,
            default_days=self.settings.default_lookback_days,
        )
        cache_key = f"timeseries:{metric}:{bucket_interval}:{start.isoformat()}:{end.isoformat()}"
        cached = analytics_cache.get(cache_key)
        if cached is not None:
            return cached

        points: dict[datetime, float] = defaultdict(float)

        if metric == TimeSeriesMetric.ACTIVE_USERS:
            user_buckets: dict[datetime, set[str]] = defaultdict(set)
            rows = self.db.execute(
                select(AnalyticsEvent.event_timestamp, AnalyticsEvent.user_id)
                .where(AnalyticsEvent.event_timestamp >= start)
                .where(AnalyticsEvent.event_timestamp <= end)
                .where(AnalyticsEvent.user_id.is_not(None))
            ).all()
            for timestamp, user_id in rows:
                bucket = self._bucket_time(_as_utc(timestamp), bucket_interval)
                user_buckets[bucket].add(str(user_id))
            for bucket, users in user_buckets.items():
                points[bucket] = float(len(users))
        else:
            event_types = self._metric_event_types(metric)
            rows = self.db.execute(
                select(AnalyticsEvent.event_timestamp, AnalyticsEvent.amount, AnalyticsEvent.event_type)
                .where(AnalyticsEvent.event_timestamp >= start)
                .where(AnalyticsEvent.event_timestamp <= end)
                .where(AnalyticsEvent.event_type.in_(event_types))
            ).all()

            for timestamp, amount, event_type in rows:
                bucket = self._bucket_time(_as_utc(timestamp), bucket_interval)
                points[bucket] += self._event_value(metric=metric, event_type=str(event_type), amount=amount)

        formatted_points: list[dict] = []
        cursor = self._bucket_time(start, bucket_interval)
        terminal = self._bucket_time(end, bucket_interval)
        step = timedelta(hours=1) if bucket_interval == "hour" else timedelta(days=1)
        while cursor <= terminal:
            formatted_points.append({"timestamp": cursor, "value": round(points.get(cursor, 0.0), 4)})
            cursor += step

        response = {
            "metric_type": metric,
            "interval": bucket_interval,
            "points": formatted_points,
        }
        ttl = self.settings.timeseries_cache_ttl_seconds or self.settings.cache_ttl_seconds
        analytics_cache.set(cache_key, response, ttl)
        return response

    def get_admin_health(self) -> dict:
        total_events_stmt = select(func.count()).select_from(AnalyticsEvent)
        total_events = int(self.db.execute(total_events_stmt).scalar_one())

        latest_event_stmt = select(func.max(AnalyticsEvent.event_timestamp))
        latest_event = self.db.execute(latest_event_stmt).scalar_one()

        db_status = "healthy"
        try:
            self.db.execute(text("SELECT 1"))
        except Exception:
            db_status = "degraded"

        return {
            "status": "healthy",
            "db_status": db_status,
            "event_consumer_enabled": self.settings.enable_event_consumer,
            "events_ingested": total_events,
            "last_event_at": latest_event,
        }

    def _normalize_window(
        self,
        *,
        start_date: datetime | None,
        end_date: datetime | None,
        default_days: int | None,
    ) -> tuple[datetime, datetime]:
        end = _as_utc(end_date) if end_date is not None else datetime.now(tz=timezone.utc)

        if start_date is not None:
            start = _as_utc(start_date)
        elif default_days is not None:
            start = end - timedelta(days=default_days)
        else:
            min_ts_stmt = select(func.min(AnalyticsEvent.event_timestamp))
            min_ts = self.db.execute(min_ts_stmt).scalar_one()
            start = _as_utc(min_ts) if min_ts is not None else end - timedelta(days=self.settings.default_lookback_days)

        if start > end:
            raise AppError("start_date must be less than or equal to end_date.", "INVALID_DATE_RANGE", 400)
        return start, end

    def _count_events(self, event_type: str, filters: list) -> int:
        stmt = (
            select(func.count())
            .select_from(AnalyticsEvent)
            .where(and_(*filters))
            .where(AnalyticsEvent.event_type == event_type)
        )
        return int(self.db.execute(stmt).scalar_one())

    def _count_all(self, filters: list) -> int:
        stmt = select(func.count()).select_from(AnalyticsEvent).where(and_(*filters))
        return int(self.db.execute(stmt).scalar_one())

    def _top_impacted_zones(self, *, start: datetime, end: datetime, limit: int) -> list[dict]:
        rows = self._zone_analytics_in_window(start=start, end=end)
        rows.sort(key=lambda item: (item["payout"], item["claims"], item["zone"]), reverse=True)
        return rows[:limit]

    @staticmethod
    def _resolve_zone_risk_level(*, low: int, medium: int, high: int) -> str:
        total = low + medium + high
        if total == 0:
            return RiskLevel.LOW

        score = (low * 1.0 + medium * 2.0 + high * 3.0) / total
        if score >= 2.3:
            return RiskLevel.HIGH
        if score >= 1.6:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    @staticmethod
    def _bucket_time(timestamp: datetime, interval: str) -> datetime:
        if interval == "hour":
            return timestamp.replace(minute=0, second=0, microsecond=0)
        return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def _metric_event_types(metric: str) -> list[str]:
        if metric == TimeSeriesMetric.CLAIMS:
            return [EventType.CLAIM_INITIATED]
        if metric == TimeSeriesMetric.PAYOUT:
            return [EventType.PAYOUT_COMPLETED]
        if metric == TimeSeriesMetric.FRAUD:
            return [EventType.FRAUD_DETECTED]
        if metric == TimeSeriesMetric.POLICY:
            return [EventType.POLICY_CREATED]
        return [EventType.DISRUPTION_DETECTED]

    @staticmethod
    def _event_value(*, metric: str, event_type: str, amount: Decimal | None) -> float:
        if metric == TimeSeriesMetric.PAYOUT and event_type == EventType.PAYOUT_COMPLETED:
            return float(amount or 0)
        return 1.0
