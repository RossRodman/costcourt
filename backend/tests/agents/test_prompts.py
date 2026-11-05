from __future__ import annotations

from app.agents.prompts import INSTRUCTIONS
from app.debate.models import DEBATERS, Role


def test_every_role_has_instructions() -> None:
    assert set(INSTRUCTIONS) == set(Role)


def test_debaters_share_the_debate_rules_and_differ_in_role() -> None:
    texts = [INSTRUCTIONS[r] for r in DEBATERS]
    assert all("How to argue well" in t for t in texts)
    assert len(set(texts)) == len(DEBATERS)


def test_judge_does_not_get_debater_rules() -> None:
    assert "How to argue well" not in INSTRUCTIONS[Role.JUDGE]
    assert "rule on every line item" in INSTRUCTIONS[Role.JUDGE]
