from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from kombu import Connection, Exchange, Producer, Queue


class EventProducer:
	def __init__(
		self,
		*,
		rabbitmq_url: str,
		exchange_name: str = "devtrails.events",
		exchange_type: str = "topic",
	) -> None:
		self.rabbitmq_url = rabbitmq_url
		self.exchange = Exchange(exchange_name, type=exchange_type, durable=True)

	def build_message(self, *, event_type: str, payload: dict[str, Any], event_id: str | None = None) -> dict[str, Any]:
		return {
			"event_type": event_type,
			"event_id": event_id or str(uuid4()),
			"timestamp": datetime.now(tz=timezone.utc).isoformat(),
			"payload": payload,
		}

	def publish(
		self,
		*,
		event_type: str,
		payload: dict[str, Any],
		routing_key: str,
		queue_name: str | None = None,
		event_id: str | None = None,
		headers: dict[str, Any] | None = None,
	) -> dict[str, Any]:
		message = self.build_message(event_type=event_type, payload=payload, event_id=event_id)

		queue = None
		if queue_name:
			queue = Queue(queue_name, exchange=self.exchange, routing_key=routing_key, durable=True)

		with Connection(self.rabbitmq_url) as connection:
			if queue is not None:
				queue.maybe_bind(connection)
				queue.declare()

			producer = Producer(connection)
			producer.publish(
				message,
				serializer="json",
				exchange=self.exchange,
				routing_key=routing_key,
				headers=headers or {},
				declare=[queue] if queue is not None else [self.exchange],
				retry=True,
			)

		return message

