from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from kombu import Connection, Exchange, Producer, Queue

from app.core.config import get_settings
from app.core.constants import TriggerEventName


logger = logging.getLogger(__name__)


class TriggerEventPublisher:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.exchange = Exchange(self.settings.trigger_exchange_name, type="topic", durable=True)
        self.queue = Queue(
            "trigger.events",
            exchange=self.exchange,
            routing_key=self.settings.trigger_routing_key,
            durable=True,
        )

    def publish_disruption_detected(self, payload: dict) -> None:
        if self.settings.app_env == "test":
            return

        event_payload = {
            "event_id": payload["event_id"],
            "zone": payload["zone"],
            "type": payload["type"],
            "severity": payload["severity"],
        }

        message = {
            "event": TriggerEventName.DISRUPTION_DETECTED.value,
            "event_type": TriggerEventName.DISRUPTION_DETECTED.value,
            "event_id": event_payload["event_id"],
            "zone": event_payload["zone"],
            "type": event_payload["type"],
            "severity": event_payload["severity"],
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "payload": event_payload,
        }

        try:
            with Connection(self.settings.rabbitmq_url) as connection:
                self.queue.maybe_bind(connection)
                self.queue.declare()
                producer = Producer(connection)
                producer.publish(
                    json.loads(json.dumps(message)),
                    exchange=self.exchange,
                    routing_key=self.settings.trigger_routing_key,
                    declare=[self.queue],
                    serializer="json",
                    delivery_mode=2,
                    retry=True,
                )
        except Exception as exc:
            logger.warning("Failed to publish disruption event: %s", exc)
