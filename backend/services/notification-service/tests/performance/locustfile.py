from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from locust import HttpUser, between, task


class NotificationUser(HttpUser):
    wait_time = between(1, 2)

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
            "X-Request-ID": "locust-req-001",
            "Content-Type": "application/json",
        }

    @task(3)
    def send_notification(self):
        self.client.post(
            "/api/v1/notify/send",
            headers=self.headers,
            json={
                "user_id": "6f0f7ac8-7f06-4f24-9ec8-dbcd793c30af",
                "channel": "IN_APP",
                "type": "CLAIM_UPDATE",
                "message": "Load test message",
            },
            name="notify_send",
        )

    @task(1)
    def get_history(self):
        self.client.get(
            "/api/v1/notify/6f0f7ac8-7f06-4f24-9ec8-dbcd793c30af",
            headers=self.headers,
            name="notify_history",
        )
