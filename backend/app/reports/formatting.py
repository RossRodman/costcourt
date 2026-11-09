"""Human-readable labels and numbers, shared by every export format."""

from __future__ import annotations

from decimal import Decimal

from app.agents.context import ROLE_TITLES
from app.debate.models import Argument, Decision, Role, Stance
from app.estimates.models import Category, Unit

UNIT_LABELS: dict[Unit, str] = {
    Unit.M: "m",
    Unit.M2: "m²",
    Unit.M3: "m³",
    Unit.KG: "kg",
    Unit.T: "t",
    Unit.PCS: "pcs",
    Unit.HR: "hr",
    Unit.DAY: "day",
    Unit.LS: "lump sum",
}

STANCE_LABELS: dict[Stance, str] = {
    Stance.SUPPORT: "Supports",
    Stance.INCREASE: "Increase",
    Stance.DECREASE: "Decrease",
    Stance.MISSING: "Missing scope",
}

DECISION_LABELS: dict[Decision, str] = {
    Decision.ACCEPTED: "Accepted",
    Decision.ADJUSTED: "Adjusted",
    Decision.REJECTED: "Removed",
}


def money(value: Decimal) -> str:
    """190799.27 -> '190,799.27'."""
    return f"{value:,.2f}"


def signed_money(value: Decimal) -> str:
    """27896.8 -> '+27,896.80', 0 -> '0.00'."""
    return f"{value:+,.2f}" if value else money(value)


def quantity(value: Decimal) -> str:
    """12600 -> '12,600', 2.5 -> '2.5', 0.125 -> '0.125'."""
    if value == value.to_integral_value():
        return f"{value:,.0f}"
    return f"{value.normalize():,f}"


def signed_percent(value: float) -> str:
    """14.62 -> '+14.62%', 0 -> '0.00%'."""
    return f"{value:+.2f}%" if value else "0.00%"


def percent(value: float) -> str:
    """0.82 -> '82%'."""
    return f"{value:.0%}"


def unit_label(unit: Unit) -> str:
    return UNIT_LABELS[unit]


def category_label(category: Category) -> str:
    """'site_prep' -> 'Site prep', 'mep' -> 'MEP'."""
    if category is Category.MEP:
        return "MEP"
    return category.value.replace("_", " ").capitalize()


def role_title(role: Role) -> str:
    return ROLE_TITLES[role]


def stance_label(stance: Stance) -> str:
    return STANCE_LABELS[stance]


def decision_label(decision: Decision) -> str:
    return DECISION_LABELS[decision]


def proposal(argument: Argument) -> str:
    """'Proposes quantity 504 and unit rate 168.00', or '' when it proposes nothing."""
    parts = []
    if argument.proposed_quantity is not None:
        parts.append(f"quantity {quantity(argument.proposed_quantity)}")
    if argument.proposed_unit_rate is not None:
        parts.append(f"unit rate {money(argument.proposed_unit_rate)}")
    return f"Proposes {' and '.join(parts)}" if parts else ""
