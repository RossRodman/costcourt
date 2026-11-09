"""Reusable constrained types for money, quantities and percentages.

Amounts are `Decimal` internally (no float rounding drift in totals) and are
serialised to JSON numbers so the client and LLM tooling get plain numbers.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated

from pydantic import AfterValidator, Field, PlainSerializer, WithJsonSchema

CENT = Decimal("0.01")
_QTY_STEP = Decimal("0.001")


def round_money(value: Decimal) -> Decimal:
    """Round to cents using commercial (half-up) rounding."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _round_quantity(value: Decimal) -> Decimal:
    return value.quantize(_QTY_STEP, rounding=ROUND_HALF_UP).normalize()


_as_json_number = PlainSerializer(float, return_type=float, when_used="json")
# Advertise plain numbers (not "number or string") to API clients and the LLM.
_number_schema = WithJsonSchema({"type": "number"})

Money = Annotated[
    Decimal, Field(ge=0), AfterValidator(round_money), _as_json_number, _number_schema
]
"""Non-negative amount, rounded to cents."""

SignedMoney = Annotated[Decimal, AfterValidator(round_money), _as_json_number, _number_schema]
"""Amount that may be negative (e.g. a delta between two totals)."""

Quantity = Annotated[
    Decimal, Field(gt=0), AfterValidator(_round_quantity), _as_json_number, _number_schema
]
"""Strictly positive quantity, up to three decimal places."""

Percent = Annotated[Decimal, Field(ge=0, le=100), _as_json_number, _number_schema]
"""Percentage in the 0-100 range (15 means 15 %)."""
