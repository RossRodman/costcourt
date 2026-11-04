from __future__ import annotations

import pytest

from app.estimates.catalog import (
    EstimateNotFoundError,
    SampleCatalog,
    get_sample_catalog,
    load_samples,
)
from tests.factories import estimate


def test_bundled_samples_are_valid() -> None:
    samples = load_samples()
    assert {s.id for s in samples} == {
        "house-foundation-frame",
        "office-fit-out",
        "warehouse-slab",
    }


def test_warehouse_totals_are_stable() -> None:
    """Guards the sample data: agents and UI screenshots rely on these figures."""
    totals = get_sample_catalog().get("warehouse-slab").totals
    assert float(totals.direct_cost) == 162_410.00
    assert float(totals.grand_total) == 190_799.27


def test_list_is_sorted_by_title() -> None:
    titles = [s.title for s in get_sample_catalog().list()]
    assert titles == sorted(titles)


def test_get_unknown_raises() -> None:
    with pytest.raises(EstimateNotFoundError, match="nope"):
        get_sample_catalog().get("nope")


def test_rejects_duplicate_ids() -> None:
    with pytest.raises(ValueError, match="unique"):
        SampleCatalog([estimate(), estimate()])
