from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.debate.models import DebateReport
from app.reports.store import ReportStore


@pytest.fixture
def store(client: TestClient) -> ReportStore:
    reports: ReportStore = client.app.state.reports  # type: ignore[attr-defined]
    return reports


@pytest.fixture
def saved(store: ReportStore, report: DebateReport) -> DebateReport:
    store.save(report)
    return report


def test_list(client: TestClient, saved: DebateReport) -> None:
    response = client.get("/api/reports")

    assert response.status_code == 200
    [summary] = response.json()
    assert summary["id"] == str(saved.id)
    assert summary["revised_total"] == 1370.0
    assert summary["delta_pct"] == -33.17


def test_list_is_empty_at_first(client: TestClient) -> None:
    assert client.get("/api/reports").json() == []


def test_get(client: TestClient, saved: DebateReport) -> None:
    response = client.get(f"/api/reports/{saved.id}")

    assert response.status_code == 200
    assert DebateReport.model_validate(response.json()) == saved


@pytest.mark.parametrize(
    ("fmt", "content_type", "extension"),
    [
        ("markdown", "text/markdown; charset=utf-8", "md"),
        ("html", "text/html; charset=utf-8", "html"),
        ("json", "application/json", "json"),
    ],
)
def test_export(
    client: TestClient, saved: DebateReport, fmt: str, content_type: str, extension: str
) -> None:
    response = client.get(f"/api/reports/{saved.id}/export", params={"format": fmt})

    assert response.status_code == 200
    assert response.headers["content-type"] == content_type
    name = f"costcourt-test-estimate-{saved.id.hex[:8]}.{extension}"
    assert response.headers["content-disposition"] == f"inline; filename*=utf-8''{name}"


def test_export_defaults_to_html(client: TestClient, saved: DebateReport) -> None:
    response = client.get(f"/api/reports/{saved.id}/export")
    assert response.text.startswith("<!doctype html>")


def test_export_as_download(client: TestClient, saved: DebateReport) -> None:
    response = client.get(
        f"/api/reports/{saved.id}/export", params={"format": "markdown", "download": True}
    )
    assert response.headers["content-disposition"].startswith("attachment; ")


def test_unknown_format(client: TestClient, saved: DebateReport) -> None:
    response = client.get(f"/api/reports/{saved.id}/export", params={"format": "pdf"})
    assert response.status_code == 422


def test_delete(client: TestClient, saved: DebateReport) -> None:
    assert client.delete(f"/api/reports/{saved.id}").status_code == 204
    assert client.get(f"/api/reports/{saved.id}").status_code == 404
    assert client.delete(f"/api/reports/{saved.id}").status_code == 404


@pytest.mark.parametrize("path", ["", "/export"])
def test_unknown_report(client: TestClient, path: str) -> None:
    missing = uuid4()
    response = client.get(f"/api/reports/{missing}{path}")

    assert response.status_code == 404
    assert response.json() == {"detail": f"no saved report with id '{missing}'"}


def test_ids_must_be_uuids(client: TestClient) -> None:
    assert client.get("/api/reports/..%2F..%2Fetc%2Fpasswd").status_code in (404, 422)
    assert client.get("/api/reports/not-a-uuid").status_code == 422
