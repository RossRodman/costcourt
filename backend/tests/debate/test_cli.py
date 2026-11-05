from __future__ import annotations

import pytest

from app.agents.llm import LLMUnavailableError
from app.debate import __main__ as cli
from tests.fakes import ScriptedLLM, debate_script, scripted_panel


def use_script(monkeypatch: pytest.MonkeyPatch, llm: ScriptedLLM) -> None:
    monkeypatch.setattr(cli, "build_panel", lambda _settings: scripted_panel(llm))


def test_prints_the_whole_debate(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    use_script(monkeypatch, ScriptedLLM(debate_script(rounds=2)))

    cli.main(["warehouse-slab", "--rounds", "2"])

    out = capsys.readouterr().out
    assert "2 round(s)" in out
    assert "=== Round 2 of 2 ===" in out
    assert "Contractor's advocate is thinking" in out
    assert "[01.010] INCREASE: Quantity misses waste." in out
    assert "=== Judge ===" in out
    assert "[01.010] ADJUSTED" in out
    assert "confidence 90%" in out


def test_failed_debate_exits_non_zero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    use_script(monkeypatch, ScriptedLLM([LLMUnavailableError("overloaded")]))

    with pytest.raises(SystemExit) as exc:
        cli.main(["warehouse-slab", "--rounds", "1"])

    assert exc.value.code == 1
    assert "Debate failed: overloaded" in capsys.readouterr().err


def test_missing_api_key_is_a_clean_error() -> None:
    with pytest.raises(SystemExit, match="ANTHROPIC_API_KEY"):
        cli.main(["warehouse-slab"])


def test_unknown_sample_is_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        cli.main(["nope"])
    assert "invalid choice" in capsys.readouterr().err
