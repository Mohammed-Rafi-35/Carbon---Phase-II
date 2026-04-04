from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.core.constants import NotificationChannel, NotificationType


class NotificationSendRequest(BaseModel):
    user_id: UUID | None = None
    user_ids: list[UUID] | None = None
    channel: NotificationChannel
    type: NotificationType
    message: str | None = Field(default=None, min_length=1)
    template_name: str | None = None
    template_variables: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_targets_and_message(self) -> "NotificationSendRequest":
        if not self.user_id and not self.user_ids:
            raise ValueError("Either user_id or user_ids must be provided.")
        if self.user_id and self.user_ids:
            raise ValueError("Provide either user_id or user_ids, not both.")
        if not self.message and not self.template_name:
            raise ValueError("Either message or template_name must be provided.")
        return self


class NotificationRetryRequest(BaseModel):
    notification_id: UUID


class NotificationQueuedData(BaseModel):
    notification_id: UUID | None = None
    notification_ids: list[UUID] | None = None
    status: str


class NotificationHistoryItem(BaseModel):
    notification_id: UUID
    type: str
    status: str
    timestamp: datetime
