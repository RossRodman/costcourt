from __future__ import annotations

from fastapi.testclient import TestClient

from app import __version__
from app.core.config import Settings
from app.main import create_app


def test_health_reports_ok(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": __version__,
        "env": "test",
        "llm_configured": False,
    }


def test_health_reflects_configured_key() -> None:
    settings = Settings(anthropic_api_key="sk-ant-test")  # type: ignore[arg-type]
    response = TestClient(create_app(settings)).get("/api/health")
    assert response.json()["llm_configured"] is True


def test_openapi_is_served(client: TestClient) -> None:
    assert client.get("/api/openapi.json").status_code == 200


def test_shutdown_closes_running_debates(settings: Settings) -> None:
    app = create_app(settings)
    with TestClient(app):
        pass  # lifespan start + shutdown
    assert app.state.debates.list() == []
