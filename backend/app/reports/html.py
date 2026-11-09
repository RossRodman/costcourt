"""Render a debate report as one self-contained, printable HTML page."""

from __future__ import annotations

from functools import cache

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

from app import __version__
from app.debate.models import DebateReport
from app.reports import formatting
from app.reports.view import build_view


@cache
def _environment() -> Environment:
    env = Environment(
        loader=PackageLoader("app.reports", "templates"),
        # Every estimate field is user input: escape everything.
        autoescape=select_autoescape(default=True, default_for_string=True),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters.update(
        money=formatting.money,
        signed_money=formatting.signed_money,
        quantity=formatting.quantity,
        percent=formatting.percent,
        signed_percent=formatting.signed_percent,
        unit=formatting.unit_label,
        category=formatting.category_label,
        role=formatting.role_title,
        stance=formatting.stance_label,
        decision=formatting.decision_label,
        proposal=formatting.proposal,
    )
    return env


def render_html(report: DebateReport) -> str:
    template = _environment().get_template("report.html")
    return template.render(view=build_view(report), report=report, version=__version__)
