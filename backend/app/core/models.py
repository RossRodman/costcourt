"""Base class for all domain models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class DomainModel(BaseModel):
    """Immutable, strict model.

    Unknown fields are rejected so typos fail loudly, but computed fields are
    silently dropped on input: an object returned by the API (which includes
    them) can be sent straight back.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    @model_validator(mode="before")
    @classmethod
    def _drop_computed_fields(cls, data: Any) -> Any:
        if isinstance(data, dict) and cls.model_computed_fields:
            return {k: v for k, v in data.items() if k not in cls.model_computed_fields}
        return data
