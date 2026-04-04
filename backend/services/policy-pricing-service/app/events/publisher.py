from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from kombu import Connection, Exchange, Producer, Queue

from app.core.config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()

exchange = Exchange("devtrails.events", type="topic", durable=True)
queue = Queue("policy.events", exchange=exchange, routing_key="policy.*", durable=True)


def publish_policy_event(event_type: str, payload: dict) -> None:
    if settings.app_env == "test":
        return

    message = {
        "event_type": event_type,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "payload": payload,
    }

    try:
        with Connection(settings.rabbitmq_url) as connection:
            queue.maybe_bind(connection)
            queue.declare()
            producer = Producer(connection)
            producer.publish(
                json.loads(json.dumps(message)),
                exchange=exchange,
                routing_key=f"policy.{event_type.lower()}",
                declare=[queue],
                serializer="json",
                delivery_mode=2,
                retry=True,
            )
    except Exception as exc:
        logger.warning("Failed to publish policy event %s: %s", event_type, exc)