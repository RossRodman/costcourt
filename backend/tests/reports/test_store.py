from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from app.debate.models import DebateReport
from app.reports.store import ReportNotFoundError, ReportStore, ReportSummary


@pytest.fixture
def store(tmp_path: Path) -> ReportStore:
    return ReportStore(tmp_path / "reports")


def test_save_and_get(store: ReportStore, report: DebateReport) -> None:
    path = store.save(report)

    assert path == store.root / f"{report.id}.json"
    assert store.get(report.id) == report
    assert [p.name for p in store.root.iterdir()] == [path.name]  # no temp files left


def test_unknown_report(store: ReportStore) -> None:
    missing = uuid4()
    with pytest.raises(ReportNotFoundError, match=f"no saved report with id '{missing}'"):
        store.get(missing)
    with pytest.raises(ReportNotFoundError):
        store.delete(missing)


def test_list_newest_first(store: ReportStore, report: DebateReport) -> None:
    now = datetime.now(UTC)
    old = report.model_copy(update={"id": uuid4(), "created_at": now - timedelta(days=1)})
    new = report.model_copy(update={"id": uuid4(), "created_at": now})
    store.save(old)
    store.save(new)

    assert [s.id for s in store.list()] == [new.id, old.id]


def test_summary(report: DebateReport, demo_report: DebateReport) -> None:
    summary = ReportSummary.of(report)

    assert summary.estimate_title == report.estimate.title
    assert summary.rulings == 2
    assert summary.delta_pct == report.impact.delta_pct == -33.17
    assert summary.demo is False
    assert ReportSummary.of(demo_report).demo is True


def test_list_without_a_directory(store: ReportStore) -> None:
    assert store.list() == []


def test_list_skips_unreadable_files(
    store: ReportStore, report: DebateReport, caplog: pytest.LogCaptureFixture
) -> None:
    store.save(report)
    (store.root / "broken.json").write_text("{not json", encoding="utf-8")

    assert [s.id for s in store.list()] == [report.id]
    assert "skipping unreadable report broken.json" in caplog.text


def test_list_notices_changed_and_deleted_files(store: ReportStore, report: DebateReport) -> None:
    path = store.save(report)
    assert store.list()[0].estimate_title == report.estimate.title

    estimate = report.estimate.model_copy(update={"title": "Renamed estimate"})
    store.save(report.model_copy(update={"estimate": estimate}))
    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))
    assert store.list()[0].estimate_title == "Renamed estimate"

    store.delete(report.id)
    assert store.list() == []
    with pytest.raises(ReportNotFoundError):
        store.get(report.id)
