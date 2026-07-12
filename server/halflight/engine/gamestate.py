"""In-memory snapshot of what one turn needs. Pure — no DB imports.

The state layer (state.py) builds a GameState from the DB for a run; the resolver
reads it to produce a TurnResult. Keeping it DB-free is what lets the resolver be
unit-tested with hand-built scenes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

BASELINE_STAT = 10


@dataclass
class PlayerView:
    hp: int
    location_id: str
    stats: dict[str, int]
    inventory: dict[str, int] = field(default_factory=dict)  # item_id -> qty
    credits: int = 0
    time_ticks: int = 0

    def stat(self, name: str) -> int:
        return self.stats.get(name, BASELINE_STAT)


@dataclass
class NpcView:
    id: str
    hp: int
    stats: dict[str, int]
    location_id: str
    name: str = ""
    alive: bool = True
    disposition: int = 0
    faction_id: str | None = None

    def stat(self, name: str) -> int:
        return self.stats.get(name, BASELINE_STAT)


@dataclass
class LocationView:
    id: str
    name: str = ""
    connections: list[str] = field(default_factory=list)
    danger: int = 0


@dataclass
class ItemView:
    id: str
    kind: str
    value: int = 0
    effects: dict[str, Any] = field(default_factory=dict)


@dataclass
class GameState:
    player: PlayerView
    location: LocationView  # the player's current location
    npcs: dict[str, NpcView] = field(default_factory=dict)  # npcs in the current scene
    items: dict[str, ItemView] = field(default_factory=dict)  # catalog for referenced items
    faction_rep: dict[str, int] = field(default_factory=dict)  # faction_id -> standing


def effective_disposition(npc: NpcView, faction_rep: dict[str, int]) -> int:
    """An NPC's attitude = their personal disposition plus your standing with their faction."""
    return npc.disposition + (faction_rep.get(npc.faction_id, 0) if npc.faction_id else 0)
