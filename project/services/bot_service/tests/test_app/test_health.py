from fastapi.testclient import TestClient

from app.main import create_app


def test_health_ok() -> None:
    with TestClient(create_app(with_max_webhook=False)) as client:
        response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["transport"] == "max"
