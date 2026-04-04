from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from locust import HttpUser, constant, task


class NotificationStressUser(HttpUser):
    wait_time = constant(0.05)

    def on_start(self):
        token = jwt.encode(
            {
                "sub": "16fd2706-8baf-433b-82eb-8c7fada847da",
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
    def burst_send(self):
        self.client.post(
            "/api/v1/notify/send",
            headers=self.headers,
            json={
                "user_id": "6f0f7ac8-7f06-4f24-9ec8-dbcd793c30af",
                "channel": "IN_APP",
                "type": "PAYOUT",
                "message": "Stress test message",
            },
            name="notify_send_stress",
        )
