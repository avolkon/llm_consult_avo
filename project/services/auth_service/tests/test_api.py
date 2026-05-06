from fastapi.testclient import TestClient


def test_register_login_me_flow(client: TestClient) -> None:
    register_payload = {"email": "user1@example.com", "password": "secret123"}

    register_resp = client.post("/auth/register", json=register_payload)
    assert register_resp.status_code == 201
    register_data = register_resp.json()
    assert register_data["email"] == register_payload["email"]
    assert register_data["role"] == "user"

    login_resp = client.post(
        "/auth/login",
        data={
            "username": register_payload["email"],
            "password": register_payload["password"],
        },
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    assert token

    me_resp = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == register_payload["email"]


def test_duplicate_email_returns_409(client: TestClient) -> None:
    payload = {"email": "duplicate@example.com", "password": "secret123"}

    first = client.post("/auth/register", json=payload)
    second = client.post("/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_login_wrong_password_returns_401(client: TestClient) -> None:
    payload = {"email": "wrongpass@example.com", "password": "secret123"}
    client.post("/auth/register", json=payload)

    response = client.post(
        "/auth/login",
        data={"username": payload["email"], "password": "invalid-password"},
    )
    assert response.status_code == 401


def test_me_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_with_invalid_token_returns_401(client: TestClient) -> None:
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid.token.value"},
    )
    assert response.status_code == 401
