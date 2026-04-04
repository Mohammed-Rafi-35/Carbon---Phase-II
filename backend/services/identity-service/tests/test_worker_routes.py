from __future__ import annotations


def _register_and_token(client, phone: str, email: str):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Worker",
            "phone": phone,
            "email": email,
            "password": "SecurePass123",
        },
    )
    body = response.json()["data"]
    return body["user_id"], body["access_token"]


def test_create_worker_profile_success(client):
    user_id, token = _register_and_token(client, "9999999995", "worker1@example.com")

    response = client.post(
        "/api/v1/workers/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "user_id": user_id,
            "zone": "MR-2",
            "vehicle_type": "bike",
            "avg_weekly_income": 10000,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["profile_id"]


def test_get_worker_profile_success(client):
    user_id, token = _register_and_token(client, "9999999994", "worker2@example.com")

    client.post(
        "/api/v1/workers/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "user_id": user_id,
            "zone": "HR-3",
            "vehicle_type": "cycle",
            "avg_weekly_income": 9000,
        },
    )

    response = client.get(
        f"/api/v1/workers/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["zone"] == "HR-3"
    assert float(data["avg_weekly_income"]) == 9000


def test_profile_update_restricted_to_owner(client):
    user_id_1, token_1 = _register_and_token(client, "9999999993", "worker3@example.com")
    user_id_2, _ = _register_and_token(client, "9999999992", "worker4@example.com")

    response = client.post(
        "/api/v1/workers/profile",
        headers={"Authorization": f"Bearer {token_1}"},
        json={
            "user_id": user_id_2,
            "zone": "LR-1",
            "vehicle_type": "bike",
            "avg_weekly_income": 7000,
        },
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
