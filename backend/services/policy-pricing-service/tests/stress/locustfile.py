from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from locust import HttpUser, constant, task


class PolicyPricingStressUser(HttpUser):
    wait_time = constant(0.05)

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
            "X-Request-ID": "stress-req-001",
            "Content-Type": "application/json",
        }

    @task
    def burst_policy_create(self):
        self.client.post(
            "/api/v1/policy/create",
            headers=self.headers,
            json={
                "user_id": "6f0f7ac8-7f06-4f24-9ec8-dbcd793c30af",
                "weekly_income": 10500,
                "zone": "HR-3",
                "activity_days": 6,
                "policy_week": 1,
                "premium_paid": True,
            },
            name="policy_create_stress",
        )
