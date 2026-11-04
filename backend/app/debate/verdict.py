"""Turning the judge's rulings into a revised estimate."""

from __future__ import annotations

from app.debate.models import Decision, Verdict
from app.estimates.models import Estimate, LineItem


class UnknownLineItemError(ValueError):
    def __init__(self, item_ids: list[str]) -> None:
        super().__init__(f"verdict rules on unknown line items: {', '.join(item_ids)}")
        self.item_ids = item_ids


def apply_verdict(estimate: Estimate, verdict: Verdict) -> Estimate:
    """Return a new estimate with every ruling applied.

    Lines without a ruling, and lines ruled `accepted`, are kept as-is.
    `adjusted` lines take the approved quantity and/or rate; `rejected` lines
    are dropped. The original estimate is never mutated.
    """
    known = {item.id for item in estimate.items}
    unknown = [r.line_item_id for r in verdict.rulings if r.line_item_id not in known]
    if unknown:
        raise UnknownLineItemError(unknown)

    rulings = {r.line_item_id: r for r in verdict.rulings}
    revised: list[LineItem] = []

    for item in estimate.items:
        ruling = rulings.get(item.id)
        if ruling is None or ruling.decision is Decision.ACCEPTED:
            revised.append(item)
        elif ruling.decision is Decision.ADJUSTED:
            revised.append(
                item.model_copy(
                    update={
                        "quantity": ruling.approved_quantity or item.quantity,
                        "unit_rate": (
                            item.unit_rate
                            if ruling.approved_unit_rate is None
                            else ruling.approved_unit_rate
                        ),
                    }
                )
            )
        # Decision.REJECTED: the line is removed.

    # Validate again so a verdict that rejects every line fails loudly.
    return Estimate.model_validate(estimate.model_dump() | {"items": revised})
