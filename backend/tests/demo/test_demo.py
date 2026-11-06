from __future__ import annotations

import pytest

from app.agents.debater import TurnDraft
from app.agents.llm import LLMRequest
from app.debate.events import DebateCompleted
from app.debate.models import DEBATERS
from app.debate.runner import run_debate
from app.demo import DEMO_MODEL, DemoNotAvailableError, ReplayLLM, demo_panel, demo_scripts
from app.estimates.catalog import get_sample_catalog
from tests.fakes import turn_draft

SCRIPTS = sorted(demo_scripts())


def test_every_script_targets_a_sample_and_covers_every_speaker() -> None:
    assert SCRIPTS
    catalog = get_sample_catalog()
    for estimate_id, script in demo_scripts().items():
        catalog.get(estimate_id)
        for round_ in script.rounds:
            assert set(round_) == set(DEBATERS)


@pytest.mark.parametrize("estimate_id", SCRIPTS)
async def test_script_passes_every_domain_check(estimate_id: str) -> None:
    """Replayed answers go through the same checks as real model output."""
    panel, rounds = demo_panel(estimate_id, delay_s=0)
    estimate = get_sample_catalog().get(estimate_id)
    events = [e async for e in run_debate(panel, estimate, rounds=rounds)]

    done = events[-1]
    assert isinstance(done, DebateCompleted), events[-1]
    assert done.report.rounds == rounds
    assert set(done.report.models.values()) == {DEMO_MODEL}


async def test_replay_runs_out() -> None:
    llm = ReplayLLM([turn_draft()], delay_s=0)
    request = LLMRequest(model="m", effort="low", instructions="", context="", prompt="")
    first = await llm.generate(request, TurnDraft)
    assert first.model == DEMO_MODEL
    with pytest.raises(RuntimeError, match="no more outputs"):
        await llm.generate(request, TurnDraft)


def test_no_demo_for_unrecorded_sample() -> None:
    with pytest.raises(DemoNotAvailableError, match="office-fit-out"):
        demo_panel("office-fit-out", delay_s=0)
