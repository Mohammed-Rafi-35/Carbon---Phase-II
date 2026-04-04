from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from locust import HttpUser, constant, task


class PayoutStressUser(HttpUser):
    wait_time = constant(0.05)

    def on_start(self):
        token = jwt.encode(
            {
                "sub": "16fd2706-8baf-433b-82eb-8c7fada847da",
                "role": "service",
                "exp": datetime.now(tz=timezone.utc) + timedelta(hours=1),
            },
            "dev-secret",
            algorithm="HS256",
        )
        self.headers = {
            "Authorization": f"Bearer {token}",
            "X-Request-ID": "stress-req-001",
            "Content-Type": "application/json",
        }

    @task
    def burst_process(self):
        headers = dict(self.headers)
        headers["Idempotency-Key"] = str(uuid4())
        self.client.post(
            "/api/v1/payout/process",
            headers=headers,
            json={
                "claim_id": str(uuid4()),
                "user_id": "16fd2706-8baf-433b-82eb-8c7fada847da",
                "amount": 99,
            },
            name="payout_process_stress",
        )
