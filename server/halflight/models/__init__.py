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
    EventChunk,
    FactionRep,
    Inventory,
    NpcMemory,
    NpcState,
    PlayerState,
    Run,
)

__all__ = [
    "Event",
    "EventChunk",
    "Faction",
    "FactionRep",
    "Inventory",
    "Item",
    "Location",
    "LoreChunk",
    "NoteIndex",
    "NpcMemory",
    "NpcState",
    "Npc",
    "PlayerState",
    "Run",
]
