from __future__ import annotations

from app.core.config import get_settings
from app.core.exceptions import AppError


class SMSProviderClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def send_sms(self, *, user_id: str, message: str) -> None:
        if not self.settings.sms_api_key:
            raise AppError("SMS provider API key is not configured.", "SMS_PROVIDER_NOT_CONFIGURED", 500)
        _ = user_id
        _ = message
