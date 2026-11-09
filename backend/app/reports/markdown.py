"""Render a debate report as Markdown (reads well raw, on GitHub and in editors)."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from app.debate.models import DebateReport
from app.reports.formatting import (
    category_label,
    decision_label,
    money,
    percent,
    proposal,
    quantity,
    role_title,
    signed_money,
    signed_percent,
    stance_label,
    unit_label,
)
from app.reports.view import ArgumentEntry, LineReview, ReportView, build_view


def _text(value: str) -> str:
    """Neutralise raw HTML: estimates can be uploaded by anyone."""
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _cell(value: str) -> str:
    return _text(value).replace("|", "\\|").replace("\r", "").replace("\n", " ")


def _table(header: Sequence[str], rows: Iterable[Sequence[str]], align: str) -> list[str]:
    """`align` has one char per column: l(eft) or r(ight)."""
    rule = ["---:" if a == "r" else "---" for a in align]
    return [
        f"| {' | '.join(header)} |",
        f"| {' | '.join(rule)} |",
        *(f"| {' | '.join(_cell(c) for c in row)} |" for row in rows),
    ]


def _figures(line: LineReview) -> list[str]:
    """'Quantity: 480 → 504 m³'-style changes of an adjusted or removed line."""
    old, new = line.original, line.revised
    unit = unit_label(old.unit)
    if new is None:
        return [f"- Removed: {quantity(old.quantity)} {unit} at {money(old.unit_rate)}"]
    changes = []
    if new.quantity != old.quantity:
        changes.append(f"- Quantity: {quantity(old.quantity)} → {quantity(new.quantity)} {unit}")
    if new.unit_rate != old.unit_rate:
        changes.append(f"- Unit rate: {money(old.unit_rate)} → {money(new.unit_rate)}")
    return changes


def _argument(entry: ArgumentEntry, *, in_transcript: bool) -> list[str]:
    """In the transcript: the line id and the reasoning. Elsewhere: the round."""
    arg = entry.argument
    who = role_title(entry.role) + ("" if in_transcript else f", round {entry.round}")
    target = f"`{arg.line_item_id}` " if in_transcript and arg.line_item_id else ""
    lines = [f"- **{who}**: {target}*{stance_label(arg.stance)}*: {_text(arg.claim)}"]
    if in_transcript:
        lines.append(f"  - {_text(arg.reasoning)}")
    if proposes := proposal(arg):
        lines.append(f"  - {proposes}")
    if arg.rebuts:
        lines.append(f"  - Answers the {role_title(arg.rebuts).lower()}")
    return lines


def _outcome(view: ReportView) -> list[str]:
    report = view.report
    impact = report.impact
    cur = report.estimate.currency
    return [
        "## Outcome",
        "",
        *_table(
            ["", f"Amount ({cur})"],
            [
                ["Original total", money(impact.original_total)],
                ["Revised total", money(impact.revised_total)],
                [
                    "Change",
                    f"{signed_money(impact.delta)} ({signed_percent(impact.delta_pct)})",
                ],
            ],
            "lr",
        ),
        "",
        f"**Judge's confidence:** {percent(report.verdict.confidence)}  ",
        f"**Lines ruled on:** {len(view.ruled)} of {len(view.lines)}, {len(view.changed)} changed",
        "",
        "### Judge's summary",
        "",
        _text(report.verdict.summary),
        *(
            [
                "",
                "### Recommendations",
                "",
                *(f"- {_text(r)}" for r in report.verdict.recommendations),
            ]
            if report.verdict.recommendations
            else []
        ),
    ]


def _rulings(view: ReportView) -> list[str]:
    out = ["## Rulings"]
    if not view.ruled:
        return [*out, "", "The judge made no changes to the estimate."]
    for line in view.ruled:
        assert line.ruling is not None
        ruling = line.ruling
        out += [
            "",
            f"### `{line.id}` {_text(line.original.description)}: "
            f"{decision_label(ruling.decision)}",
            "",
            *_figures(line),
            f"- Line total: {money(line.original.total)} → {money(line.revised_total)} "
            f"({signed_money(line.delta)})",
        ]
        if ruling.sided_with:
            out.append(f"- Sided with: {', '.join(role_title(r) for r in ruling.sided_with)}")
        out += ["", f"> {_text(ruling.reasoning)}"]
        if line.arguments:
            out += ["", "Arguments:", ""]
            for entry in line.arguments:
                out += _argument(entry, in_transcript=False)
    return out


def _transcript(view: ReportView) -> list[str]:
    out = ["## Debate transcript"]
    for round_no, turns in view.rounds:
        out += ["", f"### Round {round_no}"]
        for turn in turns:
            out += ["", f"#### {role_title(turn.role)}", "", _text(turn.summary)]
            if turn.arguments:
                out.append("")
                for arg in turn.arguments:
                    entry = ArgumentEntry(round=turn.round, role=turn.role, argument=arg)
                    out += _argument(entry, in_transcript=True)
    return out


def _revised_estimate(view: ReportView) -> list[str]:
    report = view.report
    old, new = report.estimate.totals, report.revised_estimate.totals
    m = report.estimate.markups
    rows = [
        [
            line.id,
            line.original.description,
            category_label(line.original.category),
            unit_label(line.original.unit),
            quantity(line.original.quantity),
            quantity(line.revised.quantity) if line.revised else "removed",
            money(line.original.unit_rate),
            money(line.revised.unit_rate) if line.revised else "removed",
            money(line.revised_total),
            signed_money(line.delta) if line.delta else "—",
        ]
        for line in view.lines
    ]
    totals = [
        ["Direct cost", "", money(old.direct_cost), money(new.direct_cost)],
        ["Overhead", f"{quantity(m.overhead)}%", money(old.overhead), money(new.overhead)],
        ["Profit", f"{quantity(m.profit)}%", money(old.profit), money(new.profit)],
        [
            "Contingency",
            f"{quantity(m.contingency)}%",
            money(old.contingency),
            money(new.contingency),
        ],
        ["Tax", f"{quantity(m.tax)}%", money(old.tax), money(new.tax)],
        ["**Grand total**", "", money(old.grand_total), f"**{money(new.grand_total)}**"],
    ]
    return [
        "## Revised estimate",
        "",
        *_table(
            [
                "Line",
                "Description",
                "Category",
                "Unit",
                "Qty",
                "Revised qty",
                "Rate",
                "Revised rate",
                "Total",
                "Change",
            ],
            rows,
            "llllrrrrrr",
        ),
        "",
        *_table(["", "Markup", "Original", "Revised"], totals, "lrrr"),
    ]


def _usage(view: ReportView) -> list[str]:
    report = view.report
    rows = [
        [
            role_title(u.role),
            str(u.round) if u.round is not None else "verdict",
            u.model,
            f"{u.input_tokens:,}",
            f"{u.output_tokens:,}",
            f"{u.cache_read_tokens:,}",
        ]
        for u in report.usage
    ]
    t = view.usage
    rows.append(
        [
            "**Total**",
            "",
            f"{t.calls} calls",
            f"{t.input_tokens:,}",
            f"{t.output_tokens:,}",
            f"{t.cache_read_tokens:,}",
        ]
    )
    return [
        "## Models and token usage",
        "",
        *_table(["Agent", "Round", "Model", "Input", "Output", "Cache read"], rows, "lllrrr"),
    ]


def render_markdown(report: DebateReport) -> str:
    view = build_view(report)
    estimate = report.estimate
    facts = [
        estimate.location,
        report.created_at.strftime("%Y-%m-%d %H:%M UTC"),
        f"{report.rounds} {'round' if report.rounds == 1 else 'rounds'}",
        estimate.currency,
    ]
    sections = [
        [
            f"# CostCourt report: {_text(estimate.title)}",
            "",
            " · ".join(_text(f) for f in facts if f),
            "",
            f"Report `{report.id}`",
        ],
        _outcome(view),
        _rulings(view),
    ]
    if view.missing_scope:
        sections.append(
            [
                "## Missing scope raised",
                "",
                "Work the debaters said the estimate leaves out. The judge rules on priced "
                "lines only, so these are follow-ups, not changes.",
                "",
                *(line for e in view.missing_scope for line in _argument(e, in_transcript=False)),
            ]
        )
    sections += [
        _transcript(view),
        _revised_estimate(view),
        _usage(view),
        ["---", "", "Generated by CostCourt."],
    ]
    return "\n\n".join("\n".join(s) for s in sections) + "\n"
