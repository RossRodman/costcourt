from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from app.debate.models import DebateReport
from app.reports import __main__ as cli
from app.reports.store import ReportStore


@pytest.fixture
def store(tmp_path: Path) -> ReportStore:
    return ReportStore(tmp_path / "data" / "reports")  # the default, relative to tmp cwd


def test_list_empty(capsys: pytest.CaptureFixture[str]) -> None:
    cli.main(["list"])
    assert "No saved reports in data/reports" in capsys.readouterr().out


def test_list(
    store: ReportStore, demo_report: DebateReport, capsys: pytest.CaptureFixture[str]
) -> None:
    store.save(demo_report)

    cli.main(["list"])

    out = capsys.readouterr().out
    assert f"{demo_report.id}" in out and "(demo)" in out
    assert "190,799.27 → 218,696.07 USD (+14.62%), 6 rulings, confidence 82%" in out


def test_export_by_id_to_stdout(
    store: ReportStore, report: DebateReport, capsys: pytest.CaptureFixture[str]
) -> None:
    store.save(report)

    cli.main(["export", str(report.id)])

    assert capsys.readouterr().out.startswith("# CostCourt report: Garage")


def test_export_format_follows_the_file_extension(
    store: ReportStore, report: DebateReport, tmp_path: Path
) -> None:
    store.save(report)
    out = tmp_path / "report.html"

    cli.main(["export", str(report.id), "-o", str(out)])

    assert out.read_text(encoding="utf-8").startswith("<!doctype html>")


def test_export_a_json_file(
    report: DebateReport, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "copy.json"
    source.write_text(report.model_dump_json(), encoding="utf-8")

    cli.main(["--dir", str(tmp_path / "elsewhere"), "export", str(source), "--format", "json"])

    assert DebateReport.model_validate_json(capsys.readouterr().out) == report


@pytest.mark.parametrize(
    ("argv", "error"),
    [
        (["export", str(uuid4())], "no saved report with id"),
        (["export", "missing.json"], "neither a saved report id nor a file"),
        (["export", "x", "-o", "report.pdf"], "unknown report extension '.pdf'"),
    ],
)
def test_errors(argv: list[str], error: str) -> None:
    with pytest.raises(SystemExit, match=error):
        cli.main(argv)


def test_invalid_json_file(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="validation error"):
        cli.main(["export", str(tmp_path / "bad.json")])
