from __future__ import annotations

import pytest

from app.agents.judge import Judge, disputed_item_ids
from app.debate.models import Argument, Decision, Role, Stance, Turn
from tests.factories import estimate, line_item, ruling, verdict
from tests.fakes import ScriptedLLM

EST = estimate(line_item(id="a"), line_item(id="b"), line_item(id="c"))


def turn(role: Role, *arguments: Argument) -> Turn:
    return Turn(round=1, role=role, summary="Position for this round.", arguments=arguments)


def challenge(item: str) -> Argument:
    return Argument(
        line_item_id=item,
        stance=Stance.DECREASE,
        claim="Too high.",
        reasoning="Quantity double-counted.",
        proposed_quantity=5,  # type: ignore[arg-type]
    )


def support(item: str) -> Argument:
    return Argument(
        line_item_id=item, stance=Stance.SUPPORT, claim="Correct.", reasoning="Matches take-off."
    )


TRANSCRIPT = [
    turn(Role.ESTIMATOR, support("a"), support("b")),
    turn(Role.ENGINEER, challenge("b"), challenge("a")),
    turn(Role.ADVOCATE, challenge("b")),
]


def judge(llm: ScriptedLLM) -> Judge:
    return Judge(llm, model="claude-opus-5-5", effort="high")


def test_disputed_ids_ignore_support_and_keep_order() -> None:
    assert disputed_item_ids(TRANSCRIPT) == ["b", "a"]


async def test_valid_verdict_is_returned() -> None:
    v = verdict(
        ruling("a", Decision.ACCEPTED, sided_with=[Role.ESTIMATOR]),
        ruling("b", Decision.ADJUSTED, approved_quantity=5, sided_with=[Role.ENGINEER]),
    )
    llm = ScriptedLLM([v])
    completion = await judge(llm).rule(EST, TRANSCRIPT)

    assert completion.output == v
    request = llm.requests[0]
    assert "must rule on: b, a" in request.prompt
    assert "Too high." in request.prompt
    assert (request.model, request.effort) == ("claude-opus-5-5", "high")


async def test_every_disputed_line_needs_a_ruling() -> None:
    llm = ScriptedLLM([verdict(ruling("b", Decision.ACCEPTED))])
    with pytest.raises(ValueError, match="no ruling for disputed line items: a"):
        await judge(llm).rule(EST, TRANSCRIPT)


async def test_cannot_side_with_a_silent_role() -> None:
    short = [turn(Role.ENGINEER, challenge("a"))]
    llm = ScriptedLLM([verdict(ruling("a", Decision.ACCEPTED, sided_with=[Role.ADVOCATE]))])
    with pytest.raises(ValueError, match="did not speak: advocate"):
        await judge(llm).rule(EST, short)


async def test_rulings_on_unknown_items_are_rejected() -> None:
    llm = ScriptedLLM(
        [
            verdict(
                ruling("a", Decision.ACCEPTED),
                ruling("b", Decision.ACCEPTED),
                ruling("x", Decision.ACCEPTED),
            )
        ]
    )
    with pytest.raises(ValueError, match="cannot be applied"):
        await judge(llm).rule(EST, TRANSCRIPT)


async def test_cannot_reject_every_line() -> None:
    llm = ScriptedLLM([verdict(*(ruling(i, Decision.REJECTED) for i in ("a", "b", "c")))])
    with pytest.raises(ValueError, match="cannot be applied"):
        await judge(llm).rule(EST, TRANSCRIPT)


async def test_no_disputes() -> None:
    llm = ScriptedLLM([verdict()])
    await judge(llm).rule(EST, [turn(Role.ESTIMATOR, support("a"))])
    assert "none (rule on clear errors only" in llm.requests[0].prompt
