from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from locust import HttpUser, between, task


class PayoutPerformanceUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        token = jwt.encode(
            {
                "sub": "16fd2706-8baf-433b-82eb-8c7fada847da",
                "role": "worker",
                "exp": datetime.now(tz=timezone.utc) + timedelta(hours=1),
            },
            "dev-secret",
            algorithm="HS256",
        )
        self.headers = {
            "Authorization": f"Bearer {token}",
            "X-Request-ID": "locust-req-001",
            "Content-Type": "application/json",
        }

    @task(3)
    def process_payout(self):
        headers = dict(self.headers)
        headers["Idempotency-Key"] = str(uuid4())
        self.client.post(
            "/api/v1/payout/process",
            headers=headers,
            json={
                "claim_id": str(uuid4()),
                "user_id": "16fd2706-8baf-433b-82eb-8c7fada847da",
                "amount": 200,
            },
            name="payout_process",
        )

    @task(1)
    def get_history(self):
        self.client.get(
            "/api/v1/payout/16fd2706-8baf-433b-82eb-8c7fada847da",
            headers=self.headers,
            name="payout_history",
        )
