"""SQLModel tables. Importing this package registers all tables on SQLModel.metadata."""

from halflight.models.authored import (
    Faction,
    Item,
    Location,
    LoreChunk,
    NoteIndex,
    Npc,
)
from halflight.models.runtime import (
    Event,
    FactionRep,
    Inventory,
    NpcState,
    PlayerState,
    Run,
)

__all__ = [
    "Event",
    "Faction",
    "FactionRep",
    "Inventory",
    "Item",
    "Location",
    "LoreChunk",
    "NoteIndex",
    "NpcState",
    "Npc",
    "PlayerState",
    "Run",
]
