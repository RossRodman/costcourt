"""Reports API: saved reports and their Markdown / HTML / JSON exports.

Handlers are plain `def`: the store does blocking file I/O, so FastAPI runs
them in its thread pool.
"""

from __future__ import annotations

from typing import Annotated, Any
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.debate.models import DebateReport
from app.reports.export import ReportFormat, export_report
from app.reports.store import ReportNotFoundError, ReportStore, ReportSummary

router = APIRouter(prefix="/reports", tags=["reports"])

NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"description": "Unknown report id"}}


def get_reports(request: Request) -> ReportStore:
    store: ReportStore = request.app.state.reports
    return store


ReportsDep = Annotated[ReportStore, Depends(get_reports)]


def _load(store: ReportStore, report_id: UUID) -> DebateReport:
    try:
        return store.get(report_id)
    except ReportNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.get("")
def list_reports(store: ReportsDep) -> list[ReportSummary]:
    """Every saved report, newest first."""
    return store.list()


@router.get("/{report_id}", responses=NOT_FOUND)
def get_report(report_id: UUID, store: ReportsDep) -> DebateReport:
    """The full report. Its id is the id of the debate that produced it."""
    return _load(store, report_id)


@router.get(
    "/{report_id}/export",
    responses={
        **NOT_FOUND,
        200: {
            "description": "The report as a file.",
            "content": {f.media_type.split(";")[0]: {} for f in ReportFormat},
        },
    },
)
def export(
    report_id: UUID,
    store: ReportsDep,
    format: Annotated[ReportFormat, Query(description="Output format.")] = ReportFormat.HTML,
    download: Annotated[
        bool, Query(description="Send as an attachment instead of opening in the browser.")
    ] = False,
) -> Response:
    exported = export_report(_load(store, report_id), format)
    disposition = "attachment" if download else "inline"
    return Response(
        exported.content,
        media_type=exported.media_type,
        headers={
            "Content-Disposition": f"{disposition}; filename*=utf-8''{quote(exported.filename)}"
        },
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND)
def delete_report(report_id: UUID, store: ReportsDep) -> None:
    try:
        store.delete(report_id)
    except ReportNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
