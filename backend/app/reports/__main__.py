"""List saved reports, or export one as Markdown, HTML or JSON.

.venv/bin/python -m app.reports list
.venv/bin/python -m app.reports export <report id> -o report.html
.venv/bin/python -m app.reports export path/to/report.json --format markdown
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError

from app.core.config import get_settings
from app.debate.models import DebateReport
from app.reports.export import ReportFormat, export_report
from app.reports.formatting import money, percent, signed_percent
from app.reports.store import ReportNotFoundError, ReportStore


def _list(store: ReportStore) -> None:
    summaries = store.list()
    if not summaries:
        print(f"No saved reports in {store.root}")
        return
    for s in summaries:
        demo = "  (demo)" if s.demo else ""
        print(
            f"{s.id}  {s.created_at:%Y-%m-%d %H:%M}  {s.estimate_title}{demo}\n"
            f"    {money(s.original_total)} → {money(s.revised_total)} {s.currency} "
            f"({signed_percent(s.delta_pct)}), {s.rulings} rulings, "
            f"confidence {percent(s.confidence)}"
        )


def _load(store: ReportStore, source: str) -> DebateReport:
    """A saved report's id, or a path to a report JSON file."""
    try:
        return store.get(UUID(source))
    except ValueError:
        pass
    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(f"'{source}' is neither a saved report id nor a file")
    return DebateReport.model_validate_json(path.read_text(encoding="utf-8"))


def _resolve_format(fmt: str | None, out: Path | None) -> ReportFormat:
    if fmt is not None:
        return ReportFormat(fmt)
    if out is not None:
        return ReportFormat.from_extension(out.suffix)
    return ReportFormat.MARKDOWN


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app.reports", description=__doc__)
    parser.add_argument(
        "--dir", type=Path, help="reports directory (default: COSTCOURT_REPORTS_DIR)"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="list saved reports, newest first")
    export = commands.add_parser("export", help="export one report")
    export.add_argument("source", help="report id, or path to a report JSON file")
    export.add_argument("-f", "--format", choices=[f.value for f in ReportFormat])
    export.add_argument(
        "-o", "--out", type=Path, help="output file; format from its extension (default: stdout)"
    )
    args = parser.parse_args(argv)

    store = ReportStore(args.dir or get_settings().reports_dir)
    if args.command == "list":
        _list(store)
        return

    try:
        fmt = _resolve_format(args.format, args.out)
        exported = export_report(_load(store, args.source), fmt)
    except (ReportNotFoundError, FileNotFoundError, ValueError, ValidationError) as exc:
        sys.exit(f"error: {exc}")
    if args.out is None:
        sys.stdout.write(exported.content)
    else:
        args.out.write_text(exported.content, encoding="utf-8")
        print(f"Wrote {exported.format.value} report to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
