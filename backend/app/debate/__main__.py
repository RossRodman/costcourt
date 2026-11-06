"""Run a full debate in the terminal (real Claude calls).

.venv/bin/python -m app.debate warehouse-slab --rounds 1
.venv/bin/python -m app.debate warehouse-slab --demo   # no API key needed
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.agents import build_panel
from app.agents.context import ROLE_TITLES
from app.agents.llm import LLMError
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.debate.events import (
    DebateCompleted,
    DebateEvent,
    DebateFailed,
    DebateStarted,
    JudgeStarted,
    RoundStarted,
    TurnCompleted,
    TurnStarted,
    VerdictReached,
)
from app.debate.models import Role
from app.debate.runner import run_debate
from app.demo import DemoNotAvailableError, demo_panel
from app.estimates.catalog import EstimateNotFoundError, get_sample_catalog


def _print_event(event: DebateEvent) -> None:
    match event:
        case DebateStarted():
            print(f"Debate on '{event.estimate_title}', {event.rounds} round(s)")
        case RoundStarted():
            print(f"\n=== Round {event.round} of {event.total_rounds} ===")
        case TurnStarted():
            print(f"\n{ROLE_TITLES[event.role]} is thinking…")
        case TurnCompleted():
            print(f"{ROLE_TITLES[event.turn.role]}: {event.turn.summary}")
            for arg in event.turn.arguments:
                target = arg.line_item_id or "missing scope"
                print(f"  [{target}] {arg.stance.upper()}: {arg.claim}")
        case JudgeStarted():
            print(f"\n=== {ROLE_TITLES[Role.JUDGE]} ===")
        case VerdictReached():
            print(event.verdict.summary)
            for r in event.verdict.rulings:
                print(f"  [{r.line_item_id}] {r.decision.upper()}: {r.reasoning}")
        case DebateCompleted():
            report = event.report
            cur = report.estimate.currency
            impact = report.impact
            tokens = sum(u.input_tokens + u.output_tokens for u in report.usage)
            print(
                f"\nTotal {impact.original_total:,} → {impact.revised_total:,} {cur} "
                f"({impact.delta_pct:+}%), confidence {report.verdict.confidence:.0%}, "
                f"{tokens:,} tokens"
            )
        case DebateFailed():
            print(f"\nDebate failed: {event.error}", file=sys.stderr)


async def _run(sample_id: str, rounds: int, *, demo: bool) -> bool:
    settings = get_settings()
    estimate = get_sample_catalog().get(sample_id)
    if demo:
        panel, rounds = demo_panel(sample_id, delay_s=settings.demo_delay_s)
    else:
        panel = build_panel(settings)
    ok = False
    async for event in run_debate(panel, estimate, rounds=rounds):
        _print_event(event)
        ok = isinstance(event, DebateCompleted)
    return ok


def main(argv: list[str] | None = None) -> None:
    settings = get_settings()
    samples = [s.id for s in get_sample_catalog().list()]
    parser = argparse.ArgumentParser(prog="python -m app.debate", description=__doc__)
    parser.add_argument("sample", choices=samples)
    parser.add_argument("--rounds", type=int, choices=range(1, 6), default=settings.debate_rounds)
    parser.add_argument(
        "--demo", action="store_true", help="replay the recorded debate (no API key needed)"
    )
    args = parser.parse_args(argv)

    configure_logging(settings.log_level)
    try:
        ok = asyncio.run(_run(args.sample, args.rounds, demo=args.demo))
    except (LLMError, EstimateNotFoundError, DemoNotAvailableError) as exc:
        sys.exit(f"error: {exc}")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
