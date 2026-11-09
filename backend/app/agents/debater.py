"""A debating agent: estimator, engineer or contractor's advocate."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import Field

from app.agents.context import ROLE_TITLES, render_estimate, render_transcript
from app.agents.llm import Completion, LLMRequest, StructuredLLM
from app.agents.prompts import INSTRUCTIONS
from app.core.config import Effort
from app.core.models import DomainModel
from app.debate.models import DEBATERS, Argument, Role, Turn
from app.estimates.models import Estimate


class TurnDraft(DomainModel):
    """What the model writes; round and role are filled in by code, not trusted to the LLM."""

    summary: str = Field(
        min_length=10, max_length=1000, description="Your position this round in 1-3 sentences."
    )
    arguments: tuple[Argument, ...] = Field(
        max_length=12, description="Your arguments, most important first."
    )


def _round_brief(round_no: int, total_rounds: int) -> str:
    if round_no == 1:
        brief = "Give your opening assessment of the estimate."
    else:
        brief = (
            "Respond to what was said since your last turn: rebut, concede or refine. "
            "Do not repeat earlier arguments unless you are updating them."
        )
    if round_no == total_rounds and total_rounds > 1:
        brief += " This is the final round, so make your closing position clear."
    return brief


class Debater:
    def __init__(self, role: Role, llm: StructuredLLM, *, model: str, effort: Effort) -> None:
        if role not in DEBATERS:
            raise ValueError(f"{role} is not a debating role")
        self.role = role
        self.model = model
        self._llm = llm
        self._effort = effort

    async def take_turn(
        self,
        estimate: Estimate,
        transcript: Sequence[Turn],
        *,
        round_no: int,
        total_rounds: int,
    ) -> Completion[Turn]:
        title = ROLE_TITLES[self.role]
        prompt = (
            f"## Debate so far\n{render_transcript(transcript)}\n\n"
            f"## Your task\nRound {round_no} of {total_rounds}. You speak as the {title}. "
            f"{_round_brief(round_no, total_rounds)}"
        )
        request = LLMRequest(
            model=self.model,
            effort=self._effort,
            instructions=INSTRUCTIONS[self.role],
            context=render_estimate(estimate),
            prompt=prompt,
        )

        known_ids = {item.id for item in estimate.items}
        speakers = {turn.role for turn in transcript}

        def check(draft: TurnDraft) -> None:
            problems = []
            for arg in draft.arguments:
                if arg.line_item_id is not None and arg.line_item_id not in known_ids:
                    problems.append(f"line item '{arg.line_item_id}' does not exist")
                if arg.rebuts is self.role:
                    problems.append("you cannot rebut yourself")
                elif arg.rebuts is not None and arg.rebuts not in speakers:
                    problems.append(f"the {arg.rebuts} has not spoken yet, so you cannot rebut it")
            if problems:
                raise ValueError("; ".join(sorted(set(problems))))

        completion = await self._llm.generate(request, TurnDraft, check)
        turn = Turn(round=round_no, role=self.role, **completion.output.model_dump())
        return completion.with_output(turn)
