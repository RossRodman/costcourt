from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.debate.models import Decision
from app.debate.verdict import UnknownLineItemError, apply_verdict
from app.estimates.models import Estimate
from tests.factories import estimate, line_item, ruling, verdict


@pytest.fixture
def original() -> Estimate:
    return estimate(
        line_item(id="a", quantity=10, unit_rate=100),
        line_item(id="b", quantity=5, unit_rate=20),
        line_item(id="c", quantity=1, unit_rate=500),
    )


def test_lines_without_rulings_are_unchanged(original: Estimate) -> None:
    assert apply_verdict(original, verdict()) == original


def test_accepted_keeps_the_line(original: Estimate) -> None:
    revised = apply_verdict(original, verdict(ruling("a", Decision.ACCEPTED)))
    assert revised.item("a") == original.item("a")


def test_adjusted_rate_only(original: Estimate) -> None:
    revised = apply_verdict(
        original, verdict(ruling("a", Decision.ADJUSTED, approved_unit_rate=130))
    )
    item = revised.item("a")
    assert (item.quantity, item.unit_rate, item.total) == (10, 130, 1300)


def test_adjusted_quantity_only(original: Estimate) -> None:
    revised = apply_verdict(original, verdict(ruling("b", Decision.ADJUSTED, approved_quantity=8)))
    assert (revised.item("b").quantity, revised.item("b").unit_rate) == (8, 20)


def test_adjusted_rate_can_be_zero(original: Estimate) -> None:
    revised = apply_verdict(original, verdict(ruling("c", Decision.ADJUSTED, approved_unit_rate=0)))
    assert revised.item("c").total == 0


def test_rejected_removes_the_line(original: Estimate) -> None:
    revised = apply_verdict(original, verdict(ruling("c", Decision.REJECTED)))
    assert [i.id for i in revised.items] == ["a", "b"]
    assert revised.totals.direct_cost == Decimal(1100)


def test_original_is_not_mutated(original: Estimate) -> None:
    before = original.model_dump()
    apply_verdict(original, verdict(ruling("a", Decision.ADJUSTED, approved_unit_rate=1)))
    assert original.model_dump() == before


def test_unknown_line_item_is_an_error(original: Estimate) -> None:
    with pytest.raises(UnknownLineItemError) as exc:
        apply_verdict(original, verdict(ruling("zzz", Decision.ACCEPTED)))
    assert exc.value.item_ids == ["zzz"]


def test_rejecting_everything_is_invalid() -> None:
    est = estimate(line_item(id="a"))
    with pytest.raises(ValidationError):
        apply_verdict(est, verdict(ruling("a", Decision.REJECTED)))
