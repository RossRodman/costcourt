from __future__ import annotations

from decimal import Decimal

import pytest

from app.debate.models import Argument, Stance
from app.estimates.models import Category, Unit
from app.reports import formatting as f


@pytest.mark.parametrize(
    ("value", "expected"),
    [("190799.27", "190,799.27"), ("0", "0.00"), ("2.5", "2.50")],
)
def test_money(value: str, expected: str) -> None:
    assert f.money(Decimal(value)) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [("27896.8", "+27,896.80"), ("-1050", "-1,050.00"), ("0", "0.00")],
)
def test_signed_money(value: str, expected: str) -> None:
    assert f.signed_money(Decimal(value)) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [("12600", "12,600"), ("12600.000", "12,600"), ("2.5", "2.5"), ("0.125", "0.125")],
)
def test_quantity(value: str, expected: str) -> None:
    assert f.quantity(Decimal(value)) == expected


def test_percentages() -> None:
    assert f.signed_percent(14.62) == "+14.62%"
    assert f.signed_percent(-3.1) == "-3.10%"
    assert f.signed_percent(0) == "0.00%"
    assert f.percent(0.82) == "82%"


def test_labels() -> None:
    assert f.unit_label(Unit.M3) == "m³"
    assert f.unit_label(Unit.LS) == "lump sum"
    assert f.category_label(Category.SITE_PREP) == "Site prep"
    assert f.category_label(Category.MEP) == "MEP"
    assert f.stance_label(Stance.MISSING) == "Missing scope"


def _arg(**figures: Decimal) -> Argument:
    stance = Stance.INCREASE if figures else Stance.SUPPORT
    return Argument(
        line_item_id="01.010",
        stance=stance,
        claim="A claim.",
        reasoning="Some reasoning.",
        **figures,
    )


def test_proposal() -> None:
    assert f.proposal(_arg()) == ""
    assert f.proposal(_arg(proposed_quantity=Decimal(504))) == "Proposes quantity 504"
    both = _arg(proposed_quantity=Decimal(504), proposed_unit_rate=Decimal(168))
    assert f.proposal(both) == "Proposes quantity 504 and unit rate 168.00"
