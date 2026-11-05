"""The four agents (estimator, engineer, advocate, judge) and their LLM access."""

from __future__ import annotations

from dataclasses import dataclass

from app.agents.debater import Debater
from app.agents.judge import Judge
from app.agents.llm import ClaudeLLM, StructuredLLM
from app.core.config import Settings
from app.debate.models import DEBATERS


@dataclass(frozen=True, slots=True)
class Panel:
    """Everyone needed to run one debate, speaking in `debaters` order."""

    debaters: tuple[Debater, ...]
    judge: Judge


def build_panel(settings: Settings, llm: StructuredLLM | None = None) -> Panel:
    """Assemble the panel from settings. Pass `llm` to use a fake in tests."""
    llm = llm or ClaudeLLM.from_settings(settings)
    return Panel(
        debaters=tuple(
            Debater(role, llm, model=settings.debater_model, effort=settings.debater_effort)
            for role in DEBATERS
        ),
        judge=Judge(llm, model=settings.judge_model, effort=settings.judge_effort),
    )


__all__ = ["Debater", "Judge", "Panel", "build_panel"]
