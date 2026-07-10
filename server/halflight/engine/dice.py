"""Dice. Injectable so the resolver stays deterministic and unit-testable."""

from __future__ import annotations

import random
from typing import Protocol


class Roller(Protocol):
    def d20(self) -> int: ...


class Dice:
    """Seeded RNG. Same seed -> same rolls, for reproducible runs and tests."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def d20(self) -> int:
        return self._rng.randint(1, 20)
