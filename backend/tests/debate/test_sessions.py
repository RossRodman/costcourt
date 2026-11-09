from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

import pytest

from app.debate.events import DebateEvent, DebateFailed, RoundStarted
from app.debate.models import DebateReport
from app.debate.sessions import DebateManager, DebateNotFoundError, DebateSession, DebateStatus
from tests.factories import estimate
from tests.fakes import ScriptedLLM, debate_script, scripted_panel

EST = estimate()


def manager(**kwargs: Any) -> DebateManager:
    return DebateManager(**kwargs)


async def finish(session: DebateSession) -> list[DebateEvent]:
    return [e async for _, e in session.subscribe()]


async def test_debate_runs_in_the_background() -> None:
    debates = manager()
    session = debates.start(scripted_panel(ScriptedLLM(debate_script(1))), EST, rounds=1)
    assert session.status is DebateStatus.RUNNING
    assert debates.get(session.id) is session

    events = await finish(session)

    assert session.status is DebateStatus.COMPLETED
    assert session.report is not None and session.error is None
    assert events == session.events
    assert events[-1].type == "debate_completed"


async def test_late_and_resuming_subscribers_get_history() -> None:
    session = manager().start(scripted_panel(ScriptedLLM(debate_script(1))), EST, rounds=1)
    everything = await finish(session)

    replay = [i async for i, _ in session.subscribe(after=3)]
    assert replay == list(range(3, len(everything)))
    assert [e async for e in session.subscribe(after=len(everything))] == []


async def test_live_subscriber_sees_events_as_published() -> None:
    session = DebateSession(EST, rounds=1)
    received: list[str] = []

    async def follow() -> None:
        async for _, event in session.subscribe():
            received.append(event.type)

    follower = asyncio.create_task(follow())
    await session.publish(RoundStarted(round=1, total_rounds=1))
    await asyncio.sleep(0)
    assert received == ["round_started"]

    await session.publish(DebateFailed(error="boom"))
    await asyncio.wait_for(follower, 1)
    assert received == ["round_started", "debate_failed"]
    assert session.status is DebateStatus.FAILED and session.error == "boom"
    assert session.report is None

    with pytest.raises(RuntimeError, match="already finished"):
        await session.publish(RoundStarted(round=2, total_rounds=1))


async def _crashing(*_: Any, **__: Any) -> AsyncIterator[DebateEvent]:
    yield RoundStarted(round=1, total_rounds=1)
    raise RuntimeError("bug")


async def _silent(*_: Any, **__: Any) -> AsyncIterator[DebateEvent]:
    yield RoundStarted(round=1, total_rounds=1)


async def _endless(*_: Any, **__: Any) -> AsyncIterator[DebateEvent]:
    yield RoundStarted(round=1, total_rounds=1)
    await asyncio.Event().wait()


@pytest.mark.parametrize(
    ("runner", "error"),
    [
        (_crashing, "internal error while running the debate"),
        (_silent, "the debate ended without a result"),
    ],
)
async def test_broken_runner_still_terminates(runner: Any, error: str) -> None:
    session = manager(runner=runner).start(scripted_panel(ScriptedLLM()), EST, rounds=1)
    events = await finish(session)
    assert session.error == error
    assert len(events) == 2


async def test_shutdown_cancels_running_debates() -> None:
    debates = manager(runner=_endless)
    session = debates.start(scripted_panel(ScriptedLLM()), EST, rounds=1)
    await asyncio.sleep(0)

    await debates.aclose()

    assert session.error == "the server stopped this debate"


async def test_keeps_only_recent_finished_debates() -> None:
    debates = manager(max_sessions=2, runner=_endless)
    running = debates.start(scripted_panel(ScriptedLLM()), EST, rounds=1)
    finished = [
        manager().start(scripted_panel(ScriptedLLM(debate_script(1))), EST, rounds=1)
        for _ in range(2)
    ]
    for s in finished:
        await finish(s)
        debates._sessions[s.id] = s  # adopt finished sessions

    debates.start(scripted_panel(ScriptedLLM()), EST, rounds=1)

    kept = debates.list()
    assert running in kept  # still running, never evicted
    assert finished[0] not in kept
    assert kept[0].created_at >= kept[-1].created_at
    await debates.aclose()


def test_unknown_debate() -> None:
    debate_id = uuid4()
    with pytest.raises(DebateNotFoundError, match=str(debate_id)):
        manager().get(debate_id)


async def test_report_is_saved_before_completion_is_announced() -> None:
    saved: list[DebateReport] = []
    debates = manager(save_report=saved.append)
    session = debates.start(scripted_panel(ScriptedLLM(debate_script(1))), EST, rounds=1)

    async for _, event in session.subscribe():
        if event.type == "debate_completed":
            assert saved == [event.report]

    assert saved == [session.report]


async def test_failed_save_does_not_fail_the_debate(caplog: pytest.LogCaptureFixture) -> None:
    def broken(report: DebateReport) -> None:
        raise OSError("disk full")

    debates = manager(save_report=broken)
    session = debates.start(scripted_panel(ScriptedLLM(debate_script(1))), EST, rounds=1)
    await finish(session)

    assert session.status is DebateStatus.COMPLETED
    assert "could not save the report" in caplog.text
