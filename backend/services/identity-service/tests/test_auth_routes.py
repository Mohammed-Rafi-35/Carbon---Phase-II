from __future__ import annotations


def test_register_user_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Ravi Kumar",
            "phone": "9999999999",
            "email": "ravi@example.com",
            "password": "SecurePass123",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "success"
    assert body["error"] is None
    assert body["data"]["user_id"]
    assert body["data"]["access_token"]
    assert body["data"]["refresh_token"]


def test_register_duplicate_phone(client):
    payload = {
        "name": "Ravi Kumar",
        "phone": "9999999998",
        "email": "ravi2@example.com",
        "password": "SecurePass123",
    }
    client.post("/api/v1/auth/register", json=payload)

    second = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Another",
            "phone": "9999999998",
            "email": "another@example.com",
            "password": "SecurePass123",
        },
    )
    assert second.status_code == 409
    body = second.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "PHONE_ALREADY_EXISTS"


def test_login_success(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Meera",
            "phone": "9999999997",
            "email": "meera@example.com",
            "password": "SecurePass123",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"phone": "9999999997", "password": "SecurePass123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["access_token"]
    assert body["data"]["refresh_token"]


def test_validate_session(client):
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Anil",
            "phone": "9999999996",
            "email": "anil@example.com",
            "password": "SecurePass123",
        },
    )
    token = reg.json()["data"]["access_token"]

    response = client.get(
        "/api/v1/auth/validate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["valid"] is True
