"""Application settings, loaded from environment variables and `.env`."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEV = "dev"
    TEST = "test"
    PROD = "prod"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


Effort = Literal["low", "medium", "high", "xhigh", "max"]


class Settings(BaseSettings):
    """All runtime configuration lives here.

    Every field can be overridden with an `COSTCOURT_`-prefixed env var,
    except the API key, which uses the standard `ANTHROPIC_API_KEY`.
    """

    model_config = SettingsConfigDict(
        env_prefix="COSTCOURT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
        validate_by_name=True,
    )

    # --- runtime -----------------------------------------------------------
    env: Environment = Environment.DEV
    log_level: LogLevel = LogLevel.INFO
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)

    # --- LLM ---------------------------------------------------------------
    anthropic_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="ANTHROPIC_API_KEY",
    )
    debater_model: str = "claude-opus-5-5"
    judge_model: str = "claude-opus-5-5"
    debater_effort: Effort = "medium"
    """How hard debaters think. Higher means deeper arguments, more tokens."""
    judge_effort: Effort = "high"
    max_output_tokens: int = Field(default=16_000, ge=1024, le=64_000)
    """Per call, thinking included."""
    request_timeout_s: float = Field(default=300.0, gt=0)
    llm_max_attempts: int = Field(default=2, ge=1, le=5)
    """Attempts per agent turn when the model's output fails validation."""
    server_fallback: bool = True
    """Let the API retry a refused request on Anthropic's recommended fallback model."""

    # --- debate ------------------------------------------------------------
    debate_rounds: int = Field(default=2, ge=1, le=5)
    demo_delay_s: float = Field(default=2.5, ge=0, le=30)
    """Simulated thinking time per agent in demo debates."""

    # --- reports -----------------------------------------------------------
    reports_dir: Path = Path("data/reports")
    """Where completed debate reports are saved (relative to the working directory)."""

    @property
    def has_api_key(self) -> bool:
        return self.anthropic_api_key is not None and bool(
            self.anthropic_api_key.get_secret_value().strip()
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings instance (cached)."""
    return Settings()
