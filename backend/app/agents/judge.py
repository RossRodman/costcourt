"""The judge: reads the whole debate and rules on every disputed line."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import ValidationError

from app.agents.context import render_estimate, render_transcript
from app.agents.llm import Completion, LLMRequest, StructuredLLM
from app.agents.prompts import INSTRUCTIONS
from app.core.config import Effort
from app.debate.models import Role, Stance, Turn, Verdict
from app.debate.verdict import apply_verdict
from app.estimates.models import Estimate


def disputed_item_ids(transcript: Sequence[Turn]) -> list[str]:
    """Line items that at least one speaker challenged, in first-challenged order."""
    seen: dict[str, None] = {}
    for turn in transcript:
        for arg in turn.arguments:
            if arg.line_item_id and arg.stance is not Stance.SUPPORT:
                seen.setdefault(arg.line_item_id, None)
    return list(seen)


class Judge:
    role = Role.JUDGE

    def __init__(self, llm: StructuredLLM, *, model: str, effort: Effort) -> None:
        self.model = model
        self._llm = llm
        self._effort = effort

    async def rule(self, estimate: Estimate, transcript: Sequence[Turn]) -> Completion[Verdict]:
        disputed = disputed_item_ids(transcript)
        to_rule = ", ".join(disputed) if disputed else "none (rule on clear errors only, if any)"
        prompt = (
            f"## Debate transcript\n{render_transcript(transcript)}\n\n"
            f"## Your task\nIssue your verdict. Disputed line items you must rule on: {to_rule}."
        )
        request = LLMRequest(
            model=self.model,
            effort=self._effort,
            instructions=INSTRUCTIONS[Role.JUDGE],
            context=render_estimate(estimate),
            prompt=prompt,
        )
        speakers = {turn.role for turn in transcript}

        def check(verdict: Verdict) -> None:
            ruled = {r.line_item_id for r in verdict.rulings}
            problems = []
            if missing := [i for i in disputed if i not in ruled]:
                problems.append(f"no ruling for disputed line items: {', '.join(missing)}")
            for r in verdict.rulings:
                if absent := [str(role) for role in r.sided_with if role not in speakers]:
                    problems.append(
                        f"ruling on {r.line_item_id} sides with roles that did not speak: "
                        f"{', '.join(absent)}"
                    )
            if not problems:
                try:
                    apply_verdict(estimate, verdict)
                except (ValueError, ValidationError) as exc:
                    problems.append(f"the verdict cannot be applied to the estimate: {exc}")
            if problems:
                raise ValueError("; ".join(problems))

        return await self._llm.generate(request, Verdict, check)
