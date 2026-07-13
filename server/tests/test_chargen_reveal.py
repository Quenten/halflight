"""Per-step chargen reveal: preview_step rolls one step, and the final build
reproduces the revealed outcomes deterministically."""

from __future__ import annotations

from halflight.engine.lifepath import preview_step, resolve_build


class SeqRoller:
    def __init__(self, values: list[int]) -> None:
        self._v = list(values)

    def d20(self) -> int:
        return self._v.pop(0)


def _kind(step_id: str, option_id: str, rolls: list[int]) -> str:
    out = preview_step(step_id, option_id, SeqRoller(rolls))
    assert out is not None
    return out.kind


def test_preview_step_reflects_the_roll() -> None:
    assert _kind("marked", "betrayal", [20]) == "positive"
    assert _kind("marked", "betrayal", [1]) == "negative"
    assert _kind("marked", "betrayal", [10]) == "neutral"


def test_preview_flat_step_is_chosen() -> None:
    out = preview_step("upbringing", "sump", SeqRoller([]))
    assert out is not None and out.kind == "chosen"


def test_preview_unknown_returns_none() -> None:
    assert preview_step("marked", "nope", SeqRoller([10])) is None


def test_resolve_build_honors_revealed_outcomes() -> None:
    choices = {"upbringing": "sump", "marked": "betrayal", "ran_with": "fixer",
               "last_job": "protection"}
    outcomes = {"marked": "negative", "ran_with": "negative", "last_job": "negative"}
    # A roller that would otherwise roll all-positive must be ignored when outcomes given.
    build = resolve_build("enforcer", choices, SeqRoller([20, 20, 20]), outcomes)
    kinds = {b.step_id: b.outcome_kind for b in build.backstory}
    assert kinds["marked"] == "negative"
    assert kinds["ran_with"] == "negative"
    assert kinds["last_job"] == "negative"
    # negative rolls seed the enemy/missing contacts
    assert {c.name for c in build.contacts} == {"Wick", "Corva", "Dr. Sabec"}


def test_resolve_build_still_rolls_without_outcomes() -> None:
    choices = {"upbringing": "sump", "marked": "betrayal", "ran_with": "fixer",
               "last_job": "protection"}
    build = resolve_build("enforcer", choices, SeqRoller([1, 1, 1]))
    assert all(b.outcome_kind in ("chosen", "negative") for b in build.backstory)
