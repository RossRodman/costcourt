"""Render domain objects as compact, deterministic prompt text.

Output must be byte-stable for the same input (no timestamps, no random
ordering) so the estimate block is served from the prompt cache.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from app.debate.models import Argument, Role, Turn
from app.estimates.models import Estimate

ROLE_TITLES: dict[Role, str] = {
    Role.ESTIMATOR: "Estimator",
    Role.ENGINEER: "Engineer",
    Role.ADVOCATE: "Contractor's advocate",
    Role.JUDGE: "Judge",
}


def _num(value: Decimal) -> str:
    """12500 -> '12,500', 2.8 -> '2.80', 0.125 -> '0.125'."""
    if value == value.to_integral_value():
        return f"{value:,.0f}"
    places = max(2, -int(value.normalize().as_tuple().exponent))
    return f"{value:,.{places}f}"


def render_estimate(estimate: Estimate) -> str:
    cur = estimate.currency
    t = estimate.totals
    m = estimate.markups

    lines = [
        f"# Estimate: {estimate.title}",
        f"Location: {estimate.location or 'not stated'}",
        f"Currency: {cur}",
        "",
        "## Scope",
        estimate.scope,
        "",
        "## Line items",
        "| id | description | category | unit | quantity | unit rate | total | notes |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for i in estimate.items:
        lines.append(
            f"| {i.id} | {i.description} | {i.category} | {i.unit} | {_num(i.quantity)} "
            f"| {_num(i.unit_rate)} | {_num(i.total)} | {i.notes or ''} |"
        )
    lines += [
        "",
        "## Markups and totals",
        f"- Direct cost: {_num(t.direct_cost)} {cur}",
        f"- Overhead {_num(m.overhead)}% of direct cost: {_num(t.overhead)} {cur}",
        f"- Profit {_num(m.profit)}% of direct cost + overhead: {_num(t.profit)} {cur}",
        f"- Contingency {_num(m.contingency)}% of direct cost: {_num(t.contingency)} {cur}",
        f"- Tax {_num(m.tax)}% of subtotal: {_num(t.tax)} {cur}",
        f"- Grand total: {_num(t.grand_total)} {cur}",
    ]
    return "\n".join(lines)


def _render_argument(arg: Argument) -> str:
    target = f"[{arg.line_item_id}]" if arg.line_item_id else "[missing scope]"
    head = f"- {target} {arg.stance.upper()}: {arg.claim}"
    extras = []
    if arg.proposed_quantity is not None:
        extras.append(f"proposed quantity {_num(arg.proposed_quantity)}")
    if arg.proposed_unit_rate is not None:
        extras.append(f"proposed rate {_num(arg.proposed_unit_rate)}")
    if arg.rebuts is not None:
        extras.append(f"answering the {ROLE_TITLES[arg.rebuts].lower()}")
    if extras:
        head += f" ({'; '.join(extras)})"
    return f"{head}\n  {arg.reasoning}"


def render_transcript(turns: Sequence[Turn]) -> str:
    if not turns:
        return "The debate has not started yet; nobody has spoken."

    blocks: list[str] = []
    current_round = 0
    for turn in turns:
        if turn.round != current_round:
            current_round = turn.round
            blocks.append(f"## Round {current_round}")
        args = "\n".join(_render_argument(a) for a in turn.arguments) or "- (no arguments)"
        blocks.append(f"### {ROLE_TITLES[turn.role]}\n{turn.summary}\n\n{args}")
    return "\n\n".join(blocks)
