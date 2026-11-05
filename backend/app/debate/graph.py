"""The debate as a LangGraph state machine.

    START → open_round → estimator → engineer → advocate ─┬─▶ open_round  (more rounds)
                                                          └─▶ judge → END

Agents are injected through the run context, not captured in closures, so
one compiled graph serves every debate. Nodes report progress with the
LangGraph stream writer; `run_debate` turns that into `DebateEvent`s.
"""

from __future__ import annotations

import operator
from dataclasses import dataclass
from functools import cache
from itertools import pairwise
from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.runtime import Runtime

from app.agents import Panel
from app.agents.judge import disputed_item_ids
from app.agents.llm import Completion
from app.debate.events import (
    JudgeStarted,
    RoundStarted,
    TurnCompleted,
    TurnStarted,
    VerdictReached,
)
from app.debate.models import DEBATERS, LLMUsage, Role, Turn, Verdict
from app.debate.verdict import apply_verdict
from app.estimates.models import Estimate

OPEN_ROUND: Literal["open_round"] = "open_round"
JUDGE: Literal["judge"] = "judge"


class DebateInput(TypedDict):
    estimate: Estimate
    rounds: int


class DebateState(DebateInput, total=False):
    round: int
    turns: Annotated[list[Turn], operator.add]
    usage: Annotated[list[LLMUsage], operator.add]
    verdict: Verdict
    revised_estimate: Estimate


@dataclass(frozen=True, slots=True)
class DebateContext:
    panel: Panel


def _usage(completion: Completion[Any], role: Role, round_no: int | None) -> LLMUsage:
    return LLMUsage(
        role=role,
        round=round_no,
        model=completion.model,
        input_tokens=completion.input_tokens,
        output_tokens=completion.output_tokens,
        cache_read_tokens=completion.cache_read_tokens,
    )


# --------------------------------------------------------------------- nodes


def open_round(state: DebateState, runtime: Runtime[DebateContext]) -> dict[str, Any]:
    round_no = state.get("round", 0) + 1
    runtime.stream_writer(RoundStarted(round=round_no, total_rounds=state["rounds"]))
    return {"round": round_no}


def _debater_node(role: Role) -> Any:
    async def speak(state: DebateState, runtime: Runtime[DebateContext]) -> dict[str, Any]:
        round_no = state["round"]
        runtime.stream_writer(TurnStarted(round=round_no, role=role))
        completion = await runtime.context.panel.debater(role).take_turn(
            state["estimate"],
            state.get("turns", []),
            round_no=round_no,
            total_rounds=state["rounds"],
        )
        usage = _usage(completion, role, round_no)
        runtime.stream_writer(TurnCompleted(turn=completion.output, usage=usage))
        return {"turns": [completion.output], "usage": [usage]}

    speak.__name__ = f"speak_{role}"
    return speak


async def judge(state: DebateState, runtime: Runtime[DebateContext]) -> dict[str, Any]:
    turns = state.get("turns", [])
    runtime.stream_writer(JudgeStarted(disputed_item_ids=tuple(disputed_item_ids(turns))))
    completion = await runtime.context.panel.judge.rule(state["estimate"], turns)
    verdict = completion.output
    usage = _usage(completion, Role.JUDGE, None)
    runtime.stream_writer(VerdictReached(verdict=verdict, usage=usage))
    return {
        "verdict": verdict,
        "revised_estimate": apply_verdict(state["estimate"], verdict),
        "usage": [usage],
    }


def after_round(state: DebateState) -> Literal["open_round", "judge"]:
    return OPEN_ROUND if state["round"] < state["rounds"] else JUDGE


# --------------------------------------------------------------------- graph


@cache
def debate_graph() -> CompiledStateGraph[DebateState, DebateContext, DebateInput, DebateState]:
    """Build and compile the graph once; it is stateless and safe to share."""
    builder = StateGraph(DebateState, context_schema=DebateContext, input_schema=DebateInput)

    builder.add_node(OPEN_ROUND, open_round)
    for role in DEBATERS:
        builder.add_node(role.value, _debater_node(role))
    builder.add_node(JUDGE, judge)

    builder.add_edge(START, OPEN_ROUND)
    builder.add_edge(OPEN_ROUND, DEBATERS[0].value)
    for speaker, nxt in pairwise(DEBATERS):
        builder.add_edge(speaker.value, nxt.value)
    builder.add_conditional_edges(DEBATERS[-1].value, after_round, [OPEN_ROUND, JUDGE])
    builder.add_edge(JUDGE, END)

    return builder.compile(name="costcourt-debate")
