from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_samples(client: TestClient) -> None:
    response = client.get("/api/estimates/samples")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    assert set(body[0]) == {"id", "title", "location", "currency", "item_count", "grand_total"}


def test_get_sample_includes_computed_totals(client: TestClient) -> None:
    response = client.get("/api/estimates/samples/warehouse-slab")
    assert response.status_code == 200
    body = response.json()
    assert body["totals"]["grand_total"] == 190_799.27
    assert body["items"][0]["total"] == 8_160.0


def test_get_unknown_sample_is_404(client: TestClient) -> None:
    response = client.get("/api/estimates/samples/nope")
    assert response.status_code == 404
    assert "nope" in response.json()["detail"]


def test_preview_computes_totals(client: TestClient) -> None:
    payload = {
        "id": "my-job",
        "title": "Garden wall",
        "scope": "Brick garden wall, 12 m long.",
        "currency": "EUR",
        "markups": {"tax": 20},
        "items": [
            {
                "id": "1",
                "description": "Brickwork",
                "category": "masonry",
                "unit": "m2",
                "quantity": 14.4,
                "unit_rate": 85,
            }
        ],
    }
    response = client.post("/api/estimates/preview", json=payload)
    assert response.status_code == 200
    assert response.json()["totals"]["grand_total"] == 1468.8  # 1224 + 20 %


def test_preview_rejects_invalid_estimate(client: TestClient) -> None:
    response = client.post("/api/estimates/preview", json={"id": "x", "items": []})
    assert response.status_code == 422
