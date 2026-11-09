from __future__ import annotations

from app.agents.context import render_estimate, render_transcript
from app.debate.models import Argument, Role, Stance, Turn
from app.estimates.catalog import get_sample_catalog
from app.estimates.models import Markups
from tests.factories import estimate, line_item


def test_estimate_lists_every_item_and_the_totals() -> None:
    est = get_sample_catalog().get("warehouse-slab")
    text = render_estimate(est)
    for item in est.items:
        assert f"| {item.id} |" in text
    assert (
        "| 02.020 | Ready-mix concrete 4000 psi to 200 mm slab | concrete | m3 | 420 | 165 |"
        in text
    )
    assert "Grand total: 190,799.27 USD" in text
    assert "Contingency 3% of direct cost: 4,872.30 USD" in text


def test_estimate_render_is_deterministic() -> None:
    est = get_sample_catalog().get("office-fit-out")
    assert render_estimate(est) == render_estimate(est)


def test_numbers_keep_meaningful_decimals() -> None:
    est = estimate(
        line_item(id="a", quantity="2.5", unit_rate="0.9"),
        line_item(id="b", quantity="0.125", unit_rate=12500),
        markups=Markups(tax="7.5"),
    )
    text = render_estimate(est)
    assert "| 2.50 | 0.90 | 2.25 |" in text
    assert "| 0.125 | 12,500 | 1,562.50 |" in text
    assert "Tax 7.50% of subtotal" in text


def test_missing_location_is_explicit() -> None:
    assert "Location: not stated" in render_estimate(estimate())


def test_empty_transcript() -> None:
    assert "has not started" in render_transcript([])


def test_transcript_groups_by_round_and_shows_proposals() -> None:
    turns = [
        Turn(round=1, role=Role.ESTIMATOR, summary="The estimate is sound overall."),
        Turn(
            round=1,
            role=Role.ENGINEER,
            summary="Concrete volume is short.",
            arguments=(
                Argument(
                    line_item_id="02.020",
                    stance=Stance.INCREASE,
                    claim="Slab volume is understated.",
                    reasoning="60 x 40 x 0.2 = 480 m3 before waste.",
                    proposed_quantity=495,  # type: ignore[arg-type]
                    rebuts=Role.ESTIMATOR,
                ),
                Argument(
                    line_item_id=None,
                    stance=Stance.MISSING,
                    claim="No edge insulation priced.",
                    reasoning="Required for a heated warehouse.",
                ),
            ),
        ),
        Turn(round=2, role=Role.ADVOCATE, summary="Agree with the engineer on volume."),
    ]
    text = render_transcript(turns)
    assert text.index("## Round 1") < text.index("### Engineer") < text.index("## Round 2")
    assert "### Estimator\nThe estimate is sound overall.\n\n- (no arguments)" in text
    assert (
        "- [02.020] INCREASE: Slab volume is understated. "
        "(proposed quantity 495; answering the estimator)"
    ) in text
    assert "- [missing scope] MISSING: No edge insulation priced." in text
    assert "### Contractor's advocate" in text
