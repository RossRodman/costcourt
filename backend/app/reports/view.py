"""What a report shows, computed once and shared by every export format.

The `DebateReport` is the raw audit trail. This view lines it up the way a
reader asks for it: per line item, what changed, which ruling changed it and
which arguments led there.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from itertools import groupby

from app.debate.models import Argument, DebateReport, Decision, Role, Ruling, Turn
from app.estimates.models import LineItem


class LineStatus(StrEnum):
    UNCHANGED = "unchanged"
    """Nobody's ruling touched it."""
    ACCEPTED = "accepted"
    """Disputed, but kept as priced."""
    ADJUSTED = "adjusted"
    REMOVED = "removed"


@dataclass(frozen=True)
class ArgumentEntry:
    """One argument, with who made it and when."""

    round: int
    role: Role
    argument: Argument


@dataclass(frozen=True)
class LineReview:
    """One line of the original estimate and what the debate did to it."""

    original: LineItem
    revised: LineItem | None
    ruling: Ruling | None
    arguments: tuple[ArgumentEntry, ...]

    @property
    def id(self) -> str:
        return self.original.id

    @property
    def status(self) -> LineStatus:
        if self.ruling is None:
            return LineStatus.UNCHANGED
        return {
            Decision.ACCEPTED: LineStatus.ACCEPTED,
            Decision.ADJUSTED: LineStatus.ADJUSTED,
            Decision.REJECTED: LineStatus.REMOVED,
        }[self.ruling.decision]

    @property
    def revised_total(self) -> Decimal:
        return self.revised.total if self.revised else Decimal(0)

    @property
    def delta(self) -> Decimal:
        return self.revised_total - self.original.total


@dataclass(frozen=True)
class UsageTotals:
    calls: int
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int


@dataclass(frozen=True)
class ReportView:
    report: DebateReport
    lines: tuple[LineReview, ...]
    """Every line of the original estimate, in order."""
    missing_scope: tuple[ArgumentEntry, ...]
    """Arguments about work the estimate leaves out (not tied to a line)."""
    rounds: tuple[tuple[int, tuple[Turn, ...]], ...]
    usage: UsageTotals

    @property
    def ruled(self) -> tuple[LineReview, ...]:
        """Lines the judge ruled on, in estimate order."""
        return tuple(line for line in self.lines if line.ruling is not None)

    @property
    def changed(self) -> tuple[LineReview, ...]:
        return tuple(line for line in self.lines if line.delta)


def build_view(report: DebateReport) -> ReportView:
    entries = [
        ArgumentEntry(round=turn.round, role=turn.role, argument=argument)
        for turn in report.turns
        for argument in turn.arguments
    ]
    rulings = {r.line_item_id: r for r in report.verdict.rulings}
    revised = {item.id: item for item in report.revised_estimate.items}

    lines = tuple(
        LineReview(
            original=item,
            revised=revised.get(item.id),
            ruling=rulings.get(item.id),
            arguments=tuple(e for e in entries if e.argument.line_item_id == item.id),
        )
        for item in report.estimate.items
    )
    turns = sorted(report.turns, key=lambda t: t.round)
    return ReportView(
        report=report,
        lines=lines,
        missing_scope=tuple(e for e in entries if e.argument.line_item_id is None),
        rounds=tuple((n, tuple(group)) for n, group in groupby(turns, key=lambda t: t.round)),
        usage=UsageTotals(
            calls=len(report.usage),
            input_tokens=sum(u.input_tokens for u in report.usage),
            output_tokens=sum(u.output_tokens for u in report.usage),
            cache_read_tokens=sum(u.cache_read_tokens for u in report.usage),
        ),
    )
