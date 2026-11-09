"""Completed debate reports, saved as JSON files so they outlive the server.

Live debates are kept in memory only; their reports are written here the
moment a debate completes. One file per report, named by its id: easy to
back up, diff, or delete by hand.
"""

from __future__ import annotations

import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError

from app.core.models import DomainModel
from app.core.types import Money
from app.debate.models import CostImpact, DebateReport
from app.demo import DEMO_MODEL

log = logging.getLogger(__name__)


class ReportNotFoundError(KeyError):
    def __init__(self, report_id: UUID) -> None:
        super().__init__(report_id)
        self.report_id = report_id

    def __str__(self) -> str:
        return f"no saved report with id '{self.report_id}'"


class ReportSummary(DomainModel):
    """Listing entry: enough to pick a report without loading the transcript."""

    id: UUID
    created_at: datetime
    estimate_id: str
    estimate_title: str
    location: str | None
    currency: str
    rounds: int
    rulings: int
    confidence: float
    original_total: Money
    revised_total: Money
    delta_pct: float
    demo: bool

    @classmethod
    def of(cls, report: DebateReport) -> ReportSummary:
        impact: CostImpact = report.impact
        return cls(
            id=report.id,
            created_at=report.created_at,
            estimate_id=report.estimate.id,
            estimate_title=report.estimate.title,
            location=report.estimate.location,
            currency=report.estimate.currency,
            rounds=report.rounds,
            rulings=len(report.verdict.rulings),
            confidence=report.verdict.confidence,
            original_total=impact.original_total,
            revised_total=impact.revised_total,
            delta_pct=impact.delta_pct,
            demo=bool(report.models) and set(report.models.values()) == {DEMO_MODEL},
        )


class ReportStore:
    """Reads and writes `<root>/<report id>.json`. Blocking I/O: call from a thread."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self._summaries: dict[Path, tuple[int, ReportSummary]] = {}
        """Parsed summaries keyed by file, with the mtime they were read at."""

    def _path(self, report_id: UUID) -> Path:
        return self.root / f"{report_id}.json"

    def save(self, report: DebateReport) -> Path:
        """Write atomically: readers never see a half-written file."""
        self.root.mkdir(parents=True, exist_ok=True)
        path = self._path(report.id)
        fd, tmp = tempfile.mkstemp(dir=self.root, prefix=".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(report.model_dump_json(indent=2))
            Path(tmp).replace(path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
        return path

    def get(self, report_id: UUID) -> DebateReport:
        try:
            raw = self._path(report_id).read_text(encoding="utf-8")
        except FileNotFoundError:
            raise ReportNotFoundError(report_id) from None
        return DebateReport.model_validate_json(raw)

    def list(self) -> list[ReportSummary]:
        """Newest first. Unreadable files are skipped (and logged), not fatal."""
        if not self.root.is_dir():
            return []
        summaries = []
        seen = set()
        for path in self.root.glob("*.json"):
            seen.add(path)
            try:
                mtime = path.stat().st_mtime_ns
                cached = self._summaries.get(path)
                if cached is None or cached[0] != mtime:
                    report = DebateReport.model_validate_json(path.read_text(encoding="utf-8"))
                    cached = (mtime, ReportSummary.of(report))
                    self._summaries[path] = cached
            except (OSError, ValidationError) as exc:
                log.warning("skipping unreadable report %s: %s", path.name, exc)
                continue
            summaries.append(cached[1])
        for gone in self._summaries.keys() - seen:
            del self._summaries[gone]
        return sorted(summaries, key=lambda s: s.created_at, reverse=True)

    def delete(self, report_id: UUID) -> None:
        try:
            self._path(report_id).unlink()
        except FileNotFoundError:
            raise ReportNotFoundError(report_id) from None
