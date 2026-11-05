from __future__ import annotations

import pytest

from app.agents import __main__ as cli
from tests.fakes import ScriptedLLM, scripted_panel, turn_draft


def test_runs_one_turn(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    llm = ScriptedLLM([turn_draft()])
    monkeypatch.setattr(cli, "build_panel", lambda _settings: scripted_panel(llm))

    cli.main(["warehouse-slab", "--role", "advocate"])

    out = capsys.readouterr().out
    assert "Contractor's advocate is reviewing" in out
    assert "[01.010] INCREASE: Quantity misses waste.  (qty 12)" in out
    assert llm.requests[0].instructions.count("CONTRACTOR'S ADVOCATE") >= 1


def test_missing_api_key_is_a_clean_error() -> None:
    with pytest.raises(SystemExit, match="ANTHROPIC_API_KEY"):
        cli.main(["warehouse-slab"])
