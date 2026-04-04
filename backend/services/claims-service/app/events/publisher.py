from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

from kombu import Connection, Exchange, Producer, Queue

from app.core.config import get_settings


logger = logging.getLogger(__name__)


class ClaimsEventPublisher:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.exchange = Exchange(self.settings.claims_exchange_name, type="topic", durable=True)
        self.queue = Queue("claims.events", exchange=self.exchange, routing_key="claim.*", durable=True)

    def _publish(self, *, event_type: str, payload: dict, routing_key: str) -> None:
        if self.settings.app_env == "test":
            return

        message = {
            "event_type": event_type,
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
                    routing_key=routing_key,
                    declare=[self.queue],
                    serializer="json",
                    delivery_mode=2,
                    retry=True,
                )
        except Exception as exc:
            logger.warning("Failed to publish claim event %s: %s", event_type, exc)

    def publish_claim_initiated(self, payload: dict) -> None:
        self._publish(
            event_type="CLAIM_INITIATED",
            payload=payload,
            routing_key=self.settings.claim_initiated_routing_key,
        )

    def publish_claim_approved(self, payload: dict) -> None:
        self._publish(
            event_type="CLAIM_APPROVED",
            payload=payload,
            routing_key=self.settings.claim_approved_routing_key,
        )

    def publish_claim_processing(self, payload: dict) -> None:
        self._publish(
            event_type="CLAIM_PROCESSING",
            payload=payload,
            routing_key=self.settings.claim_processing_routing_key,
        )
