"""Events a running debate emits, in order. They drive the live UI stream.

A debate always emits `debate_started` first and exactly one terminal event
last: `debate_completed` (with the full report) or `debate_failed`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, TypeAdapter

from app.core.models import DomainModel
from app.debate.models import DebateReport, LLMUsage, Role, Turn, Verdict


class _Event(DomainModel):
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DebateStarted(_Event):
    type: Literal["debate_started"] = "debate_started"
    debate_id: UUID
    estimate_id: str
    estimate_title: str
    rounds: int
    speakers: tuple[Role, ...]


class RoundStarted(_Event):
    type: Literal["round_started"] = "round_started"
    round: int
    total_rounds: int


class TurnStarted(_Event):
    """A debater has started thinking. Useful for a 'typing' indicator."""

    type: Literal["turn_started"] = "turn_started"
    round: int
    role: Role


class TurnCompleted(_Event):
    type: Literal["turn_completed"] = "turn_completed"
    turn: Turn
    usage: LLMUsage


class JudgeStarted(_Event):
    type: Literal["judge_started"] = "judge_started"
    disputed_item_ids: tuple[str, ...]


class VerdictReached(_Event):
    type: Literal["verdict_reached"] = "verdict_reached"
    verdict: Verdict
    usage: LLMUsage


class DebateCompleted(_Event):
    type: Literal["debate_completed"] = "debate_completed"
    report: DebateReport


class DebateFailed(_Event):
    type: Literal["debate_failed"] = "debate_failed"
    error: str
    """Safe to show to the user."""


DebateEvent = Annotated[
    DebateStarted
    | RoundStarted
    | TurnStarted
    | TurnCompleted
    | JudgeStarted
    | VerdictReached
    | DebateCompleted
    | DebateFailed,
    Field(discriminator="type"),
]

debate_event_adapter: TypeAdapter[DebateEvent] = TypeAdapter(DebateEvent)
"""Parse/serialise any event, e.g. `debate_event_adapter.validate_json(data)`."""
