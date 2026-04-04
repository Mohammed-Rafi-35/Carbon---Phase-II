from __future__ import annotations

import logging
import socket
import threading
from uuid import UUID

from kombu import Connection, Consumer, Exchange, Producer, Queue

from app.core.config import get_settings
from app.core.constants import NotificationChannel, NotificationType
from app.db.session import SessionLocal
from app.schemas.notification import NotificationSendRequest
from app.services.notification_service import NotificationService


logger = logging.getLogger(__name__)


class NotificationEventBusConsumer:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.exchange = Exchange("devtrails.events", type="topic", durable=True)
        self.dlx = Exchange("devtrails.events.dlx", type="direct", durable=True)
        self.queue = Queue(
            self.settings.notification_event_queue_name,
            exchange=self.exchange,
            routing_key=self.settings.notification_event_routing_key,
            durable=True,
            queue_arguments={
                "x-dead-letter-exchange": self.dlx.name,
                "x-dead-letter-routing-key": f"{self.settings.notification_event_queue_name}.failed",
            },
        )
        self.dlq = Queue(
            f"{self.settings.notification_event_queue_name}.dlq",
            exchange=self.dlx,
            routing_key=f"{self.settings.notification_event_queue_name}.failed",
            durable=True,
        )

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="notification-event-consumer")
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
                logger.warning("notification event consumer connection failed: %s", exc)
                self._stop_event.wait(2)

    def _handle_message(self, connection: Connection, body: dict, message) -> None:
        try:
            payload = body.get("payload", body)
            event_type = str(body.get("event_type", "")).upper()
            if event_type == "CLAIM_APPROVED":
                self._enqueue_claim_notification(payload)
            elif event_type == "PAYOUT_COMPLETED":
                self._enqueue_payout_notification(payload)
            message.ack()
        except Exception as exc:
            retries = int((message.headers or {}).get("x-retry-count", 0))
            producer = Producer(connection)
            if retries < self.settings.retry_limit:
                producer.publish(
                    body,
                    serializer="json",
                    exchange=self.exchange,
                    routing_key=self.settings.notification_event_routing_key,
                    headers={"x-retry-count": retries + 1},
                    delivery_mode=2,
                    declare=[self.queue],
                    retry=True,
                )
            else:
                producer.publish(
                    body,
                    serializer="json",
                    exchange=self.dlx,
                    routing_key=f"{self.settings.notification_event_queue_name}.failed",
                    headers={"x-last-error": str(exc)},
                    delivery_mode=2,
                    declare=[self.dlq],
                    retry=True,
                )
            message.ack()

    def _enqueue_claim_notification(self, payload: dict) -> None:
        user_id = payload.get("user_id")
        claim_id = payload.get("claim_id")
        amount = payload.get("amount")
        if not user_id or not claim_id:
            return

        db = SessionLocal()
        try:
            service = NotificationService(db)
            service.queue_notification(
                NotificationSendRequest(
                    user_id=UUID(str(user_id)),
                    channel=NotificationChannel.IN_APP,
                    type=NotificationType.CLAIM_UPDATE,
                    message=f"Claim {claim_id} approved. Payout amount: {amount}.",
                )
            )
        finally:
            db.close()

    def _enqueue_payout_notification(self, payload: dict) -> None:
        user_id = payload.get("user_id")
        transaction_id = payload.get("transaction_id")
        amount = payload.get("amount")
        if not user_id or not transaction_id:
            return

        db = SessionLocal()
        try:
            service = NotificationService(db)
            service.queue_notification(
                NotificationSendRequest(
                    user_id=UUID(str(user_id)),
                    channel=NotificationChannel.IN_APP,
                    type=NotificationType.PAYOUT,
                    message=f"Payout completed: {transaction_id}. Amount: {amount}.",
                )
            )
        finally:
            db.close()
