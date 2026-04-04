from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from uuid import uuid4

import pytest


BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8001").rstrip("/")
TOKEN = os.getenv("E2E_BEARER_TOKEN")
USER_ID = os.getenv("E2E_USER_ID", "16fd2706-8baf-433b-82eb-8c7fada847da")
POLL_SECONDS = int(os.getenv("E2E_POLL_SECONDS", "60"))


def _http_json(method: str, path: str, payload: dict | None = None, headers: dict | None = None) -> tuple[int, dict]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, method=method)
    req.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        req.add_header(key, value)

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode("utf-8")
            return response.status, json.loads(content)
    except urllib.error.HTTPError as exc:
        content = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(content)
        except json.JSONDecodeError:
            return exc.code, {"raw": content}


def _stack_available() -> bool:
    try:
        status, _ = _http_json("GET", "/health")
        return status == 200
    except Exception:
        return False


def test_autonomous_claim_to_payout_flow() -> None:
    if not _stack_available():
        pytest.skip("Live stack is not running; start docker compose stack for E2E validation.")

    if not TOKEN:
        pytest.skip("Set E2E_BEARER_TOKEN to run autonomous claim-to-payout E2E flow.")

    auth_headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-Request-ID": str(uuid4()),
        "Idempotency-Key": f"e2e-{uuid4()}",
    }

    event_id = str(uuid4())
    status, created = _http_json(
        "POST",
        "/api/v1/claims/auto",
        payload={"user_id": USER_ID, "event_id": event_id},
        headers=auth_headers,
    )
    assert status in {200, 201}, created
    claim_id = created.get("data", {}).get("claim_id")
    assert claim_id, created

    process_headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-Request-ID": str(uuid4()),
    }
    status, processed = _http_json(
        "POST",
        "/api/v1/claims/process",
        payload={"claim_id": claim_id},
        headers=process_headers,
    )
    assert status in {200, 202}, processed

    deadline = time.time() + POLL_SECONDS
    final_status = None
    while time.time() < deadline:
        status, detail = _http_json(
            "GET",
            f"/api/v1/claims/detail/{claim_id}",
            headers={"Authorization": f"Bearer {TOKEN}", "X-Request-ID": str(uuid4())},
        )
        if status == 200:
            final_status = str(detail.get("data", {}).get("status", "")).lower()
            if final_status in {"paid", "approved", "rejected"}:
                break
        time.sleep(2)

    assert final_status in {"paid", "approved", "rejected"}
