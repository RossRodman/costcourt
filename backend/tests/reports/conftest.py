from __future__ import annotations

import asyncio

import pytest

from app.debate.events import DebateCompleted
from app.debate.models import DebateReport
from app.debate.runner import run_debate
from app.demo import demo_panel
from app.estimates.catalog import get_sample_catalog
from tests.factories import debate_report


async def _run_demo() -> DebateReport:
    panel, rounds = demo_panel("warehouse-slab", delay_s=0)
    estimate = get_sample_catalog().get("warehouse-slab")
    async for event in run_debate(panel, estimate, rounds=rounds):
        if isinstance(event, DebateCompleted):
            return event.report
    raise AssertionError("the demo debate did not complete")


@pytest.fixture(scope="session")
def demo_report() -> DebateReport:
    """The recorded warehouse-slab debate, run through the real pipeline."""
    return asyncio.run(_run_demo())


@pytest.fixture
def report() -> DebateReport:
    return debate_report()
