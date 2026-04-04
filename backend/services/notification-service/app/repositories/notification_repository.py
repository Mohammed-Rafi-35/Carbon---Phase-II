from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, user_id: UUID, channel: str, type_: str, message: str, status: str) -> Notification:
        item = Notification(
            user_id=user_id,
            channel=channel,
            type=type_,
            message=message,
            status=status,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_by_id(self, notification_id: UUID) -> Notification | None:
        stmt = select(Notification).where(Notification.id == notification_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_user(self, user_id: UUID) -> list[Notification]:
        stmt = select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def mark_sent(self, item: Notification) -> Notification:
        item.status = "sent"
        item.sent_at = datetime.now(tz=timezone.utc)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def mark_failed(self, item: Notification) -> Notification:
        item.status = "failed"
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def mark_retry_scheduled(self, item: Notification) -> Notification:
        item.status = "retry_scheduled"
        item.retry_count += 1
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item
