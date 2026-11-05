"""Run one debate end to end and yield its events as they happen."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any, cast
from uuid import UUID, uuid4

from app.agents import Panel
from app.agents.llm import LLMError
from app.debate.events import DebateCompleted, DebateEvent, DebateFailed, DebateStarted
from app.debate.graph import DebateContext, DebateInput, debate_graph
from app.debate.models import DebateReport, Role
from app.estimates.models import Estimate

log = logging.getLogger(__name__)


async def run_debate(
    panel: Panel,
    estimate: Estimate,
    *,
    rounds: int,
    debate_id: UUID | None = None,
) -> AsyncIterator[DebateEvent]:
    """Stream a debate: `debate_started`, progress events, then one terminal event.

    Never raises for agent failures; they become a `debate_failed` event so a
    client always sees the stream end cleanly.
    """
    if rounds < 1:
        raise ValueError("a debate needs at least one round")
    debate_id = debate_id or uuid4()

    yield DebateStarted(
        debate_id=debate_id,
        estimate_id=estimate.id,
        estimate_title=estimate.title,
        rounds=rounds,
        speakers=tuple(d.role for d in panel.debaters),
    )

    final: dict[str, Any] = {}
    try:
        async for mode, chunk in debate_graph().astream(
            DebateInput(estimate=estimate, rounds=rounds),
            context=DebateContext(panel=panel),
            stream_mode=["custom", "values"],
        ):
            if mode == "custom":
                yield cast(DebateEvent, chunk)
            else:
                final = cast(dict[str, Any], chunk)
        report = DebateReport(
            id=debate_id,
            estimate=estimate,
            revised_estimate=final["revised_estimate"],
            turns=tuple(final["turns"]),
            verdict=final["verdict"],
            models={
                **{d.role: d.model for d in panel.debaters},
                Role.JUDGE: panel.judge.model,
                # The model that actually answered wins (differs after a fallback).
                **{u.role: u.model for u in final["usage"]},
            },
            usage=tuple(final["usage"]),
        )
    except LLMError as exc:
        log.warning("debate %s failed: %s", debate_id, exc)
        yield DebateFailed(error=str(exc))
        return
    except Exception:
        log.exception("debate %s crashed", debate_id)
        yield DebateFailed(error="internal error while running the debate")
        return

    yield DebateCompleted(report=report)
