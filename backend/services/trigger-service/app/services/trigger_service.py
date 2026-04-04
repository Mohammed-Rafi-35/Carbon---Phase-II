from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.constants import DisruptionSource
from app.core.exceptions import AppError
from app.events.publisher import TriggerEventPublisher
from app.repositories.disruption_repository import DisruptionRepository


class TriggerService:
    def __init__(self, db: Session, publisher: TriggerEventPublisher | None = None) -> None:
        self.repository = DisruptionRepository(db=db)
        self.publisher = publisher or TriggerEventPublisher()

    def create_manual_trigger(self, *, zone: str, disruption_type: str, severity: str):
        disruption = self.repository.create(
            zone=zone,
            disruption_type=disruption_type,
            severity=severity,
            source=DisruptionSource.MANUAL.value,
        )
        self._publish_disruption(disruption)
        return disruption

    def create_if_absent(self, *, zone: str, disruption_type: str, severity: str, source: str):
        existing = self.repository.get_active_by_zone_and_type(zone=zone, disruption_type=disruption_type)
        if existing:
            return None

        disruption = self.repository.create(
            zone=zone,
            disruption_type=disruption_type,
            severity=severity,
            source=source,
        )
        self._publish_disruption(disruption)
        return disruption

    def get_active_disruptions(self):
        return self.repository.list_active()

    def stop_trigger(self, *, event_id: str):
        disruption = self.repository.get_by_id(event_id=event_id)
        if not disruption:
            raise AppError("Event not found.", "EVENT_NOT_FOUND", 404)
        return self.repository.stop(disruption)

    def _publish_disruption(self, disruption) -> None:
        self.publisher.publish_disruption_detected(
            {
                "event_id": disruption.id,
                "zone": disruption.zone,
                "type": disruption.type,
                "severity": disruption.severity,
            }
        )
