from fastapi.testclient import TestClient

from tests.conftest import GOOD_PASSWORD


def test_register_login_me_flow(client: TestClient) -> None:
    register_payload = {"email": "user1@example.com", "password": GOOD_PASSWORD}

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
    payload = {"email": "duplicate@example.com", "password": GOOD_PASSWORD}

    first = client.post("/auth/register", json=payload)
    second = client.post("/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_login_wrong_password_returns_401(client: TestClient) -> None:
    payload = {"email": "wrongpass@example.com", "password": GOOD_PASSWORD}
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


def test_invalid_email_returns_422(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": GOOD_PASSWORD},
    )
    assert response.status_code == 422


def test_weak_password_rejected(client: TestClient) -> None:
    r = client.post(
        "/auth/register",
        json={"email": "weak@example.com", "password": "Sh0rt!"},
    )
    assert r.status_code == 422


def test_password_without_special_rejected(client: TestClient) -> None:
    r = client.post(
        "/auth/register",
        json={"email": "nospec@example.com", "password": "ValidPass1"},
    )
    assert r.status_code == 422


def test_password_without_uppercase_rejected(client: TestClient) -> None:
    r = client.post(
        "/auth/register",
        json={"email": "noupper@example.com", "password": "validp@ss1"},
    )
    assert r.status_code == 422


def test_password_without_digit_rejected(client: TestClient) -> None:
    r = client.post(
        "/auth/register",
        json={"email": "nodigit@example.com", "password": "OnlyHere!Ab"},
    )
    assert r.status_code == 422


def test_register_body_over_limit_returns_413(monkeypatch) -> None:
    monkeypatch.setenv("MAX_REQUEST_BODY_BYTES", "120")
    from app.core.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    app = create_app()
    with TestClient(app) as c:
        payload = b'{"email":"u@example.com","password":"' + (b"Aa1!" * 28) + b'"}'
        response = c.post(
            "/auth/register",
            content=payload,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 413
        assert response.json()["detail"] == "Request body too large"
    get_settings.cache_clear()
