from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
from fastapi import FastAPI

from app.core.config import Settings
from app.debate.router import get_panel_factory
from app.debate.sessions import DebateManager
from app.main import create_app
from tests.factories import estimate, line_item
from tests.fakes import DISPUTED_ID, ScriptedLLM, debate_script, scripted_panel


@pytest.fixture
def llm() -> ScriptedLLM:
    return ScriptedLLM(debate_script(rounds=1))


@pytest.fixture
def app(settings: Settings, llm: ScriptedLLM) -> FastAPI:
    app = create_app(settings.model_copy(update={"debate_rounds": 1, "demo_delay_s": 0}))
    app.dependency_overrides[get_panel_factory] = lambda: lambda: scripted_panel(llm)
    return app


@pytest.fixture
async def api(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test/api") as client:
        yield client
    await app.state.debates.aclose()


def parse_sse(text: str) -> list[dict[str, Any]]:
    messages = []
    for block in text.replace("\r\n", "\n").strip().split("\n\n"):
        fields = dict(line.split(": ", 1) for line in block.splitlines() if ": " in line)
        if "event" in fields:
            messages.append(fields | {"data": json.loads(fields["data"])})
    return messages


async def start(api: httpx.AsyncClient, **body: Any) -> dict[str, Any]:
    response = await api.post("/debates", json=body)
    assert response.status_code == 202, response.text
    assert response.headers["location"] == f"/debates/{response.json()['id']}"
    data: dict[str, Any] = response.json()
    return data


async def test_debate_on_a_sample_end_to_end(api: httpx.AsyncClient) -> None:
    debate = await start(api, sample_id="warehouse-slab")
    assert debate["status"] == "running"
    assert debate["estimate_title"]
    assert debate["rounds"] == 1  # server default

    stream = await api.get(f"/debates/{debate['id']}/events")
    assert stream.headers["content-type"].startswith("text/event-stream")
    messages = parse_sse(stream.text)
    assert messages[0]["event"] == "debate_started"
    assert messages[-1]["event"] == "debate_completed"
    assert [m["id"] for m in messages] == [str(i) for i in range(len(messages))]
    assert all(m["event"] == m["data"]["type"] for m in messages)

    done = (await api.get(f"/debates/{debate['id']}")).json()
    assert done["status"] == "completed"
    assert done["events"] == len(messages)
    report = done["report"]
    assert report["id"] == debate["id"]
    assert report["impact"]["delta"] != 0
    assert report["verdict"]["rulings"][0]["line_item_id"] == DISPUTED_ID


async def test_debate_on_an_uploaded_estimate(api: httpx.AsyncClient) -> None:
    custom = estimate(line_item(id=DISPUTED_ID), title="My garage slab")
    debate = await start(api, estimate=custom.model_dump(mode="json"), rounds=1)
    assert debate["estimate_title"] == "My garage slab"
    assert debate["estimate"]["items"][0]["id"] == DISPUTED_ID

    await api.get(f"/debates/{debate['id']}/events")
    assert (await api.get(f"/debates/{debate['id']}")).json()["status"] == "completed"


async def test_resume_with_last_event_id(api: httpx.AsyncClient) -> None:
    debate = await start(api, sample_id="warehouse-slab")
    full = parse_sse((await api.get(f"/debates/{debate['id']}/events")).text)

    resumed = await api.get(f"/debates/{debate['id']}/events", headers={"Last-Event-ID": "4"})
    assert parse_sse(resumed.text) == full[5:]


async def test_list_debates_without_reports(api: httpx.AsyncClient) -> None:
    debate = await start(api, sample_id="warehouse-slab")
    await api.get(f"/debates/{debate['id']}/events")

    listed = (await api.get("/debates")).json()
    assert [d["id"] for d in listed] == [debate["id"]]
    assert listed[0]["report"] is None
    assert listed[0]["estimate"] is None


@pytest.mark.parametrize(
    "body",
    [{}, {"sample_id": "warehouse-slab", "estimate": {}}, {"sample_id": "x", "rounds": 9}],
)
async def test_invalid_requests(api: httpx.AsyncClient, body: dict[str, Any]) -> None:
    assert (await api.post("/debates", json=body)).status_code == 422


async def test_unknown_sample(api: httpx.AsyncClient) -> None:
    response = await api.post("/debates", json={"sample_id": "nope"})
    assert response.status_code == 404


@pytest.mark.parametrize("path", ["", "/events"])
async def test_unknown_debate(api: httpx.AsyncClient, path: str) -> None:
    response = await api.get(f"/debates/00000000-0000-0000-0000-000000000000{path}")
    assert response.status_code == 404
    assert "no debate" in response.json()["detail"]


async def test_no_api_key_is_503(settings: Settings) -> None:
    app = create_app(settings)
    assert isinstance(app.state.debates, DebateManager)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test/api") as api:
        response = await api.post("/debates", json={"sample_id": "warehouse-slab"})
    assert response.status_code == 503
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]


async def test_demo_debate_needs_no_api_key(settings: Settings) -> None:
    app = create_app(settings.model_copy(update={"demo_delay_s": 0}))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test/api") as api:
        assert (await api.get("/debates/demos")).json() == ["warehouse-slab"]

        debate = await start(api, sample_id="warehouse-slab", demo=True, rounds=5)
        assert debate["demo"] is True
        assert debate["rounds"] == 2  # the recording's length, not the requested rounds

        messages = parse_sse((await api.get(f"/debates/{debate['id']}/events")).text)
        assert messages[-1]["event"] == "debate_completed"
        report = messages[-1]["data"]["report"]
        assert set(report["models"].values()) == {"costcourt-demo"}
        assert report["impact"]["delta_pct"] > 0


async def test_demo_only_for_recorded_samples(api: httpx.AsyncClient) -> None:
    response = await api.post("/debates", json={"sample_id": "office-fit-out", "demo": True})
    assert response.status_code == 404
    assert "no demo" in response.json()["detail"]

    custom = estimate().model_dump(mode="json")
    response = await api.post("/debates", json={"estimate": custom, "demo": True})
    assert response.status_code == 422


async def test_completed_debate_is_saved_as_a_report(api: httpx.AsyncClient) -> None:
    debate = await start(api, sample_id="warehouse-slab", demo=True)
    await api.get(f"/debates/{debate['id']}/events")  # wait for the end

    [summary] = (await api.get("/reports")).json()
    assert summary["id"] == debate["id"]
    assert summary["demo"] is True
    assert summary["delta_pct"] == 14.62

    exported = await api.get(f"/reports/{debate['id']}/export", params={"format": "markdown"})
    assert exported.status_code == 200
    assert exported.text.startswith("# CostCourt report: Warehouse slab-on-grade")
