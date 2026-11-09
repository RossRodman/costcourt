from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.estimates.models import Estimate, EstimateSummary, Markups
from tests.factories import estimate, line_item


class TestLineItem:
    def test_total_is_quantity_times_rate_rounded_half_up(self) -> None:
        item = line_item(quantity="3.333", unit_rate="1.25")
        assert item.total == Decimal("4.17")  # 4.16625 -> 4.17

    def test_money_is_rounded_to_cents(self) -> None:
        assert line_item(unit_rate="10.005").unit_rate == Decimal("10.01")

    @pytest.mark.parametrize("quantity", [0, -1])
    def test_quantity_must_be_positive(self, quantity: int) -> None:
        with pytest.raises(ValidationError):
            line_item(quantity=quantity)

    def test_rate_cannot_be_negative(self) -> None:
        with pytest.raises(ValidationError):
            line_item(unit_rate=-1)

    def test_unknown_unit_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            line_item(unit="furlong")

    def test_is_immutable(self) -> None:
        item = line_item()
        with pytest.raises(ValidationError):
            item.quantity = Decimal(1)  # type: ignore[misc]

    def test_serialises_amounts_as_json_numbers(self) -> None:
        data = line_item(quantity="2.5", unit_rate="10").model_dump(mode="json")
        assert data["quantity"] == 2.5
        assert data["total"] == 25.0


class TestEstimate:
    def test_requires_at_least_one_item(self) -> None:
        with pytest.raises(ValidationError):
            Estimate(id="e", title="Empty", scope="Nothing to price here.", items=())

    def test_rejects_duplicate_item_ids(self) -> None:
        with pytest.raises(ValidationError, match="duplicate line item ids: a"):
            estimate(line_item(id="a"), line_item(id="a"), line_item(id="b"))

    def test_rejects_lowercase_currency(self) -> None:
        with pytest.raises(ValidationError):
            estimate(currency="usd")

    def test_item_lookup(self) -> None:
        est = estimate(line_item(id="a"), line_item(id="b", unit_rate=5))
        assert est.item("b").unit_rate == Decimal(5)
        with pytest.raises(KeyError):
            est.item("missing")

    def test_totals_without_markups(self) -> None:
        est = estimate(line_item(id="a"), line_item(id="b", quantity=2, unit_rate="50.50"))
        assert est.totals.direct_cost == Decimal("1101.00")
        assert est.totals.grand_total == Decimal("1101.00")

    def test_totals_apply_markups_in_order(self) -> None:
        est = estimate(
            line_item(quantity=1, unit_rate=1000),
            markups=Markups(overhead=10, profit=10, contingency=5, tax=20),
        )
        t = est.totals
        assert t.direct_cost == Decimal(1000)
        assert t.overhead == Decimal(100)  # 10 % of direct
        assert t.profit == Decimal(110)  # 10 % of direct + overhead
        assert t.contingency == Decimal(50)  # 5 % of direct
        assert t.subtotal == Decimal(1260)
        assert t.tax == Decimal(252)  # 20 % of subtotal
        assert t.grand_total == Decimal(1512)

    @pytest.mark.parametrize("pct", [-1, 101])
    def test_markup_percent_is_bounded(self, pct: int) -> None:
        with pytest.raises(ValidationError):
            Markups(overhead=pct)

    def test_api_output_can_be_sent_back(self) -> None:
        """Computed fields (`total`, `totals`) in the input are ignored, not rejected."""
        est = estimate(markups=Markups(tax=19))
        assert Estimate.model_validate_json(est.model_dump_json()) == est

    def test_unknown_fields_are_still_rejected(self) -> None:
        data = estimate().model_dump() | {"titel": "typo"}
        with pytest.raises(ValidationError, match="titel"):
            Estimate.model_validate(data)

    def test_summary(self) -> None:
        est = estimate(line_item(id="a"), line_item(id="b"), location="Kyiv")
        summary = EstimateSummary.of(est)
        assert summary.item_count == 2
        assert summary.location == "Kyiv"
        assert summary.grand_total == Decimal(2000)
