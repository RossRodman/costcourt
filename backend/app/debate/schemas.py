"""Request and response bodies of the debates API."""

from __future__ import annotations

from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.debate.models import DebateReport
from app.debate.sessions import DebateSession, DebateStatus
from app.estimates.models import Estimate


class DebateRequest(BaseModel):
    """Start a debate on a built-in sample or on your own estimate (exactly one)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"sample_id": "warehouse-slab", "rounds": 2},
                {"sample_id": "warehouse-slab", "demo": True},
            ]
        },
    )

    sample_id: str | None = None
    estimate: Estimate | None = None
    rounds: int | None = Field(
        default=None, ge=1, le=5, description="Debate rounds; server default if omitted."
    )
    demo: bool = Field(
        default=False,
        description="Replay a recorded debate (no API key needed). Samples with a demo only; "
        "`rounds` is ignored.",
    )

    @model_validator(mode="after")
    def _exactly_one_source(self) -> Self:
        if (self.sample_id is None) == (self.estimate is None):
            raise ValueError("provide exactly one of 'sample_id' or 'estimate'")
        if self.demo and self.sample_id is None:
            raise ValueError("demo debates run on a sample: set 'sample_id'")
        return self


class DebateOut(BaseModel):
    """A debate's current state. `report` is set once it completes."""

    id: UUID
    status: DebateStatus
    created_at: datetime
    estimate: Estimate | None = Field(description="The estimate under review (omitted in lists).")
    estimate_id: str
    estimate_title: str
    rounds: int
    demo: bool
    events: int = Field(description="Events emitted so far.")
    error: str | None = None
    report: DebateReport | None = None

    @classmethod
    def of(cls, session: DebateSession, *, detail: bool = True) -> DebateOut:
        """`detail=False` leaves out the estimate and the report, for listings."""
        return cls(
            id=session.id,
            status=session.status,
            created_at=session.created_at,
            estimate=session.estimate if detail else None,
            estimate_id=session.estimate.id,
            estimate_title=session.estimate.title,
            rounds=session.rounds,
            demo=session.demo,
            events=len(session.events),
            error=session.error,
            report=session.report if detail else None,
        )
