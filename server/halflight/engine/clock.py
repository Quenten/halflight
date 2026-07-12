"""The city clock — Cinderreach runs on labor shifts, not day and night.

The halflight never changes (permanent dusk), but the colony imposes its own
rhythm: three shifts cycle the decks between packed and curfew-empty. Pure —
derived from a run's accumulated time_ticks, one tick per turn.
"""

from __future__ import annotations

from dataclasses import dataclass

TICKS_PER_SHIFT = 8  # turns spent in one shift before it rolls over


@dataclass(frozen=True)
class Shift:
    key: str  # stable id: "highshift" | "lowshift" | "deadshift"
    name: str  # display name
    mood: str  # one-line scene descriptor for the narrator
    curfew: bool  # deadshift: Watch curfew, being seen costs you


_SHIFTS = [
    Shift(
        "highshift",
        "Highshift",
        "Shift-change crowds pack the decks; vendors shout over the churn and no one "
        "looks twice at anyone.",
        False,
    ),
    Shift(
        "lowshift",
        "Lowshift",
        "The crowds are thinning and shutters are rattling down; the decks are quieter, "
        "the light dimmer, footsteps easier to hear.",
        False,
    ),
    Shift(
        "deadshift",
        "Deadshift",
        "Curfew hour. The decks are near-empty and shuttered, and Watch patrols work the "
        "quiet — anyone still out is worth a second look.",
        True,
    ),
]


def shift_for(time_ticks: int) -> Shift:
    """Which shift the city is in after `time_ticks` turns."""
    return _SHIFTS[(time_ticks // TICKS_PER_SHIFT) % len(_SHIFTS)]
