"""Built-in sample estimates, shipped as JSON inside the package."""

from __future__ import annotations

from functools import lru_cache
from importlib import resources

from app.estimates.models import Estimate, EstimateSummary

_SAMPLES_PACKAGE = "app.estimates.samples"


class EstimateNotFoundError(LookupError):
    def __init__(self, estimate_id: str) -> None:
        super().__init__(f"estimate '{estimate_id}' not found")
        self.estimate_id = estimate_id


class SampleCatalog:
    """Read-only, in-memory catalog of sample estimates."""

    def __init__(self, estimates: list[Estimate]) -> None:
        self._by_id = {e.id: e for e in sorted(estimates, key=lambda e: e.title)}
        if len(self._by_id) != len(estimates):
            raise ValueError("sample estimates must have unique ids")

    def list(self) -> list[EstimateSummary]:
        return [EstimateSummary.of(e) for e in self._by_id.values()]

    def get(self, estimate_id: str) -> Estimate:
        try:
            return self._by_id[estimate_id]
        except KeyError:
            raise EstimateNotFoundError(estimate_id) from None


def load_samples() -> list[Estimate]:
    files = resources.files(_SAMPLES_PACKAGE).iterdir()
    return [
        Estimate.model_validate_json(f.read_text(encoding="utf-8"))
        for f in files
        if f.name.endswith(".json")
    ]


@lru_cache(maxsize=1)
def get_sample_catalog() -> SampleCatalog:
    return SampleCatalog(load_samples())
