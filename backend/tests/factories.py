"""Small builders so tests only spell out the fields they care about."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.debate.models import (
    Argument,
    DebateReport,
    Decision,
    LLMUsage,
    Role,
    Ruling,
    Stance,
    Turn,
    Verdict,
)
from app.debate.verdict import apply_verdict
from app.estimates.models import Estimate, LineItem


def line_item(**overrides: Any) -> LineItem:
    data: dict[str, Any] = {
        "id": "01.010",
        "description": "Ready-mix concrete",
        "category": "concrete",
        "unit": "m3",
        "quantity": 10,
        "unit_rate": 100,
    }
    return LineItem.model_validate(data | overrides)


def estimate(*items: LineItem, **overrides: Any) -> Estimate:
    data: dict[str, Any] = {
        "id": "test-estimate",
        "title": "Test estimate",
        "scope": "A small concrete job used in tests.",
        "items": items or (line_item(),),
    }
    return Estimate.model_validate(data | overrides)


def ruling(line_item_id: str, decision: Decision, **overrides: Any) -> Ruling:
    data: dict[str, Any] = {
        "line_item_id": line_item_id,
        "decision": decision,
        "reasoning": "Reasoning given by the judge.",
    }
    return Ruling.model_validate(data | overrides)


def verdict(*rulings: Ruling) -> Verdict:
    return Verdict(
        summary="The judge's overall summary of the debate.",
        rulings=rulings,
        confidence=0.8,
    )


def debate_report(**overrides: Any) -> DebateReport:
    """A small finished debate: one line adjusted, one removed, one untouched,
    one missing-scope argument, and user text that needs escaping."""
    est = estimate(
        line_item(id="01.010", description="Concrete <b>C30</b> | slab"),
        line_item(id="02.010", description="Formwork", unit="m2", quantity=50, unit_rate=20),
        line_item(id="03.010", description="Curing", unit="m2", quantity=50, unit_rate=1),
        title="Garage <script>alert(1)</script>",
        location="Leeds | UK",
    )
    adjusted = ruling(
        "01.010",
        Decision.ADJUSTED,
        approved_quantity=12,
        approved_unit_rate=110,
        sided_with=(Role.ENGINEER,),
    )
    rejected = ruling("02.010", Decision.REJECTED, reasoning="Formwork is <em>not</em> needed.")
    v = verdict(adjusted, rejected)
    turns = (
        Turn(
            round=1,
            role=Role.ESTIMATOR,
            summary="The estimate is right as priced.",
            arguments=(
                Argument(
                    line_item_id="01.010",
                    stance=Stance.SUPPORT,
                    claim="Ten cubic metres is enough.",
                    reasoning="Matches the drawings exactly.",
                ),
            ),
        ),
        Turn(
            round=1,
            role=Role.ENGINEER,
            summary="Concrete is short and curing blankets are missing.",
            arguments=(
                Argument(
                    line_item_id="01.010",
                    stance=Stance.INCREASE,
                    claim="Allow waste and a winter rate.",
                    reasoning="Five percent waste is standard.",
                    proposed_quantity=Decimal(12),
                    proposed_unit_rate=Decimal(110),
                    rebuts=Role.ESTIMATOR,
                ),
                Argument(
                    line_item_id=None,
                    stance=Stance.MISSING,
                    claim="Winter blankets are not priced.",
                    reasoning="Pours may happen in January.",
                ),
            ),
        ),
    )
    data: dict[str, Any] = {
        "estimate": est,
        "revised_estimate": apply_verdict(est, v),
        "turns": turns,
        "verdict": v,
        "models": {Role.ESTIMATOR: "claude-opus-5-5", Role.JUDGE: "claude-opus-5-5"},
        "usage": (
            LLMUsage(
                role=Role.ESTIMATOR,
                round=1,
                model="claude-opus-5-5",
                input_tokens=1200,
                output_tokens=300,
                cache_read_tokens=900,
            ),
            LLMUsage(
                role=Role.JUDGE, model="claude-opus-5-5", input_tokens=2000, output_tokens=500
            ),
        ),
    }
    return DebateReport.model_validate(data | overrides)
