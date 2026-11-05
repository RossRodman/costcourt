from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest

from app.agents.llm import LLMUnavailableError
from app.debate.events import (
    DebateCompleted,
    DebateEvent,
    DebateFailed,
    DebateStarted,
    JudgeStarted,
    TurnCompleted,
    TurnStarted,
    VerdictReached,
)
from app.debate.graph import debate_graph
from app.debate.models import DEBATERS, Role
from app.debate.runner import run_debate
from tests.factories import estimate, line_item
from tests.fakes import DISPUTED_ID, ScriptedLLM, debate_script, scripted_panel

EST = estimate(line_item(id=DISPUTED_ID), line_item(id="01.020"))


async def collect(llm: ScriptedLLM, rounds: int, **kwargs: Any) -> list[DebateEvent]:
    return [e async for e in run_debate(scripted_panel(llm), EST, rounds=rounds, **kwargs)]


def test_graph_shape() -> None:
    graph = debate_graph().get_graph()
    nodes = set(graph.nodes) - {"__start__", "__end__"}
    assert nodes == {"open_round", "judge", *(r.value for r in DEBATERS)}
    assert debate_graph() is debate_graph()  # compiled once


async def test_two_round_debate_event_sequence() -> None:
    llm = ScriptedLLM(debate_script(rounds=2))
    events = await collect(llm, rounds=2)

    speaking = [r.value for r in DEBATERS]
    assert [e.type for e in events] == [
        "debate_started",
        *(["round_started"] + ["turn_started", "turn_completed"] * 3) * 2,
        "judge_started",
        "verdict_reached",
        "debate_completed",
    ]
    turns = [e for e in events if isinstance(e, TurnStarted)]
    assert [(t.round, t.role.value) for t in turns] == [
        (r, role) for r in (1, 2) for role in speaking
    ]
    started = events[0]
    assert isinstance(started, DebateStarted)
    assert started.speakers == DEBATERS
    judge_started = next(e for e in events if isinstance(e, JudgeStarted))
    assert judge_started.disputed_item_ids == (DISPUTED_ID,)


async def test_report_carries_the_whole_trail() -> None:
    debate_id = uuid4()
    llm = ScriptedLLM(debate_script(rounds=2))
    events = await collect(llm, rounds=2, debate_id=debate_id)

    done = events[-1]
    assert isinstance(done, DebateCompleted)
    report = done.report
    assert report.id == debate_id
    assert report.rounds == 2
    assert len(report.turns) == 6
    assert report.turns == tuple(e.turn for e in events if isinstance(e, TurnCompleted))
    assert report.verdict == next(e.verdict for e in events if isinstance(e, VerdictReached))
    assert report.revised_estimate.item(DISPUTED_ID).quantity == Decimal("12")
    assert report.impact.delta > 0
    assert len(report.usage) == 7
    assert report.usage[-1].role is Role.JUDGE and report.usage[-1].round is None
    assert set(report.models) == {*DEBATERS, Role.JUDGE}


async def test_later_turns_see_the_transcript() -> None:
    llm = ScriptedLLM(debate_script(rounds=2))
    await collect(llm, rounds=2)

    first, *_, fourth, _, _, judge = llm.requests
    assert "Quantity misses waste" not in first.prompt
    assert "Round 2 of 2" in fourth.prompt
    assert "Quantity misses waste" in fourth.prompt
    assert judge.instructions != first.instructions


async def test_single_round_goes_straight_to_the_judge() -> None:
    events = await collect(ScriptedLLM(debate_script(rounds=1)), rounds=1)
    assert sum(isinstance(e, TurnCompleted) for e in events) == 3
    assert isinstance(events[-1], DebateCompleted)


async def test_llm_failure_ends_with_debate_failed() -> None:
    script = debate_script(rounds=1)
    script[1] = LLMUnavailableError("Claude API call failed: overloaded")
    events = await collect(ScriptedLLM(script), rounds=1)

    assert isinstance(events[-1], DebateFailed)
    assert events[-1].error == "Claude API call failed: overloaded"
    assert sum(isinstance(e, TurnCompleted) for e in events) == 1


async def test_unexpected_error_is_not_leaked() -> None:
    script = debate_script(rounds=1)
    script[0] = RuntimeError("secret internals")
    events = await collect(ScriptedLLM(script), rounds=1)

    assert isinstance(events[-1], DebateFailed)
    assert "secret" not in events[-1].error


async def test_rounds_must_be_positive() -> None:
    with pytest.raises(ValueError, match="at least one round"):
        await collect(ScriptedLLM(), rounds=0)
