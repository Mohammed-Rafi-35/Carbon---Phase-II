from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import NotificationChannel, NotificationStatus
from app.core.exceptions import AppError
from app.events.publisher import publish_notification_delivery
from app.integrations.push_provider import PushProviderClient
from app.integrations.sms_provider import SMSProviderClient
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import NotificationHistoryItem, NotificationSendRequest
from app.services.metrics_service import metrics_service
from app.services.template_service import TemplateService


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.repository = NotificationRepository(db)
        self.template_service = TemplateService()
        self.sms_client = SMSProviderClient()
        self.push_client = PushProviderClient()

    def queue_notification(self, payload: NotificationSendRequest) -> list[UUID]:
        target_users = payload.user_ids if payload.user_ids else [payload.user_id]
        rendered_message = self.template_service.render(
            type_=payload.type,
            message=payload.message,
            template_name=payload.template_name,
            variables=payload.template_variables,
        )

        created_ids: list[UUID] = []
        for target in target_users:
            item = self.repository.create(
                user_id=target,
                channel=payload.channel,
                type_=payload.type,
                message=rendered_message,
                status=NotificationStatus.QUEUED,
            )
            publish_notification_delivery(item.id)
            metrics_service.queued()
            created_ids.append(item.id)

        return created_ids

    def list_notification_history(self, user_id: UUID) -> list[NotificationHistoryItem]:
        items = self.repository.list_for_user(user_id)
        return [
            NotificationHistoryItem(
                notification_id=item.id,
                type=item.type,
                status=item.status,
                timestamp=item.sent_at or item.created_at,
            )
            for item in items
        ]

    def retry_notification(self, notification_id: UUID) -> None:
        item = self.repository.get_by_id(notification_id)
        if not item:
            raise AppError("Notification not found.", "NOTIFICATION_NOT_FOUND", 404)

        if item.retry_count >= self.settings.max_retries:
            raise AppError("Maximum retries exceeded.", "MAX_RETRIES_EXCEEDED", 400)

        self.repository.mark_retry_scheduled(item)
        metrics_service.retried()
        metrics_service.queued()
        publish_notification_delivery(item.id, countdown=30)

    def deliver_notification(self, notification_id: UUID) -> None:
        item = self.repository.get_by_id(notification_id)
        if not item:
            return

        metrics_service.dequeued()

        try:
            if item.channel == NotificationChannel.SMS:
                self.sms_client.send_sms(user_id=str(item.user_id), message=item.message)
            elif item.channel == NotificationChannel.PUSH:
                self.push_client.send_push(user_id=str(item.user_id), message=item.message)
            elif item.channel == NotificationChannel.IN_APP:
                pass
            else:
                raise AppError("Unsupported notification channel.", "UNSUPPORTED_CHANNEL", 400)

            self.repository.mark_sent(item)
            metrics_service.sent()
        except Exception:
            if item.retry_count < self.settings.max_retries:
                self.repository.mark_retry_scheduled(item)
                metrics_service.retried()
                metrics_service.queued()
                publish_notification_delivery(item.id, countdown=30)
            else:
                self.repository.mark_failed(item)
                metrics_service.failed()

    def current_metrics(self) -> dict:
        m = metrics_service.snapshot()
        return {
            "delivery_success_rate": (m.sent_count / max(1, m.sent_count + m.failed_count)),
            "retry_count": m.retry_count,
            "queue_length": m.queue_depth,
        }
