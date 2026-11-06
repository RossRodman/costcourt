"""Demo mode: replay a pre-written debate, no API key needed.

The replay goes through the real pipeline (graph, domain checks, events,
sessions, report). Only the model call is swapped for recorded output with a
short delay. It lets anyone try the UI, and shows exactly what a debate
looks like before spending tokens.
"""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Iterable
from functools import cache
from importlib import resources

from pydantic import BaseModel

from app.agents import Panel
from app.agents.debater import Debater, TurnDraft
from app.agents.judge import Judge
from app.agents.llm import Check, Completion, LLMRequest, T
from app.core.models import DomainModel
from app.debate.models import DEBATERS, Role, Verdict

DEMO_MODEL = "costcourt-demo"
_SCRIPTS_PACKAGE = "app.demo.scripts"


class DemoScript(DomainModel):
    """A recorded debate on one sample estimate."""

    estimate_id: str
    rounds: tuple[dict[Role, TurnDraft], ...]
    verdict: Verdict

    def turns_of(self, role: Role) -> list[TurnDraft]:
        return [r[role] for r in self.rounds]


class DemoNotAvailableError(LookupError):
    def __init__(self, estimate_id: str) -> None:
        super().__init__(f"no demo debate is recorded for estimate '{estimate_id}'")


class ReplayLLM:
    """`StructuredLLM` that returns recorded outputs in order, after a delay.

    Domain checks still run, so a recorded script that breaks the rules
    fails just like a real model answer would.
    """

    def __init__(self, outputs: Iterable[BaseModel], *, delay_s: float) -> None:
        self._outputs: deque[BaseModel] = deque(outputs)
        self._delay_s = delay_s

    async def generate(
        self, request: LLMRequest, output: type[T], check: Check[T] | None = None
    ) -> Completion[T]:
        if not self._outputs:
            raise RuntimeError("the demo script has no more outputs")
        await asyncio.sleep(self._delay_s)
        result = output.model_validate(self._outputs.popleft().model_dump())
        if check is not None:
            check(result)
        return Completion(output=result, model=DEMO_MODEL)


@cache
def demo_scripts() -> dict[str, DemoScript]:
    files = resources.files(_SCRIPTS_PACKAGE).iterdir()
    scripts = [
        DemoScript.model_validate_json(f.read_text(encoding="utf-8"))
        for f in files
        if f.name.endswith(".json")
    ]
    return {s.estimate_id: s for s in scripts}


def demo_panel(estimate_id: str, *, delay_s: float) -> tuple[Panel, int]:
    """A panel that replays the recorded debate, and how many rounds it has."""
    script = demo_scripts().get(estimate_id)
    if script is None:
        raise DemoNotAvailableError(estimate_id)
    panel = Panel(
        debaters=tuple(
            Debater(
                role,
                ReplayLLM(script.turns_of(role), delay_s=delay_s),
                model=DEMO_MODEL,
                effort="low",
            )
            for role in DEBATERS
        ),
        judge=Judge(ReplayLLM([script.verdict], delay_s=delay_s), model=DEMO_MODEL, effort="low"),
    )
    return panel, len(script.rounds)
