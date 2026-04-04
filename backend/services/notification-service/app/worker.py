from app.events.celery_app import celery_app
from app.events import tasks  # noqa: F401

__all__ = ["celery_app"]
