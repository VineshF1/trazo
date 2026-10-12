"""Phase 0 check: the app starts and the health endpoint answers."""

from fastapi.testclient import TestClient

from app.config import APP_NAME, APP_VERSION
from main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
    }


def test_health_logs_nothing_about_medicines():
    """The health payload carries no user, image or medicine data."""
    body = client.get("/health").json()
    assert set(body) == {"status", "service", "version"}