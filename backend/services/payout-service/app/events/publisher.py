from __future__ import annotations

import json
import logging

from kombu import Connection, Exchange, Producer

from app.core.config import get_settings


logger = logging.getLogger(__name__)


def publish_payout_event(event_type: str, payload: dict) -> None:
    settings = get_settings()

    logger.info(
        "payout_event",
        extra={
            "event_type": event_type,
            "payload": payload,
        },
    )

    if not settings.enable_event_publish:
        return

    exchange = Exchange("devtrails.events", type="topic", durable=True)
    routing_key = (
        settings.payout_completed_event_routing_key
        if event_type == "PAYOUT_COMPLETED"
        else settings.payout_failed_event_routing_key
    )

    with Connection(settings.rabbitmq_url) as conn:
        producer = Producer(conn)
        producer.publish(
            {
                "event_type": event_type,
                "payload": payload,
            },
            serializer="json",
            exchange=exchange,
            routing_key=routing_key,
            declare=[exchange],
            delivery_mode=2,
            retry=True,
        )

    logger.info(
        "payout_event_published",
        extra={
            "event_type": event_type,
            "routing_key": routing_key,
            "payload": json.dumps(payload),
        },
    )
