from __future__ import annotations

from uuid import UUID

from app.services.notification_service import NotificationService


def test_sms_delivery_success_marks_sent(db_session, monkeypatch):
    service = NotificationService(db_session)

    # The queue_notification path is validated in route tests.
    # This integration test validates delivery state transition directly.
    item = service.repository.create(
        user_id=UUID("6f0f7ac8-7f06-4f24-9ec8-dbcd793c30af"),
        channel="SMS",
        type_="CLAIM_UPDATE",
        message="Delivery test",
        status="queued",
    )

    monkeypatch.setattr(service.sms_client, "send_sms", lambda user_id, message: None)

    service.deliver_notification(item.id)
    updated = service.repository.get_by_id(item.id)
    assert updated is not None
    assert updated.status == "sent"


def test_push_delivery_failure_retries(db_session, monkeypatch):
    service = NotificationService(db_session)
    item = service.repository.create(
        user_id=UUID("16fd2706-8baf-433b-82eb-8c7fada847da"),
        channel="PUSH",
        type_="PAYOUT",
        message="Push test",
        status="queued",
    )

    def fail_push(user_id: str, message: str) -> None:
        _ = user_id
        _ = message
        raise RuntimeError("provider-down")

    monkeypatch.setattr(service.push_client, "send_push", fail_push)

    service.deliver_notification(item.id)
    updated = service.repository.get_by_id(item.id)
    assert updated is not None
    assert updated.status in {"retry_scheduled", "failed"}
