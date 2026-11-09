from __future__ import annotations

import pytest

from app.agents import build_panel
from app.agents.llm import LLMNotConfiguredError
from app.core.config import Settings
from app.debate.models import Role
from tests.fakes import ScriptedLLM


def test_panel_speaking_order_and_models() -> None:
    settings = Settings(debater_model="claude-sonnet-5-5", judge_effort="max")
    panel = build_panel(settings, ScriptedLLM())
    assert [d.role for d in panel.debaters] == [Role.ESTIMATOR, Role.ENGINEER, Role.ADVOCATE]
    assert {d.model for d in panel.debaters} == {"claude-sonnet-5-5"}
    assert panel.judge.model == "claude-opus-5-5"


def test_real_panel_needs_an_api_key() -> None:
    with pytest.raises(LLMNotConfiguredError, match="ANTHROPIC_API_KEY"):
        build_panel(Settings())


def test_real_panel_with_key() -> None:
    panel = build_panel(Settings(anthropic_api_key="sk-ant-test"))  # type: ignore[arg-type]
    assert len(panel.debaters) == 3


def test_debater_lookup() -> None:
    panel = build_panel(Settings(), ScriptedLLM())
    assert panel.debater(Role.ADVOCATE).role is Role.ADVOCATE
    with pytest.raises(KeyError, match="judge"):
        panel.debater(Role.JUDGE)
