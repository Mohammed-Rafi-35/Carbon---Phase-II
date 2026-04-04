from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.aggregated_stat import AggregatedStat
from app.models.analytics_event import AnalyticsEvent
from app.models.analytics_metric import AnalyticsMetric


class AnalyticsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def event_key_exists(self, event_key: str) -> bool:
        stmt = select(AnalyticsEvent.id).where(AnalyticsEvent.event_key == event_key).limit(1)
        return self.db.execute(stmt).first() is not None

    def create_event(self, event: AnalyticsEvent) -> AnalyticsEvent:
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def create_metrics(self, metrics: list[AnalyticsMetric]) -> None:
        if not metrics:
            return
        self.db.add_all(metrics)
        self.db.commit()

    def increment_aggregated_stats(self, increments: dict[str, Decimal], *, as_of: datetime) -> None:
        if not increments:
            return

        for metric_name, delta in increments.items():
            stmt = select(AggregatedStat).where(AggregatedStat.metric_name == metric_name)
            row = self.db.execute(stmt).scalar_one_or_none()
            if row is None:
                row = AggregatedStat(metric_name=metric_name, value=delta, last_updated=as_of)
                self.db.add(row)
            else:
                row.value = Decimal(str(row.value)) + delta
                row.last_updated = as_of
                self.db.add(row)

        self.db.commit()
