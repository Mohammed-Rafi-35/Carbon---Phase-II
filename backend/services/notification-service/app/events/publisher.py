from __future__ import annotations

from uuid import UUID

from app.core.config import get_settings
from app.events.celery_app import celery_app


settings = get_settings()


def publish_notification_delivery(notification_id: UUID, countdown: int = 0) -> None:
    if settings.app_env == "test":
        return
    celery_app.send_task(
        "app.events.tasks.deliver_notification_task",
        args=[str(notification_id)],
        countdown=countdown,
    )
