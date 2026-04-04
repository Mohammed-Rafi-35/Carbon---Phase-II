from __future__ import annotations

from app.db.session import SessionLocal
from app.events.publisher import TriggerEventPublisher
from app.integrations.external_sources import ZoneSnapshot
from app.services.detection_service import DetectionService
from app.services.trigger_service import TriggerService


class StubGateway:
    def fetch_zone_snapshot(self, zone: str) -> ZoneSnapshot:
        return ZoneSnapshot(
            rain_mm=80.0,
            congestion_ratio=0.85,
            outage_ratio=0.0,
            platform_outage=False,
        )


def test_detection_creates_events_once():
    db = SessionLocal()
    try:
        trigger_service = TriggerService(db=db)
        detection = DetectionService(trigger_service=trigger_service, source_gateway=StubGateway())

        first_created = detection.poll_sources(["MR-2"])
        second_created = detection.poll_sources(["MR-2"])

        assert first_created == 2
        assert second_created == 0

        active = trigger_service.get_active_disruptions()
        assert len(active) == 2
        types = sorted(item.type for item in active)
        assert types == ["traffic", "weather"]
    finally:
        db.close()


def test_publisher_emits_contract_shape(monkeypatch):
    published: dict = {}

    class DummyConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class DummyQueue:
        def maybe_bind(self, _connection):
            return None

        def declare(self):
            return None

    class DummyProducer:
        def __init__(self, _connection):
            return None

        def publish(self, message, **kwargs):
            published["message"] = message
            published["kwargs"] = kwargs

    monkeypatch.setattr("app.events.publisher.Connection", lambda *_args, **_kwargs: DummyConnection())
    monkeypatch.setattr("app.events.publisher.Producer", DummyProducer)

    publisher = TriggerEventPublisher()
    publisher.settings.app_env = "development"
    publisher.queue = DummyQueue()

    publisher.publish_disruption_detected(
        {
            "event_id": "11111111-1111-1111-1111-111111111111",
            "zone": "MR-2",
            "type": "weather",
            "severity": "HIGH",
        }
    )

    message = published["message"]
    assert message["event"] == "DISRUPTION_DETECTED"
    assert message["event_type"] == "DISRUPTION_DETECTED"
    assert message["event_id"] == "11111111-1111-1111-1111-111111111111"
    assert message["payload"]["event_id"] == "11111111-1111-1111-1111-111111111111"
    assert message["payload"]["zone"] == "MR-2"
    assert message["payload"]["type"] == "weather"
    assert message["payload"]["severity"] == "HIGH"
