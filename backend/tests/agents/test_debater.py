from __future__ import annotations

from typing import Any

import pytest

from app.agents.debater import Debater, TurnDraft
from app.debate.models import Argument, Role, Stance, Turn
from tests.factories import estimate, line_item
from tests.fakes import ScriptedLLM

EST = estimate(line_item(id="a"), line_item(id="b"))


def arg(**overrides: Any) -> Argument:
    data: dict[str, Any] = {
        "line_item_id": "a",
        "stance": Stance.INCREASE,
        "claim": "Rate is too low.",
        "reasoning": "Market moved since the quote.",
        "proposed_unit_rate": 120,
    }
    return Argument.model_validate(data | overrides)


def draft(*arguments: Argument) -> TurnDraft:
    return TurnDraft(summary="My position this round.", arguments=arguments)


def debater(llm: ScriptedLLM, role: Role = Role.ENGINEER) -> Debater:
    return Debater(role, llm, model="claude-opus-5-5", effort="medium")


async def test_turn_gets_role_and_round_from_code() -> None:
    llm = ScriptedLLM([draft(arg())])
    completion = await debater(llm).take_turn(EST, [], round_no=1, total_rounds=2)

    turn = completion.output
    assert (turn.role, turn.round) == (Role.ENGINEER, 1)
    assert turn.arguments[0].proposed_unit_rate == 120
    assert completion.model == "claude-opus-5-5"


async def test_request_carries_role_instructions_estimate_and_transcript() -> None:
    llm = ScriptedLLM([draft()])
    earlier = [Turn(round=1, role=Role.ESTIMATOR, summary="Estimate is fine as priced.")]
    await debater(llm, Role.ADVOCATE).take_turn(EST, earlier, round_no=2, total_rounds=2)

    request = llm.requests[0]
    assert "CONTRACTOR'S ADVOCATE" in request.instructions
    assert "| a |" in request.context  # estimate goes in the cached context
    assert "Estimate is fine as priced." in request.prompt
    assert "Round 2 of 2" in request.prompt
    assert "final round" in request.prompt
    assert (request.model, request.effort) == ("claude-opus-5-5", "medium")


async def test_opening_round_brief() -> None:
    llm = ScriptedLLM([draft()])
    await debater(llm).take_turn(EST, [], round_no=1, total_rounds=3)
    assert "opening assessment" in llm.requests[0].prompt
    assert "final round" not in llm.requests[0].prompt


async def test_rejects_unknown_line_items() -> None:
    llm = ScriptedLLM([draft(arg(line_item_id="zzz"))])
    with pytest.raises(ValueError, match="line item 'zzz' does not exist"):
        await debater(llm).take_turn(EST, [], round_no=1, total_rounds=1)


async def test_missing_scope_needs_no_line_item() -> None:
    missing = arg(line_item_id=None, stance=Stance.MISSING, proposed_unit_rate=None)
    llm = ScriptedLLM([draft(missing)])
    completion = await debater(llm).take_turn(EST, [], round_no=1, total_rounds=1)
    assert completion.output.arguments[0].line_item_id is None


async def test_cannot_rebut_itself() -> None:
    llm = ScriptedLLM([draft(arg(rebuts=Role.ENGINEER))])
    with pytest.raises(ValueError, match="cannot rebut yourself"):
        await debater(llm).take_turn(EST, [], round_no=1, total_rounds=1)


async def test_cannot_rebut_someone_who_has_not_spoken() -> None:
    llm = ScriptedLLM([draft(arg(rebuts=Role.ADVOCATE))])
    with pytest.raises(ValueError, match="advocate has not spoken"):
        await debater(llm).take_turn(EST, [], round_no=1, total_rounds=1)


async def test_can_rebut_an_earlier_speaker() -> None:
    llm = ScriptedLLM([draft(arg(rebuts=Role.ESTIMATOR))])
    earlier = [Turn(round=1, role=Role.ESTIMATOR, summary="Estimate is fine as priced.")]
    completion = await debater(llm).take_turn(EST, earlier, round_no=1, total_rounds=1)
    assert completion.output.arguments[0].rebuts is Role.ESTIMATOR


def test_judge_is_not_a_debater() -> None:
    with pytest.raises(ValueError, match="not a debating role"):
        Debater(Role.JUDGE, ScriptedLLM(), model="m", effort="low")
