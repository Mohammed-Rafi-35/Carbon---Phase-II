from __future__ import annotations

from celery import Celery

from app.core.config import get_settings


settings = get_settings()

celery_app = Celery(
    "notification_service",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url or "rpc://",
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_routes={
        "app.events.tasks.deliver_notification_task": {"queue": "notifications"},
    },
    task_default_retry_delay=30,
)
