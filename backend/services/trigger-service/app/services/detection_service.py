from __future__ import annotations

import logging
from threading import Lock

from sqlalchemy import text

from app.core.config import get_settings
from app.core.constants import DisruptionSource
from app.db.session import SessionLocal
from app.integrations.external_sources import ExternalSourceGateway
from app.services.trigger_service import TriggerService


logger = logging.getLogger(__name__)
_LOCAL_SCHEDULER_LOCK = Lock()


def _classify_with_threshold(value: float, threshold: float) -> str | None:
    if value >= threshold * 1.5:
        return "HIGH"
    if value >= threshold:
        return "MEDIUM"
    return None


class DetectionService:
    def __init__(self, trigger_service: TriggerService, source_gateway: ExternalSourceGateway) -> None:
        self.settings = get_settings()
        self.trigger_service = trigger_service
        self.source_gateway = source_gateway

    def poll_sources(self, zones: list[str]) -> int:
        created_events = 0

        for zone in zones:
            snapshot = self.source_gateway.fetch_zone_snapshot(zone)

            weather_severity = _classify_with_threshold(snapshot.rain_mm, self.settings.threshold_rain)
            if weather_severity:
                created = self.trigger_service.create_if_absent(
                    zone=zone,
                    disruption_type="weather",
                    severity=weather_severity,
                    source=DisruptionSource.WEATHER.value,
                )
                created_events += 1 if created else 0

            traffic_severity = _classify_with_threshold(snapshot.congestion_ratio, self.settings.threshold_traffic)
            if traffic_severity:
                created = self.trigger_service.create_if_absent(
                    zone=zone,
                    disruption_type="traffic",
                    severity=traffic_severity,
                    source=DisruptionSource.TRAFFIC.value,
                )
                created_events += 1 if created else 0

            platform_severity = None
            if snapshot.outage_ratio >= self.settings.threshold_platform_outage:
                platform_severity = "HIGH"
            elif snapshot.platform_outage:
                platform_severity = "MEDIUM"

            if platform_severity:
                created = self.trigger_service.create_if_absent(
                    zone=zone,
                    disruption_type="platform",
                    severity=platform_severity,
                    source=DisruptionSource.PLATFORM.value,
                )
                created_events += 1 if created else 0

        return created_events


def _acquire_scheduler_lock(db) -> tuple[bool, str]:
    settings = get_settings()
    backend_name = db.bind.dialect.name if db.bind is not None else ""
    if backend_name.startswith("postgres"):
        acquired = bool(
            db.execute(
                text("SELECT pg_try_advisory_lock(:key)"),
                {"key": settings.scheduler_lock_key},
            ).scalar()
        )
        return acquired, "postgres"
    return _LOCAL_SCHEDULER_LOCK.acquire(blocking=False), "local"


def _release_scheduler_lock(db, mode: str) -> None:
    settings = get_settings()
    if mode == "postgres":
        db.execute(
            text("SELECT pg_advisory_unlock(:key)"),
            {"key": settings.scheduler_lock_key},
        )
        return
    if _LOCAL_SCHEDULER_LOCK.locked():
        _LOCAL_SCHEDULER_LOCK.release()


def run_detection_cycle() -> None:
    settings = get_settings()

    db = SessionLocal()
    lock_mode = "local"
    lock_acquired = False
    try:
        lock_acquired, lock_mode = _acquire_scheduler_lock(db)
        if not lock_acquired:
            logger.info("detection cycle skipped: lock not acquired")
            return

        service = TriggerService(db=db)
        detection = DetectionService(trigger_service=service, source_gateway=ExternalSourceGateway())
        created = detection.poll_sources(zones=settings.poll_zones)
        if created:
            logger.info("detection cycle completed: created_events=%s", created)
    except Exception as exc:
        logger.exception("detection cycle failed: %s", exc)
    finally:
        if lock_acquired:
            _release_scheduler_lock(db, lock_mode)
        db.close()
