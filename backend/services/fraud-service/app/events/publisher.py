from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

from kombu import Connection, Exchange, Producer, Queue

from app.core.config import get_settings


logger = logging.getLogger(__name__)


class FraudEventPublisher:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.exchange = Exchange(self.settings.fraud_exchange_name, type="topic", durable=True)
        self.queue = Queue("fraud.events", exchange=self.exchange, routing_key="fraud.*", durable=True)

    def publish_fraud_detected(self, payload: dict) -> None:
        if self.settings.app_env == "test":
            return

        message = {
            "event_type": "FRAUD_DETECTED",
            "event_id": str(uuid4()),
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "payload": payload,
        }

        try:
            with Connection(self.settings.rabbitmq_url) as connection:
                self.queue.maybe_bind(connection)
                self.queue.declare()
                producer = Producer(connection)
                producer.publish(
                    json.loads(json.dumps(message)),
                    exchange=self.exchange,
                    routing_key=self.settings.fraud_detected_routing_key,
                    declare=[self.queue],
                    serializer="json",
                    delivery_mode=2,
                    retry=True,
                )
        except Exception as exc:
            logger.warning("Failed to publish fraud event: %s", exc)
