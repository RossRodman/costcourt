from __future__ import annotations

from pathlib import Path

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


def test_demo_needs_no_key(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("COSTCOURT_DEMO_DELAY_S", "0")
    cli.main(["warehouse-slab", "--demo"])
    out = capsys.readouterr().out
    assert "2 round(s)" in out and "+14.62%" in out


def test_demo_for_unrecorded_sample() -> None:
    with pytest.raises(SystemExit, match="no demo"):
        cli.main(["office-fit-out", "--demo"])


def test_saves_the_report_and_writes_an_export(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    monkeypatch.setenv("COSTCOURT_DEMO_DELAY_S", "0")

    cli.main(["warehouse-slab", "--demo", "--report", "out.md"])

    out = capsys.readouterr().out
    [saved] = (tmp_path / "data" / "reports").glob("*.json")
    assert f"Report saved to data/reports/{saved.name}" in out
    assert "Report written to out.md" in out
    assert (tmp_path / "out.md").read_text(encoding="utf-8").startswith("# CostCourt report")


def test_report_path_needs_a_known_extension(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        cli.main(["warehouse-slab", "--demo", "--report", "out.pdf"])
    assert "unknown report extension '.pdf'" in capsys.readouterr().err
