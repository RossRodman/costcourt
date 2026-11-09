from __future__ import annotations

import pytest

from app.debate.models import DebateReport
from app.reports.export import ReportFormat, export_report, report_filename


@pytest.mark.parametrize(
    ("fmt", "media_type", "starts"),
    [
        (ReportFormat.MARKDOWN, "text/markdown; charset=utf-8", "# CostCourt report"),
        (ReportFormat.HTML, "text/html; charset=utf-8", "<!doctype html>"),
        (ReportFormat.JSON, "application/json", "{"),
    ],
)
def test_every_format(
    report: DebateReport, fmt: ReportFormat, media_type: str, starts: str
) -> None:
    exported = export_report(report, fmt)

    assert exported.format is fmt
    assert exported.media_type == media_type
    assert exported.content.startswith(starts)
    assert exported.filename == f"costcourt-test-estimate-{report.id.hex[:8]}{fmt.extension}"


def test_json_export_round_trips(report: DebateReport) -> None:
    content = export_report(report, ReportFormat.JSON).content

    assert DebateReport.model_validate_json(content) == report


@pytest.mark.parametrize(
    ("extension", "fmt"),
    [
        (".md", ReportFormat.MARKDOWN),
        (".markdown", ReportFormat.MARKDOWN),
        (".HTML", ReportFormat.HTML),
        (".htm", ReportFormat.HTML),
        (".json", ReportFormat.JSON),
    ],
)
def test_format_from_extension(extension: str, fmt: ReportFormat) -> None:
    assert ReportFormat.from_extension(extension) is fmt


def test_unknown_extension() -> None:
    with pytest.raises(ValueError, match=r"unknown report extension '\.pdf'"):
        ReportFormat.from_extension(".pdf")


def test_filename_uses_the_estimate_id(demo_report: DebateReport) -> None:
    name = report_filename(demo_report, ReportFormat.HTML)
    assert name.startswith("costcourt-warehouse-slab-") and name.endswith(".html")
