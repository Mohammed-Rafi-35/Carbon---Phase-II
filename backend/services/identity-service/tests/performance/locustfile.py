from __future__ import annotations

from locust import HttpUser, between, task


class IdentityUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.phone = "9999999000"
        self.password = "SecurePass123"
        self.email = "loadtest@example.com"
        self.user_id = None
        self.token = None

        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "name": "Load Tester",
                "phone": self.phone,
                "email": self.email,
                "password": self.password,
            },
            name="register",
        )
        if response.status_code in (200, 201):
            payload = response.json().get("data", {})
            self.user_id = payload.get("user_id")
            self.token = payload.get("token")

    @task(2)
    def login(self):
        response = self.client.post(
            "/api/v1/auth/login",
            json={"phone": self.phone, "password": self.password},
            name="login",
        )
        if response.status_code == 200:
            self.token = response.json().get("data", {}).get("token")

    @task(1)
    def validate_session(self):
        if self.token:
            self.client.get(
                "/api/v1/auth/validate",
                headers={"Authorization": f"Bearer {self.token}"},
                name="validate",
            )
