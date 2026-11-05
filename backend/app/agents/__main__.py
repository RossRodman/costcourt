"""Try a single agent against a sample estimate (real Claude call).

.venv/bin/python -m app.agents warehouse-slab --role engineer
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
from app.debate.models import DEBATERS, Role
from app.estimates.catalog import EstimateNotFoundError, get_sample_catalog


async def _run(sample_id: str, role: Role) -> None:
    settings = get_settings()
    estimate = get_sample_catalog().get(sample_id)
    panel = build_panel(settings)
    debater = next(d for d in panel.debaters if d.role is role)

    print(f"{ROLE_TITLES[role]} is reviewing '{estimate.title}' with {debater.model}…\n")
    completion = await debater.take_turn(estimate, [], round_no=1, total_rounds=1)
    turn = completion.output

    print(turn.summary, "\n")
    for arg in turn.arguments:
        target = arg.line_item_id or "missing scope"
        figures = ", ".join(
            f"{name} {value}"
            for name, value in (
                ("qty", arg.proposed_quantity),
                ("rate", arg.proposed_unit_rate),
            )
            if value is not None
        )
        print(
            f"[{target}] {arg.stance.upper()}: {arg.claim}" + (f"  ({figures})" if figures else "")
        )
        print(f"    {arg.reasoning}\n")
    print(
        f"-- {completion.model}, {completion.input_tokens} in / {completion.output_tokens} out "
        f"tokens, attempt {completion.attempts}"
    )


def main(argv: list[str] | None = None) -> None:
    samples = [s.id for s in get_sample_catalog().list()]
    parser = argparse.ArgumentParser(prog="python -m app.agents", description=__doc__)
    parser.add_argument("sample", choices=samples)
    parser.add_argument("--role", choices=[r.value for r in DEBATERS], default=Role.ENGINEER.value)
    args = parser.parse_args(argv)

    configure_logging(get_settings().log_level)
    try:
        asyncio.run(_run(args.sample, Role(args.role)))
    except (LLMError, EstimateNotFoundError) as exc:
        sys.exit(f"error: {exc}")


if __name__ == "__main__":
    main()
