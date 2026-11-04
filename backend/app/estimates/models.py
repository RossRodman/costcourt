"""Construction estimate domain model."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
from enum import StrEnum
from typing import Self

from pydantic import Field, computed_field, model_validator

from app.core.models import DomainModel
from app.core.types import Money, Percent, Quantity, round_money

_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"


class Unit(StrEnum):
    M = "m"
    M2 = "m2"
    M3 = "m3"
    KG = "kg"
    T = "t"
    PCS = "pcs"
    HR = "hr"
    DAY = "day"
    LS = "ls"
    """Lump sum."""


class Category(StrEnum):
    SITE_PREP = "site_prep"
    EARTHWORKS = "earthworks"
    CONCRETE = "concrete"
    MASONRY = "masonry"
    STEEL = "steel"
    CARPENTRY = "carpentry"
    ROOFING = "roofing"
    MEP = "mep"
    """Mechanical, electrical and plumbing."""
    FINISHES = "finishes"
    EQUIPMENT = "equipment"
    GENERAL = "general"


class LineItem(DomainModel):
    """One priced line of an estimate."""

    id: str = Field(pattern=_ID_PATTERN, examples=["03.010"])
    description: str = Field(min_length=3, max_length=300)
    category: Category
    unit: Unit
    quantity: Quantity
    unit_rate: Money
    notes: str | None = Field(default=None, max_length=1000)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total(self) -> Money:
        return round_money(self.quantity * self.unit_rate)


class Markups(DomainModel):
    """Percentages applied on top of direct cost."""

    overhead: Percent = Decimal(0)
    """Site and head-office overhead, on direct cost."""
    profit: Percent = Decimal(0)
    """Contractor margin, on direct cost + overhead."""
    contingency: Percent = Decimal(0)
    """Risk allowance, on direct cost."""
    tax: Percent = Decimal(0)
    """VAT / sales tax, on everything above."""


class EstimateTotals(DomainModel):
    direct_cost: Money
    overhead: Money
    profit: Money
    contingency: Money
    subtotal: Money
    tax: Money
    grand_total: Money


class Estimate(DomainModel):
    """A full construction estimate: scope, priced line items and markups."""

    id: str = Field(pattern=_ID_PATTERN)
    title: str = Field(min_length=3, max_length=200)
    scope: str = Field(min_length=10, max_length=4000)
    """Plain-language description of the work, given to every agent."""
    location: str | None = Field(default=None, max_length=200)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    items: tuple[LineItem, ...] = Field(min_length=1, max_length=500)
    markups: Markups = Markups()

    @model_validator(mode="after")
    def _unique_item_ids(self) -> Self:
        counts = Counter(item.id for item in self.items)
        duplicates = [item_id for item_id, n in counts.items() if n > 1]
        if duplicates:
            raise ValueError(f"duplicate line item ids: {', '.join(sorted(duplicates))}")
        return self

    def item(self, item_id: str) -> LineItem:
        for item in self.items:
            if item.id == item_id:
                return item
        raise KeyError(item_id)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def totals(self) -> EstimateTotals:
        m = self.markups
        direct = sum((i.total for i in self.items), Decimal(0))
        overhead = round_money(direct * m.overhead / 100)
        profit = round_money((direct + overhead) * m.profit / 100)
        contingency = round_money(direct * m.contingency / 100)
        subtotal = direct + overhead + profit + contingency
        tax = round_money(subtotal * m.tax / 100)
        return EstimateTotals(
            direct_cost=direct,
            overhead=overhead,
            profit=profit,
            contingency=contingency,
            subtotal=subtotal,
            tax=tax,
            grand_total=subtotal + tax,
        )


class EstimateSummary(DomainModel):
    """Lightweight listing entry."""

    id: str
    title: str
    location: str | None
    currency: str
    item_count: int
    grand_total: Money

    @classmethod
    def of(cls, estimate: Estimate) -> EstimateSummary:
        return cls(
            id=estimate.id,
            title=estimate.title,
            location=estimate.location,
            currency=estimate.currency,
            item_count=len(estimate.items),
            grand_total=estimate.totals.grand_total,
        )
