"""Lifepath resolver: deterministic given the dice."""

from __future__ import annotations

import pytest
from halflight.engine.lifepath import CLASSES, STEPS, resolve_build

CHOICES = {"upbringing": "crew", "marked": "ambition", "ran_with": "fixer", "last_job": "salvage"}


class FixedRoller:
    def __init__(self, value: int) -> None:
        self.value = value

    def d20(self) -> int:
        return self.value


def test_tables_are_well_formed() -> None:
    assert len(CLASSES) == 4
    assert [s.id for s in STEPS] == ["upbringing", "marked", "ran_with", "last_job"]
    # steps 2-4 roll, step 1 does not
    assert [s.rolls for s in STEPS] == [False, True, True, True]
    for s in STEPS:
        if s.rolls:
            for o in s.options:
                kinds = {oc.kind for oc in o.outcomes}
                assert kinds == {"positive", "neutral", "negative"}, (s.id, o.id)


def test_positive_rolls_help() -> None:
    b = resolve_build("enforcer", CHOICES, FixedRoller(20))  # everything positive
    assert "itm_rail_maul" in b.inventory
    assert b.stats["muscle"] == 15  # enforcer 14 + crew upbringing +1
    assert b.credits > 40  # base 40 + positive scrip
    assert len(b.backstory) == 4
    assert all(step.outcome_kind in ("chosen", "positive") for step in b.backstory)


def test_negative_rolls_hurt_but_hp_clamped() -> None:
    b = resolve_build("chrome_rat", CHOICES, FixedRoller(1))  # everything negative
    assert b.hp >= 1
    assert any(step.outcome_kind == "negative" for step in b.backstory)


def test_unknown_class_raises() -> None:
    with pytest.raises(ValueError):
        resolve_build("nobody", CHOICES, FixedRoller(10))
