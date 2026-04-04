from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from locust import HttpUser, between, task


class PolicyPricingUser(HttpUser):
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
    def create_policy(self):
        self.client.post(
            "/api/v1/policy/create",
            headers=self.headers,
            json={
                "user_id": "6f0f7ac8-7f06-4f24-9ec8-dbcd793c30af",
                "weekly_income": 10000,
                "zone": "MR-2",
                "activity_days": 5,
                "policy_week": 1,
                "premium_paid": True,
            },
            name="policy_create",
        )

    @task(1)
    def get_policy(self):
        self.client.get(
            "/api/v1/policy/6f0f7ac8-7f06-4f24-9ec8-dbcd793c30af",
            headers=self.headers,
            name="policy_get",
        )
