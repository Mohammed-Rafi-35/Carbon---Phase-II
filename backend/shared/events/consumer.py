from __future__ import annotations

import logging
import socket
import threading
from collections.abc import Callable
from typing import Any

from kombu import Connection, Consumer, Exchange, Producer, Queue


logger = logging.getLogger(__name__)


class EventConsumerWorker:
	def __init__(
		self,
		*,
		rabbitmq_url: str,
		queue_name: str,
		routing_key: str,
		handler: Callable[[dict[str, Any]], None],
		exchange_name: str = "devtrails.events",
		prefetch_count: int = 10,
		retry_limit: int = 3,
		dlq_enabled: bool = True,
	) -> None:
		self.rabbitmq_url = rabbitmq_url
		self.queue_name = queue_name
		self.routing_key = routing_key
		self.handler = handler
		self.prefetch_count = prefetch_count
		self.retry_limit = retry_limit
		self.dlq_enabled = dlq_enabled

		self.exchange = Exchange(exchange_name, type="topic", durable=True)
		self.dlx = Exchange(f"{exchange_name}.dlx", type="direct", durable=True)
		self.dlq_routing_key = f"{queue_name}.failed"

		queue_args = None
		if self.dlq_enabled:
			queue_args = {
				"x-dead-letter-exchange": self.dlx.name,
				"x-dead-letter-routing-key": self.dlq_routing_key,
			}

		self.queue = Queue(
			self.queue_name,
			exchange=self.exchange,
			routing_key=self.routing_key,
			durable=True,
			queue_arguments=queue_args,
		)
		self.dlq = Queue(
			f"{self.queue_name}.dlq",
			exchange=self.dlx,
			routing_key=self.dlq_routing_key,
			durable=True,
		)

		self._stop_event = threading.Event()
		self._thread: threading.Thread | None = None

	def start(self) -> None:
		if self._thread and self._thread.is_alive():
			return
		self._stop_event.clear()
		self._thread = threading.Thread(target=self._run, daemon=True, name=f"consumer-{self.queue_name}")
		self._thread.start()

	def stop(self, timeout: float = 5.0) -> None:
		self._stop_event.set()
		if self._thread and self._thread.is_alive():
			self._thread.join(timeout=timeout)

	def _run(self) -> None:
		while not self._stop_event.is_set():
			try:
				with Connection(self.rabbitmq_url) as connection:
					self.queue.maybe_bind(connection)
					self.queue.declare()
					if self.dlq_enabled:
						self.dlq.maybe_bind(connection)
						self.dlq.declare()

					with Consumer(
						connection,
						queues=[self.queue],
						callbacks=[lambda body, message: self._handle_message(connection, body, message)],
						accept=["json"],
						prefetch_count=self.prefetch_count,
					):
						while not self._stop_event.is_set():
							try:
								connection.drain_events(timeout=1)
							except socket.timeout:
								continue
			except Exception as exc:
				logger.warning("event_consumer_connection_failed queue=%s error=%s", self.queue_name, exc)
				self._stop_event.wait(2)

	def _handle_message(self, connection: Connection, body: dict[str, Any], message) -> None:
		try:
			self.handler(body)
			message.ack()
			return
		except Exception as exc:
			headers = message.headers or {}
			retries = int(headers.get("x-retry-count", 0))
			producer = Producer(connection)

			if retries < self.retry_limit:
				producer.publish(
					body,
					serializer="json",
					exchange=self.exchange,
					routing_key=message.delivery_info.get("routing_key", self.routing_key),
					headers={**headers, "x-retry-count": retries + 1},
					declare=[self.queue],
					retry=True,
				)
				message.ack()
				return

			if self.dlq_enabled:
				producer.publish(
					body,
					serializer="json",
					exchange=self.dlx,
					routing_key=self.dlq_routing_key,
					headers={**headers, "x-last-error": str(exc)},
					declare=[self.dlq],
					retry=True,
				)
			message.ack()

