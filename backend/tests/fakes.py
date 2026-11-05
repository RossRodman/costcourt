"""Test doubles for the LLM layer."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from typing import cast

from pydantic import BaseModel

from app.agents.llm import Check, Completion, LLMRequest, T


class ScriptedLLM:
    """Returns pre-written outputs in order and records every request.

    The domain `check` is run on each output and its `ValueError` propagates,
    so tests can assert exactly what an agent would reject.
    """

    def __init__(self, outputs: Iterable[BaseModel] = ()) -> None:
        self._outputs: deque[BaseModel] = deque(outputs)
        self.requests: list[LLMRequest] = []

    def push(self, *outputs: BaseModel) -> None:
        self._outputs.extend(outputs)

    async def generate(
        self, request: LLMRequest, output: type[T], check: Check[T] | None = None
    ) -> Completion[T]:
        self.requests.append(request)
        if not self._outputs:
            raise AssertionError("ScriptedLLM ran out of outputs")
        result = self._outputs.popleft()
        if not isinstance(result, output):
            raise AssertionError(f"expected {output.__name__}, script had {type(result).__name__}")
        typed = cast(T, result)
        if check is not None:
            check(typed)
        return Completion(output=typed, model=request.model, input_tokens=100, output_tokens=50)
