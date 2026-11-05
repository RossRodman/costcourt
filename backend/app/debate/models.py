"""What the debate produces: arguments, rulings, the verdict and the report.

These models double as the structured-output contracts the agents must fill
in, so field descriptions are written for the LLM as much as for humans.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Self
from uuid import UUID, uuid4

from pydantic import Field, computed_field, model_validator

from app.core.models import DomainModel
from app.core.types import Money, Quantity, SignedMoney
from app.estimates.models import Estimate


class Role(StrEnum):
    ESTIMATOR = "estimator"
    ENGINEER = "engineer"
    ADVOCATE = "advocate"
    """The contractor's advocate."""
    JUDGE = "judge"


DEBATERS: tuple[Role, ...] = (Role.ESTIMATOR, Role.ENGINEER, Role.ADVOCATE)


class Stance(StrEnum):
    SUPPORT = "support"
    """The line is correct as priced."""
    INCREASE = "increase"
    """Quantity or rate is too low."""
    DECREASE = "decrease"
    """Quantity or rate is too high."""
    MISSING = "missing"
    """Scope is missing from the estimate."""


class Decision(StrEnum):
    ACCEPTED = "accepted"
    ADJUSTED = "adjusted"
    REJECTED = "rejected"
    """The line should be removed from the estimate."""


# --------------------------------------------------------------------- debate


class Argument(DomainModel):
    """A single point an agent makes about one line item."""

    line_item_id: str | None = Field(
        description="Id of the line item this argument is about; null only for 'missing' scope."
    )
    stance: Stance
    claim: str = Field(min_length=5, max_length=300, description="One-sentence position.")
    reasoning: str = Field(
        min_length=10, max_length=2000, description="Why: norms, market rates, site conditions."
    )
    proposed_quantity: Quantity | None = Field(
        default=None, description="Quantity the agent believes is right, if different."
    )
    proposed_unit_rate: Money | None = Field(
        default=None, description="Unit rate the agent believes is right, if different."
    )
    rebuts: Role | None = Field(
        default=None, description="Role whose earlier argument this one answers, if any."
    )

    @model_validator(mode="after")
    def _proposal_matches_stance(self) -> Self:
        if self.line_item_id is None and self.stance is not Stance.MISSING:
            raise ValueError(f"a '{self.stance}' argument must reference a line item")
        proposes = self.proposed_quantity is not None or self.proposed_unit_rate is not None
        if self.stance in (Stance.INCREASE, Stance.DECREASE) and not proposes:
            raise ValueError(f"a '{self.stance}' argument must propose a quantity or unit rate")
        if self.stance is Stance.SUPPORT and proposes:
            raise ValueError("a 'support' argument cannot propose new figures")
        return self


class Turn(DomainModel):
    """Everything one debater said in one round."""

    round: int = Field(ge=1)
    role: Role
    summary: str = Field(min_length=10, max_length=1000, description="Position in 1-3 sentences.")
    arguments: tuple[Argument, ...] = Field(default=(), max_length=50)

    @model_validator(mode="after")
    def _judge_does_not_debate(self) -> Self:
        if self.role is Role.JUDGE:
            raise ValueError("the judge rules, it does not take debate turns")
        return self


# --------------------------------------------------------------------- verdict


class Ruling(DomainModel):
    """The judge's decision on one disputed line item."""

    line_item_id: str
    decision: Decision
    approved_quantity: Quantity | None = None
    approved_unit_rate: Money | None = None
    reasoning: str = Field(min_length=10, max_length=2000)
    sided_with: tuple[Role, ...] = Field(
        default=(), description="Debaters whose arguments the ruling mainly follows."
    )

    @model_validator(mode="after")
    def _figures_match_decision(self) -> Self:
        has_figures = self.approved_quantity is not None or self.approved_unit_rate is not None
        if self.decision is Decision.ADJUSTED and not has_figures:
            raise ValueError("an 'adjusted' ruling must set a quantity or unit rate")
        if self.decision is not Decision.ADJUSTED and has_figures:
            raise ValueError(f"an '{self.decision}' ruling cannot set new figures")
        if Role.JUDGE in self.sided_with:
            raise ValueError("the judge cannot side with itself")
        return self


class Verdict(DomainModel):
    """The judge's full decision."""

    summary: str = Field(min_length=20, max_length=3000)
    rulings: tuple[Ruling, ...]
    confidence: float = Field(ge=0, le=1, description="0-1: how sure the judge is overall.")
    recommendations: tuple[str, ...] = Field(
        default=(), max_length=20, description="Follow-ups for the client, e.g. get a quote."
    )

    @model_validator(mode="after")
    def _one_ruling_per_item(self) -> Self:
        ids = [r.line_item_id for r in self.rulings]
        if len(ids) != len(set(ids)):
            raise ValueError("each line item can only be ruled on once")
        return self


# --------------------------------------------------------------------- report


class CostImpact(DomainModel):
    original_total: Money
    revised_total: Money

    @computed_field  # type: ignore[prop-decorator]
    @property
    def delta(self) -> SignedMoney:
        return self.revised_total - self.original_total

    @computed_field  # type: ignore[prop-decorator]
    @property
    def delta_pct(self) -> float:
        if not self.original_total:
            return 0.0
        return round(float(self.delta / self.original_total * 100), 2)


class DebateReport(DomainModel):
    """The full audit trail: input, every turn, the verdict and its effect."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    estimate: Estimate
    revised_estimate: Estimate
    turns: tuple[Turn, ...]
    verdict: Verdict
    models: dict[Role, str] = Field(default_factory=dict, description="Model used per role.")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def impact(self) -> CostImpact:
        return CostImpact(
            original_total=self.estimate.totals.grand_total,
            revised_total=self.revised_estimate.totals.grand_total,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def rounds(self) -> int:
        return max((t.round for t in self.turns), default=0)
