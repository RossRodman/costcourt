from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import anthropic
import httpx2
import pytest
from pydantic import BaseModel, ValidationError

from app.agents.llm import (
    ClaudeLLM,
    LLMInvalidOutputError,
    LLMNotConfiguredError,
    LLMRefusalError,
    LLMRequest,
    LLMUnavailableError,
)
from app.core.config import Settings


class Answer(BaseModel):
    value: int


def response(
    parsed: BaseModel | None = None,
    *,
    stop_reason: str = "end_turn",
    model: str = "claude-opus-5-5",
    category: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        parsed_output=parsed,
        stop_reason=stop_reason,
        stop_details=SimpleNamespace(category=category) if stop_reason == "refusal" else None,
        model=model,
        usage=SimpleNamespace(input_tokens=1200, output_tokens=300, cache_read_input_tokens=900),
    )


class StubClient:
    """Mimics `AsyncAnthropic().beta.messages.parse` with scripted results."""

    def __init__(self, *results: Any) -> None:
        self._results = list(results)
        self.calls: list[dict[str, Any]] = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(parse=self._parse))

    async def _parse(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        result = self._results.pop(0)
        if isinstance(result, BaseException):
            raise result
        return result


REQUEST = LLMRequest(
    model="claude-opus-5-5",
    effort="high",
    instructions="You are the judge.",
    context="# Estimate ...",
    prompt="Rule now.",
)


def llm(client: StubClient, **kwargs: Any) -> ClaudeLLM:
    return ClaudeLLM(client, max_tokens=16_000, max_attempts=2, **kwargs)  # type: ignore[arg-type]


def validation_error() -> ValidationError:
    try:
        Answer.model_validate({"value": "not a number"})
    except ValidationError as exc:
        return exc
    raise AssertionError("unreachable")


async def test_success_returns_parsed_output_and_usage() -> None:
    client = StubClient(response(Answer(value=42)))
    completion = await llm(client).generate(REQUEST, Answer)

    assert completion.output == Answer(value=42)
    assert (completion.input_tokens, completion.output_tokens) == (1200, 300)
    assert completion.cache_read_tokens == 900
    assert completion.attempts == 1


async def test_request_shape() -> None:
    client = StubClient(response(Answer(value=1)))
    await llm(client).generate(REQUEST, Answer)

    call = client.calls[0]
    assert call["model"] == "claude-opus-5-5"
    assert call["max_tokens"] == 16_000
    assert call["output_format"] is Answer
    assert call["output_config"] == {"effort": "high"}
    assert call["messages"] == [{"role": "user", "content": "Rule now."}]
    # role instructions first, then the shared estimate marked for caching
    assert call["system"][0] == {"type": "text", "text": "You are the judge."}
    assert call["system"][1]["cache_control"] == {"type": "ephemeral"}
    # refusals fall back server-side by default
    assert call["fallbacks"] == "default"
    assert call["betas"] == ["server-side-fallback-2026-07-01"]


async def test_reports_the_model_that_actually_answered() -> None:
    client = StubClient(response(Answer(value=1), model="claude-opus-5"))
    completion = await llm(client).generate(REQUEST, Answer)
    assert completion.model == "claude-opus-5"


@pytest.mark.parametrize(
    ("model", "server_fallback"), [("claude-haiku-5-5", True), ("claude-opus-5-5", False)]
)
async def test_fallback_can_be_off(model: str, server_fallback: bool) -> None:
    client = StubClient(response(Answer(value=1)))
    request = LLMRequest(model=model, effort="low", instructions="i", context="c", prompt="p")
    await llm(client, server_fallback=server_fallback).generate(request, Answer)
    assert "fallbacks" not in client.calls[0]
    assert "betas" not in client.calls[0]


async def test_failed_check_retries_with_feedback() -> None:
    client = StubClient(response(Answer(value=-1)), response(Answer(value=7)))

    def must_be_positive(answer: Answer) -> None:
        if answer.value < 0:
            raise ValueError("value must be positive")

    completion = await llm(client).generate(REQUEST, Answer, must_be_positive)

    assert completion.output.value == 7
    assert completion.attempts == 2
    retry_prompt = client.calls[1]["messages"][0]["content"]
    assert retry_prompt.startswith("Rule now.")
    assert "rejected for this reason:\nvalue must be positive" in retry_prompt


async def test_schema_mismatch_retries_with_field_errors() -> None:
    client = StubClient(validation_error(), response(Answer(value=3)))
    completion = await llm(client).generate(REQUEST, Answer)

    assert completion.output.value == 3
    assert "- value: Input should be a valid integer" in client.calls[1]["messages"][0]["content"]


async def test_truncated_answer_retries() -> None:
    client = StubClient(response(None, stop_reason="max_tokens"), response(Answer(value=1)))
    completion = await llm(client).generate(REQUEST, Answer)
    assert "cut off" in client.calls[1]["messages"][0]["content"]
    assert completion.attempts == 2


async def test_gives_up_after_max_attempts() -> None:
    client = StubClient(validation_error(), validation_error())
    with pytest.raises(LLMInvalidOutputError, match="after 2 attempts"):
        await llm(client).generate(REQUEST, Answer)
    assert len(client.calls) == 2


async def test_refusal_raises_with_category() -> None:
    client = StubClient(response(None, stop_reason="refusal", category="cyber"))
    with pytest.raises(LLMRefusalError, match="cyber") as exc:
        await llm(client).generate(REQUEST, Answer)
    assert exc.value.category == "cyber"


async def test_connection_error_is_wrapped() -> None:
    error = anthropic.APIConnectionError(
        request=httpx2.Request("POST", "https://api.anthropic.com")
    )
    with pytest.raises(LLMUnavailableError, match="Claude API call failed"):
        await llm(StubClient(error)).generate(REQUEST, Answer)


async def test_bad_api_key_is_reported_clearly() -> None:
    req = httpx2.Request("POST", "https://api.anthropic.com")
    error = anthropic.AuthenticationError(
        "invalid x-api-key", response=httpx2.Response(401, request=req), body=None
    )
    with pytest.raises(LLMUnavailableError, match="key was rejected"):
        await llm(StubClient(error)).generate(REQUEST, Answer)


def test_from_settings_requires_a_key() -> None:
    with pytest.raises(LLMNotConfiguredError):
        ClaudeLLM.from_settings(Settings())
