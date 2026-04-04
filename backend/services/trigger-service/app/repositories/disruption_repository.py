from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import DisruptionStatus
from app.models.disruption import Disruption


class DisruptionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        zone: str,
        disruption_type: str,
        severity: str,
        source: str,
        start_time: datetime | None = None,
    ) -> Disruption:
        disruption = Disruption(
            zone=zone,
            type=disruption_type,
            severity=severity,
            status=DisruptionStatus.ACTIVE.value,
            source=source,
            start_time=start_time or datetime.now(tz=timezone.utc),
        )
        self.db.add(disruption)
        self.db.commit()
        self.db.refresh(disruption)
        return disruption

    def get_by_id(self, event_id: str) -> Disruption | None:
        return self.db.get(Disruption, event_id)

    def list_active(self) -> list[Disruption]:
        stmt = (
            select(Disruption)
            .where(Disruption.status == DisruptionStatus.ACTIVE.value)
            .order_by(Disruption.start_time.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_active_by_zone_and_type(self, *, zone: str, disruption_type: str) -> Disruption | None:
        stmt = (
            select(Disruption)
            .where(
                Disruption.zone == zone,
                Disruption.type == disruption_type,
                Disruption.status == DisruptionStatus.ACTIVE.value,
            )
            .limit(1)
        )
        return self.db.scalars(stmt).one_or_none()

    def stop(self, disruption: Disruption) -> Disruption:
        disruption.status = DisruptionStatus.STOPPED.value
        disruption.end_time = datetime.now(tz=timezone.utc)
        self.db.add(disruption)
        self.db.commit()
        self.db.refresh(disruption)
        return disruption
