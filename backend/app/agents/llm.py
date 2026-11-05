"""Structured-output LLM access.

Agents depend on the small `StructuredLLM` protocol, not on the Anthropic SDK,
so the debate can be tested with a scripted fake and the provider stays
swappable. `ClaudeLLM` is the production implementation.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, Protocol, TypeVar

import anthropic
import pydantic
from pydantic import BaseModel

from app.core.config import Effort, Settings

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)
U = TypeVar("U", bound=BaseModel)

Check = Callable[[T], None]
"""Domain check on a parsed output. Raise `ValueError` with a message the model can act on."""

_FALLBACK_BETA = "server-side-fallback-2026-07-01"


# --------------------------------------------------------------------- errors


class LLMError(Exception):
    """Base class for every failure an agent call can surface."""


class LLMNotConfiguredError(LLMError):
    def __init__(self) -> None:
        super().__init__("ANTHROPIC_API_KEY is not set; add it to backend/.env")


class LLMUnavailableError(LLMError):
    """The API could not be reached or returned an error after retries."""


class LLMRefusalError(LLMError):
    def __init__(self, category: str | None) -> None:
        super().__init__(f"the model declined the request (category: {category or 'unknown'})")
        self.category = category


class LLMInvalidOutputError(LLMError):
    """The model's output failed validation on every attempt."""


# --------------------------------------------------------------------- contract


@dataclass(frozen=True, slots=True)
class LLMRequest:
    model: str
    effort: Effort
    instructions: str
    """Role instructions. Static per role, so it caches well."""
    context: str
    """Material shared by every call in a debate (the estimate). Cached."""
    prompt: str
    """What this specific call is asked to do."""


@dataclass(frozen=True, slots=True)
class Completion(Generic[T]):
    output: T
    model: str
    """Model that actually answered (differs from the request after a fallback)."""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    attempts: int = 1

    def with_output(self, output: U) -> Completion[U]:
        """Same call metadata, different (e.g. enriched) output."""
        return Completion(
            output=output,
            model=self.model,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            cache_read_tokens=self.cache_read_tokens,
            attempts=self.attempts,
        )


class StructuredLLM(Protocol):
    async def generate(
        self, request: LLMRequest, output: type[T], check: Check[T] | None = None
    ) -> Completion[T]: ...


def feedback_prompt(prompt: str, problem: str) -> str:
    """Append a correction note after a rejected attempt."""
    return (
        f"{prompt}\n\n"
        "IMPORTANT: your previous answer was rejected for this reason:\n"
        f"{problem}\n"
        "Answer again, fixing exactly that."
    )


# --------------------------------------------------------------------- Claude


class ClaudeLLM:
    """`StructuredLLM` backed by the Claude Messages API.

    - Structured outputs: the response is constrained to the output model's
      JSON schema and parsed into it by the SDK.
    - Self-correction: if parsing or the domain `check` fails, the call is
      retried with the reason appended, up to `max_attempts` times.
    - Refusals: opt into server-side fallback so a declined request is retried
      on Anthropic's recommended model; a final refusal raises.
    """

    def __init__(
        self,
        client: anthropic.AsyncAnthropic,
        *,
        max_tokens: int,
        max_attempts: int = 2,
        server_fallback: bool = True,
    ) -> None:
        self._client = client
        self._max_tokens = max_tokens
        self._max_attempts = max_attempts
        self._server_fallback = server_fallback

    @classmethod
    def from_settings(cls, settings: Settings) -> ClaudeLLM:
        if not settings.has_api_key or settings.anthropic_api_key is None:
            raise LLMNotConfiguredError
        client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key.get_secret_value(),
            timeout=settings.request_timeout_s,
        )
        return cls(
            client,
            max_tokens=settings.max_output_tokens,
            max_attempts=settings.llm_max_attempts,
            server_fallback=settings.server_fallback,
        )

    async def generate(
        self, request: LLMRequest, output: type[T], check: Check[T] | None = None
    ) -> Completion[T]:
        prompt = request.prompt
        problem = "no attempt made"

        for attempt in range(1, self._max_attempts + 1):
            try:
                response = await self._client.beta.messages.parse(
                    model=request.model,
                    max_tokens=self._max_tokens,
                    system=[
                        {"type": "text", "text": request.instructions},
                        {
                            "type": "text",
                            "text": request.context,
                            "cache_control": {"type": "ephemeral"},
                        },
                    ],
                    messages=[{"role": "user", "content": prompt}],
                    output_format=output,
                    output_config={"effort": request.effort},
                    **self._fallback_options(request.model),
                )
            except pydantic.ValidationError as exc:
                problem = _describe_validation_error(exc)
            except anthropic.AuthenticationError as exc:
                raise LLMUnavailableError("the Anthropic API key was rejected") from exc
            except (anthropic.APIStatusError, anthropic.APIConnectionError) as exc:
                raise LLMUnavailableError(f"Claude API call failed: {exc}") from exc
            else:
                if response.stop_reason == "refusal":
                    details = response.stop_details
                    raise LLMRefusalError(details.category if details else None)

                parsed = response.parsed_output
                if response.stop_reason == "max_tokens" or parsed is None:
                    problem = "the answer was cut off; be more concise"
                else:
                    try:
                        if check is not None:
                            check(parsed)
                    except ValueError as exc:
                        problem = str(exc)
                    else:
                        usage = response.usage
                        log.info(
                            "claude %s: %d in / %d out / %d cached tokens (attempt %d)",
                            response.model,
                            usage.input_tokens,
                            usage.output_tokens,
                            usage.cache_read_input_tokens or 0,
                            attempt,
                        )
                        return Completion(
                            output=parsed,
                            model=response.model,
                            input_tokens=usage.input_tokens,
                            output_tokens=usage.output_tokens,
                            cache_read_tokens=usage.cache_read_input_tokens or 0,
                            attempts=attempt,
                        )

            log.warning("attempt %d/%d rejected: %s", attempt, self._max_attempts, problem)
            prompt = feedback_prompt(request.prompt, problem)

        raise LLMInvalidOutputError(
            f"no valid answer after {self._max_attempts} attempts; last problem: {problem}"
        )

    def _fallback_options(self, model: str) -> dict[str, Any]:
        # Haiku has no server-side fallback (a fallback list would 400).
        if not self._server_fallback or "haiku" in model:
            return {}
        return {"betas": [_FALLBACK_BETA], "fallbacks": "default"}


def _describe_validation_error(exc: pydantic.ValidationError) -> str:
    lines = []
    for err in exc.errors()[:10]:
        where = ".".join(str(p) for p in err["loc"]) or "output"
        lines.append(f"- {where}: {err['msg']}")
    return "the JSON did not match the required schema:\n" + "\n".join(lines)
