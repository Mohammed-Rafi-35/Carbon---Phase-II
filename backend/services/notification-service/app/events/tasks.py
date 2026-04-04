from __future__ import annotations

from uuid import UUID

from app.db.session import SessionLocal
from app.events.celery_app import celery_app
from app.services.notification_service import NotificationService


@celery_app.task(name="app.events.tasks.deliver_notification_task")
def deliver_notification_task(notification_id: str) -> None:
    db = SessionLocal()
    try:
        service = NotificationService(db)
        service.deliver_notification(UUID(notification_id))
    finally:
        db.close()
