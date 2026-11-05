"""Test doubles for the LLM layer."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from decimal import Decimal
from typing import cast

from pydantic import BaseModel

from app.agents import Panel, build_panel
from app.agents.debater import TurnDraft
from app.agents.llm import Check, Completion, LLMRequest, T
from app.core.config import Environment, Settings
from app.debate.models import DEBATERS, Argument, Decision, Role, Ruling, Stance, Verdict


class ScriptedLLM:
    """Returns pre-written outputs in order and records every request.

    An `Exception` in the script is raised instead, to simulate API failures.

    The domain `check` is run on each output and its `ValueError` propagates,
    so tests can assert exactly what an agent would reject.
    """

    def __init__(self, outputs: Iterable[BaseModel | Exception] = ()) -> None:
        self._outputs: deque[BaseModel | Exception] = deque(outputs)
        self.requests: list[LLMRequest] = []

    def push(self, *outputs: BaseModel | Exception) -> None:
        self._outputs.extend(outputs)

    async def generate(
        self, request: LLMRequest, output: type[T], check: Check[T] | None = None
    ) -> Completion[T]:
        self.requests.append(request)
        if not self._outputs:
            raise AssertionError("ScriptedLLM ran out of outputs")
        result = self._outputs.popleft()
        if isinstance(result, Exception):
            raise result
        if not isinstance(result, output):
            raise AssertionError(f"expected {output.__name__}, script had {type(result).__name__}")
        typed = cast(T, result)
        if check is not None:
            check(typed)
        return Completion(output=typed, model=request.model, input_tokens=100, output_tokens=50)


# --------------------------------------------------------------------- debates

DISPUTED_ID = "01.010"
"""Line item the scripted debate argues about (exists in the factory estimate and the samples)."""


def turn_draft(*, rebuts: Role | None = None) -> TurnDraft:
    return TurnDraft(
        summary="The concrete quantity is understated.",
        arguments=(
            Argument(
                line_item_id=DISPUTED_ID,
                stance=Stance.INCREASE,
                claim="Quantity misses waste.",
                reasoning="Add 5% waste per standard practice.",
                proposed_quantity=Decimal("12"),
                rebuts=rebuts,
            ),
        ),
    )


def debate_script(rounds: int) -> list[BaseModel]:
    """Every output a full debate asks for, in speaking order, ending with the verdict."""
    outputs: list[BaseModel] = []
    for round_no in range(1, rounds + 1):
        outputs.append(turn_draft(rebuts=Role.ADVOCATE if round_no > 1 else None))
        outputs.extend(turn_draft() for _ in DEBATERS[1:])
    outputs.append(
        Verdict(
            summary="Waste allowance is justified; quantity raised.",
            rulings=(
                Ruling(
                    line_item_id=DISPUTED_ID,
                    decision=Decision.ADJUSTED,
                    approved_quantity=Decimal("12"),
                    reasoning="Waste is standard for ready-mix.",
                    sided_with=(Role.ENGINEER,),
                ),
            ),
            confidence=0.9,
        )
    )
    return outputs


def scripted_panel(llm: ScriptedLLM) -> Panel:
    return build_panel(Settings(env=Environment.TEST), llm)
