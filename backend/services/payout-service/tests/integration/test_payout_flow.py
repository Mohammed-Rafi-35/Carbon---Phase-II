from __future__ import annotations

from sqlalchemy import select

from app.models.ledger import LedgerEntry


def test_idempotent_replay_creates_single_ledger_entry(client, db_session, service_headers):
    headers = dict(service_headers)
    headers["Idempotency-Key"] = "idem-int-001"

    payload = {
        "claim_id": "018f56d1-1064-7bf3-8a18-7eac8f5c1001",
        "user_id": "8beea6d7-c470-45ff-b0a0-4e025fdb0f2f",
        "amount": 123.45,
    }

    first = client.post("/api/v1/payout/process", headers=headers, json=payload)
    second = client.post("/api/v1/payout/process", headers=headers, json=payload)

    assert first.status_code == 201
    assert second.status_code == 201

    entries = list(db_session.execute(select(LedgerEntry)).scalars().all())
    assert len(entries) == 1
