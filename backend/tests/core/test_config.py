from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Environment, Settings, get_settings


def test_defaults_without_api_key() -> None:
    settings = Settings()
    assert settings.env is Environment.DEV
    assert settings.debate_rounds == 2
    assert not settings.has_api_key


def test_reads_standard_anthropic_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    settings = Settings()
    assert settings.has_api_key
    assert settings.anthropic_api_key is not None
    assert settings.anthropic_api_key.get_secret_value() == "sk-ant-test"


def test_api_key_is_not_leaked_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-secret")
    assert "sk-ant-secret" not in repr(Settings())


def test_blank_api_key_counts_as_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "   ")
    assert not Settings().has_api_key


def test_prefixed_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COSTCOURT_DEBATE_ROUNDS", "4")
    monkeypatch.setenv("COSTCOURT_JUDGE_MODEL", "claude-haiku-5-5")
    settings = Settings()
    assert settings.debate_rounds == 4
    assert settings.judge_model == "claude-haiku-5-5"


def test_reads_dotenv_file(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("COSTCOURT_PORT=9001\n")
    assert Settings().port == 9001


@pytest.mark.parametrize("rounds", [0, 6])
def test_debate_rounds_are_bounded(rounds: int) -> None:
    with pytest.raises(ValidationError):
        Settings(debate_rounds=rounds)


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()
