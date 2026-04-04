from __future__ import annotations

import logging
import socket
import threading

from kombu import Connection, Consumer, Exchange, Producer, Queue

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.fraud_service import FraudService


logger = logging.getLogger(__name__)


class FraudEventConsumer:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.exchange = Exchange(self.settings.fraud_exchange_name, type="topic", durable=True)
        self.dlx = Exchange(f"{self.settings.fraud_exchange_name}.dlx", type="direct", durable=True)
        self.queue = Queue(
            self.settings.fraud_inbound_queue_name,
            exchange=self.exchange,
            routing_key=self.settings.fraud_inbound_routing_key,
            durable=True,
            queue_arguments={
                "x-dead-letter-exchange": self.dlx.name,
                "x-dead-letter-routing-key": f"{self.settings.fraud_inbound_queue_name}.failed",
            },
        )
        self.dlq = Queue(
            f"{self.settings.fraud_inbound_queue_name}.dlq",
            exchange=self.dlx,
            routing_key=f"{self.settings.fraud_inbound_queue_name}.failed",
            durable=True,
        )

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="fraud-event-consumer")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                with Connection(self.settings.rabbitmq_url) as connection:
                    self.queue.maybe_bind(connection)
                    self.queue.declare()
                    self.dlq.maybe_bind(connection)
                    self.dlq.declare()

                    with Consumer(
                        connection,
                        queues=[self.queue],
                        callbacks=[lambda body, message: self._handle_message(connection, body, message)],
                        accept=["json"],
                        prefetch_count=self.settings.prefetch_count,
                    ):
                        while not self._stop_event.is_set():
                            try:
                                connection.drain_events(timeout=1)
                            except socket.timeout:
                                continue
            except Exception as exc:
                logger.warning("fraud consumer connection failed: %s", exc)
                self._stop_event.wait(2)

    def _handle_message(self, connection: Connection, body: dict, message) -> None:
        try:
            event_type = str(body.get("event_type", "")).upper()
            payload = body.get("payload", body)
            if event_type == "CLAIM_INITIATED":
                self._process_claim(payload)
            message.ack()
        except Exception as exc:
            retries = int((message.headers or {}).get("x-retry-count", 0))
            producer = Producer(connection)
            if retries < self.settings.retry_limit:
                producer.publish(
                    body,
                    serializer="json",
                    exchange=self.exchange,
                    routing_key=self.settings.fraud_inbound_routing_key,
                    headers={"x-retry-count": retries + 1},
                    declare=[self.queue],
                    retry=True,
                )
            else:
                producer.publish(
                    body,
                    serializer="json",
                    exchange=self.dlx,
                    routing_key=f"{self.settings.fraud_inbound_queue_name}.failed",
                    headers={"x-last-error": str(exc)},
                    declare=[self.dlq],
                    retry=True,
                )
            message.ack()

    def _process_claim(self, payload: dict) -> None:
        db = SessionLocal()
        try:
            service = FraudService(db)
            service.check_claim_from_event(payload)
        finally:
            db.close()
