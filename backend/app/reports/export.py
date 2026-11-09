"""One entry point for every export format."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.debate.models import DebateReport
from app.reports.html import render_html
from app.reports.markdown import render_markdown


class ReportFormat(StrEnum):
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"

    @property
    def extension(self) -> str:
        return {"markdown": ".md", "html": ".html", "json": ".json"}[self.value]

    @property
    def media_type(self) -> str:
        return {
            "markdown": "text/markdown; charset=utf-8",
            "html": "text/html; charset=utf-8",
            "json": "application/json",
        }[self.value]

    @classmethod
    def from_extension(cls, extension: str) -> ReportFormat:
        """'.md' -> MARKDOWN. Raises ValueError for unknown extensions."""
        aliases = {".markdown": cls.MARKDOWN, ".htm": cls.HTML}
        by_extension = {f.extension: f for f in cls} | aliases
        try:
            return by_extension[extension.lower()]
        except KeyError:
            known = ", ".join(sorted(by_extension))
            raise ValueError(f"unknown report extension '{extension}' (use {known})") from None


@dataclass(frozen=True)
class ExportedReport:
    content: str
    format: ReportFormat
    filename: str

    @property
    def media_type(self) -> str:
        return self.format.media_type


def report_filename(report: DebateReport, fmt: ReportFormat) -> str:
    """'costcourt-warehouse-slab-1a2b3c4d.md': readable, and unique per debate."""
    return f"costcourt-{report.estimate.id}-{report.id.hex[:8]}{fmt.extension}"


def export_report(report: DebateReport, fmt: ReportFormat) -> ExportedReport:
    match fmt:
        case ReportFormat.MARKDOWN:
            content = render_markdown(report)
        case ReportFormat.HTML:
            content = render_html(report)
        case ReportFormat.JSON:
            content = report.model_dump_json(indent=2) + "\n"
    return ExportedReport(content=content, format=fmt, filename=report_filename(report, fmt))
