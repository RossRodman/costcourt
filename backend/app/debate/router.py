"""Debates API: start a debate, follow it live, fetch the result."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from functools import partial
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from sse_starlette import EventSourceResponse, ServerSentEvent

from app.agents import Panel, build_panel
from app.agents.llm import LLMNotConfiguredError
from app.api.deps import SettingsDep
from app.debate.events import debate_event_adapter
from app.debate.schemas import DebateOut, DebateRequest
from app.debate.sessions import DebateManager, DebateNotFoundError, DebateSession
from app.demo import DemoNotAvailableError, demo_panel, demo_scripts
from app.estimates.catalog import EstimateNotFoundError
from app.estimates.router import CatalogDep

router = APIRouter(prefix="/debates", tags=["debates"])

NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"description": "Unknown debate id"}}


def get_debates(request: Request) -> DebateManager:
    manager: DebateManager = request.app.state.debates
    return manager


PanelFactory = Callable[[], Panel]


def get_panel_factory(settings: SettingsDep) -> PanelFactory:
    """Builds the Claude-backed agents for a new debate. Overridden in tests.

    A factory rather than a panel, so a missing API key only matters for
    debates that actually call Claude (not for demo replays).
    """
    return partial(build_panel, settings)


DebatesDep = Annotated[DebateManager, Depends(get_debates)]
PanelFactoryDep = Annotated[PanelFactory, Depends(get_panel_factory)]


def _session(debates: DebateManager, debate_id: UUID) -> DebateSession:
    try:
        return debates.get(debate_id)
    except DebateNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        404: {"description": "Unknown sample id, or no demo for that sample"},
        503: {"description": "No Anthropic API key configured"},
    },
)
async def start_debate(
    body: DebateRequest,
    response: Response,
    debates: DebatesDep,
    catalog: CatalogDep,
    settings: SettingsDep,
    make_panel: PanelFactoryDep,
) -> DebateOut:
    """Start a debate in the background. Follow it at `/debates/{id}/events`."""
    if body.estimate is not None:
        estimate = body.estimate
    else:
        try:
            estimate = catalog.get(body.sample_id or "")
        except EstimateNotFoundError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    if body.demo:
        try:
            panel, rounds = demo_panel(estimate.id, delay_s=settings.demo_delay_s)
        except DemoNotAvailableError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    else:
        try:
            panel = make_panel()
        except LLMNotConfiguredError as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
        rounds = body.rounds or settings.debate_rounds

    session = debates.start(panel, estimate, rounds=rounds, demo=body.demo)
    response.headers["Location"] = f"{router.prefix}/{session.id}"
    return DebateOut.of(session)


@router.get("")
async def list_debates(debates: DebatesDep) -> list[DebateOut]:
    """Recent debates, newest first (without the full reports)."""
    return [DebateOut.of(s, detail=False) for s in debates.list()]


@router.get("/demos")
async def list_demos() -> list[str]:
    """Sample ids that have a recorded demo debate (playable without an API key)."""
    return sorted(demo_scripts())


@router.get("/{debate_id}", responses=NOT_FOUND)
async def get_debate(debate_id: UUID, debates: DebatesDep) -> DebateOut:
    return DebateOut.of(_session(debates, debate_id))


@router.get(
    "/{debate_id}/events",
    response_class=EventSourceResponse,
    responses={
        **NOT_FOUND,
        200: {
            "description": "Server-sent events: the full history, then live events. "
            "The stream closes after `debate_completed` or `debate_failed`.",
            "content": {"text/event-stream": {}},
        },
    },
)
async def stream_events(
    debate_id: UUID,
    debates: DebatesDep,
    last_event_id: Annotated[int | None, Header()] = None,
) -> EventSourceResponse:
    """Each SSE message has `id` (its index), `event` (its type) and JSON `data`.

    Browsers resend `Last-Event-ID` on reconnect, so nothing is missed or repeated.
    """
    session = _session(debates, debate_id)
    after = 0 if last_event_id is None else last_event_id + 1

    async def messages() -> AsyncIterator[ServerSentEvent]:
        async for index, event in session.subscribe(after):
            yield ServerSentEvent(
                id=str(index),
                event=event.type,
                data=debate_event_adapter.dump_json(event).decode(),
            )

    return EventSourceResponse(messages(), ping=15)
