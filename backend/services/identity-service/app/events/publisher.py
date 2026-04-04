from __future__ import annotations

from typing import Any


class EventPublisher:
    """Placeholder event publisher to keep event emission concerns isolated."""

    def publish(self, event_name: str, payload: dict[str, Any]) -> None:
        _ = (event_name, payload)
