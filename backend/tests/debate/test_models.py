from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from app.debate.models import (
    Argument,
    CostImpact,
    DebateReport,
    Decision,
    Role,
    Stance,
    Turn,
    Verdict,
)
from tests.factories import estimate, line_item, ruling, verdict


def argument(stance: Stance, **overrides: Any) -> Argument:
    data: dict[str, Any] = {
        "line_item_id": "01.010",
        "stance": stance,
        "claim": "The rate is off.",
        "reasoning": "Market rates moved since the quote.",
    }
    return Argument.model_validate(data | overrides)


class TestArgument:
    @pytest.mark.parametrize("stance", [Stance.INCREASE, Stance.DECREASE])
    def test_changing_stances_must_propose_figures(self, stance: Stance) -> None:
        with pytest.raises(ValidationError, match="must propose"):
            argument(stance)
        assert argument(stance, proposed_unit_rate=150).proposed_unit_rate == Decimal(150)

    def test_support_cannot_propose_figures(self) -> None:
        with pytest.raises(ValidationError, match="cannot propose"):
            argument(Stance.SUPPORT, proposed_quantity=5)

    def test_missing_scope_needs_no_figures(self) -> None:
        assert argument(Stance.MISSING).stance is Stance.MISSING


class TestTurn:
    def test_judge_cannot_take_a_turn(self) -> None:
        with pytest.raises(ValidationError, match="judge"):
            Turn(round=1, role=Role.JUDGE, summary="I am the judge here.")

    def test_rounds_start_at_one(self) -> None:
        with pytest.raises(ValidationError):
            Turn(round=0, role=Role.ENGINEER, summary="Opening statement.")


class TestRuling:
    def test_adjusted_requires_figures(self) -> None:
        with pytest.raises(ValidationError, match="must set"):
            ruling("a", Decision.ADJUSTED)

    @pytest.mark.parametrize("decision", [Decision.ACCEPTED, Decision.REJECTED])
    def test_other_decisions_cannot_set_figures(self, decision: Decision) -> None:
        with pytest.raises(ValidationError, match="cannot set"):
            ruling("a", decision, approved_unit_rate=1)

    def test_judge_cannot_side_with_itself(self) -> None:
        with pytest.raises(ValidationError, match="itself"):
            ruling("a", Decision.ACCEPTED, sided_with=[Role.JUDGE])


class TestVerdict:
    def test_one_ruling_per_item(self) -> None:
        with pytest.raises(ValidationError, match="once"):
            verdict(ruling("a", Decision.ACCEPTED), ruling("a", Decision.REJECTED))

    @pytest.mark.parametrize("confidence", [-0.1, 1.1])
    def test_confidence_is_bounded(self, confidence: float) -> None:
        with pytest.raises(ValidationError):
            Verdict(summary="A summary that is long enough.", rulings=(), confidence=confidence)


class TestCostImpact:
    def test_delta(self) -> None:
        impact = CostImpact(original_total=Decimal(1000), revised_total=Decimal(1150))
        assert impact.delta == Decimal(150)
        assert impact.delta_pct == 15.0

    def test_delta_can_be_negative(self) -> None:
        impact = CostImpact(original_total=Decimal(1000), revised_total=Decimal(900))
        assert impact.delta == Decimal(-100)
        assert impact.delta_pct == -10.0

    def test_zero_original_total(self) -> None:
        assert CostImpact(original_total=0, revised_total=10).delta_pct == 0.0  # type: ignore[arg-type]


def test_report_derives_rounds_and_impact() -> None:
    original = estimate(line_item(id="a", quantity=10, unit_rate=100))
    revised = estimate(line_item(id="a", quantity=10, unit_rate=120))
    report = DebateReport(
        estimate=original,
        revised_estimate=revised,
        turns=(
            Turn(round=1, role=Role.ESTIMATOR, summary="The estimate is sound."),
            Turn(round=2, role=Role.ENGINEER, summary="Concrete rate is stale."),
        ),
        verdict=verdict(ruling("a", Decision.ADJUSTED, approved_unit_rate=120)),
        models={Role.JUDGE: "claude-opus-5-5"},
    )
    assert report.rounds == 2
    assert report.impact.delta == Decimal(200)
    dumped = report.model_dump(mode="json")
    assert dumped["impact"]["delta_pct"] == 20.0
    assert dumped["models"] == {"judge": "claude-opus-5-5"}
