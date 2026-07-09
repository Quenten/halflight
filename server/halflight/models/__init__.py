"""SQLModel tables. Importing this package registers all tables on SQLModel.metadata."""

from halflight.models.authored import (
    Faction,
    Item,
    Location,
    LoreChunk,
    NoteIndex,
    Npc,
)

__all__ = ["Faction", "Item", "Location", "LoreChunk", "NoteIndex", "Npc"]
