from __future__ import annotations

from decimal import Decimal

from app.debate.models import DebateReport, Decision, Role
from app.reports.view import LineStatus, build_view


def test_every_line_with_what_happened_to_it(report: DebateReport) -> None:
    view = build_view(report)

    assert [(line.id, line.status) for line in view.lines] == [
        ("01.010", LineStatus.ADJUSTED),
        ("02.010", LineStatus.REMOVED),
        ("03.010", LineStatus.UNCHANGED),
    ]
    adjusted, removed, untouched = view.lines
    assert adjusted.delta == Decimal("320.00")  # 10 x 100 -> 12 x 110
    assert removed.revised is None and removed.delta == Decimal("-1000.00")
    assert untouched.delta == 0
    assert [line.id for line in view.ruled] == ["01.010", "02.010"]
    assert [line.id for line in view.changed] == ["01.010", "02.010"]


def test_arguments_are_grouped_by_line(report: DebateReport) -> None:
    view = build_view(report)

    concrete = view.lines[0]
    assert [(e.round, e.role) for e in concrete.arguments] == [
        (1, Role.ESTIMATOR),
        (1, Role.ENGINEER),
    ]
    assert view.lines[1].arguments == ()
    assert [e.argument.claim for e in view.missing_scope] == ["Winter blankets are not priced."]


def test_rounds_and_usage_totals(demo_report: DebateReport) -> None:
    view = build_view(demo_report)

    assert [n for n, _ in view.rounds] == [1, 2]
    assert all(len(turns) == 3 for _, turns in view.rounds)
    assert view.usage.calls == 7


def test_accepted_line_is_kept_as_priced(report: DebateReport) -> None:
    accepted = report.verdict.rulings[0].model_copy(
        update={
            "decision": Decision.ACCEPTED,
            "approved_quantity": None,
            "approved_unit_rate": None,
        }
    )
    verdict = report.verdict.model_copy(update={"rulings": (accepted,)})
    view = build_view(
        report.model_copy(update={"verdict": verdict, "revised_estimate": report.estimate})
    )

    assert view.lines[0].status is LineStatus.ACCEPTED
    assert view.ruled == (view.lines[0],)
    assert view.changed == ()
