"""Debates running in the background, with replayable event logs.

A client starts a debate with one request and follows it with another
(server-sent events). Every event is kept, so a client that connects late or
reconnects gets the full history first, then live events.

State is in memory: fine for a single-process app, swap for Redis/Postgres
to scale out.
"""

from __future__ import annotations

import asyncio
import logging
from collections import OrderedDict
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime
from enum import StrEnum
from functools import partial
from uuid import UUID, uuid4

from app.agents import Panel
from app.debate.events import DebateCompleted, DebateEvent, DebateFailed
from app.debate.models import DebateReport
from app.debate.runner import run_debate
from app.estimates.models import Estimate

log = logging.getLogger(__name__)

Runner = Callable[..., AsyncIterator[DebateEvent]]


class DebateStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class DebateNotFoundError(KeyError):
    def __init__(self, debate_id: UUID) -> None:
        super().__init__(f"no debate with id {debate_id}")
        self.debate_id = debate_id

    def __str__(self) -> str:
        return str(self.args[0])


class DebateSession:
    """One debate: its input, its event log and its outcome."""

    def __init__(self, estimate: Estimate, rounds: int) -> None:
        self.id = uuid4()
        self.created_at = datetime.now(UTC)
        self.estimate = estimate
        self.rounds = rounds
        self.events: list[DebateEvent] = []
        self._changed = asyncio.Condition()

    @property
    def status(self) -> DebateStatus:
        last = self.events[-1] if self.events else None
        if isinstance(last, DebateCompleted):
            return DebateStatus.COMPLETED
        if isinstance(last, DebateFailed):
            return DebateStatus.FAILED
        return DebateStatus.RUNNING

    @property
    def done(self) -> bool:
        return self.status is not DebateStatus.RUNNING

    @property
    def report(self) -> DebateReport | None:
        last = self.events[-1] if self.events else None
        return last.report if isinstance(last, DebateCompleted) else None

    @property
    def error(self) -> str | None:
        last = self.events[-1] if self.events else None
        return last.error if isinstance(last, DebateFailed) else None

    async def publish(self, event: DebateEvent) -> None:
        if self.done:
            raise RuntimeError("debate already finished")
        async with self._changed:
            self.events.append(event)
            self._changed.notify_all()

    def _ready(self, index: int) -> bool:
        return index < len(self.events) or self.done

    async def subscribe(self, after: int = 0) -> AsyncIterator[tuple[int, DebateEvent]]:
        """Yield `(index, event)` from `after` onwards, live, until the debate ends."""
        index = max(after, 0)
        while True:
            async with self._changed:
                await self._changed.wait_for(partial(self._ready, index))
                batch = self.events[index:]
            for event in batch:
                yield index, event
                index += 1
            if self.done and index >= len(self.events):
                return


class DebateManager:
    """Starts debates as background tasks and keeps the most recent ones."""

    def __init__(self, *, max_sessions: int = 100, runner: Runner = run_debate) -> None:
        self._sessions: OrderedDict[UUID, DebateSession] = OrderedDict()
        self._tasks: set[asyncio.Task[None]] = set()
        self._max_sessions = max_sessions
        self._runner = runner

    def start(self, panel: Panel, estimate: Estimate, *, rounds: int) -> DebateSession:
        session = DebateSession(estimate, rounds)
        self._sessions[session.id] = session
        self._evict()
        task = asyncio.create_task(self._run(session, panel), name=f"debate-{session.id}")
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return session

    def get(self, debate_id: UUID) -> DebateSession:
        try:
            return self._sessions[debate_id]
        except KeyError:
            raise DebateNotFoundError(debate_id) from None

    def list(self) -> list[DebateSession]:
        """Newest first."""
        return list(reversed(self._sessions.values()))

    async def aclose(self) -> None:
        """Cancel running debates (on shutdown)."""
        for task in list(self._tasks):
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def _run(self, session: DebateSession, panel: Panel) -> None:
        try:
            async for event in self._runner(
                panel, session.estimate, rounds=session.rounds, debate_id=session.id
            ):
                await session.publish(event)
        except asyncio.CancelledError:
            if not session.done:
                await session.publish(DebateFailed(error="the server stopped this debate"))
            raise
        except Exception:
            log.exception("debate %s runner crashed", session.id)
            if not session.done:
                await session.publish(DebateFailed(error="internal error while running the debate"))
        else:
            if not session.done:
                await session.publish(DebateFailed(error="the debate ended without a result"))

    def _evict(self) -> None:
        """Drop the oldest finished debates once over capacity."""
        for debate_id in list(self._sessions):
            if len(self._sessions) <= self._max_sessions:
                break
            if self._sessions[debate_id].done:
                del self._sessions[debate_id]
