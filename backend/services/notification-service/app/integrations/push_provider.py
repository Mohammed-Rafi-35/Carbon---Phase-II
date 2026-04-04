from __future__ import annotations

from app.core.config import get_settings
from app.core.exceptions import AppError


class PushProviderClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def send_push(self, *, user_id: str, message: str) -> None:
        if not self.settings.push_api_key:
            raise AppError("Push provider API key is not configured.", "PUSH_PROVIDER_NOT_CONFIGURED", 500)
        _ = user_id
        _ = message
