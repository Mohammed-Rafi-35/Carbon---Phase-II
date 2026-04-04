from __future__ import annotations

import datetime
import os
from uuid import uuid4

import jwt
from fastapi.testclient import TestClient


os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///./ai_risk_integration_test.db"

from app.core.config import get_settings
from app.main import app


client = TestClient(app)


def _token() -> str:
    settings = get_settings()
    payload = {
        "sub": str(uuid4()),
        "role": "service",
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def test_risk_evaluate_endpoint_returns_success() -> None:
    headers = {
        "Authorization": f"Bearer {_token()}",
        "X-Request-ID": str(uuid4()),
    }
    payload = {
        "zone": "MR-2",
        "metrics": {
            "disruption_freq": 0.6,
            "duration": 0.7,
            "traffic": 0.5,
            "order_drop": 0.8,
            "activity": 0.4,
            "claims": 0.3,
        },
    }

    response = client.post("/api/v1/risk/evaluate", json=payload, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "risk_score" in body["data"]
