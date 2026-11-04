"""Small builders so tests only spell out the fields they care about."""

from __future__ import annotations

from typing import Any

from app.debate.models import Decision, Ruling, Verdict
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
