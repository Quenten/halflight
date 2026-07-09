"""Map linter Notes to typed table rows and compute change-detection hashes.

Ingestion reuses the linter's parse (frontmatter + body) so there's one parser.
`to_row` builds the authored row for a note; lore notes have no typed table and
return None (they contribute chunks only). `note_hash` covers frontmatter and
body, so any edit re-triggers embedding for that note.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlmodel import SQLModel

from halflight.ingest.linter import Note
from halflight.models import Faction, Item, Location, Npc


def note_hash(meta: dict[str, Any], body: str) -> str:
    canonical = json.dumps(meta, sort_keys=True, default=str) + "\n" + body
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _list(value: Any) -> list[str]:
    return [str(v) for v in value] if isinstance(value, list) else []


def to_row(note: Note) -> SQLModel | None:
    """Build the authored row for a note. Returns None for lore (chunks only)."""
    m = note.meta

    if note.type == "faction":
        return Faction(
            id=note.id,
            name=str(m.get("name", note.id)),
            rivals=_list(m.get("rivals")),
            allies=_list(m.get("allies")),
            territory=_list(m.get("territory")),
        )
    if note.type == "location":
        return Location(
            id=note.id,
            name=str(m.get("name", note.id)),
            district=str(m.get("district", "")),
            danger=int(m.get("danger", 0)),
            connections=_list(m.get("connections")),
            tags=_list(m.get("tags")),
        )
    if note.type == "item":
        return Item(
            id=note.id,
            name=str(m.get("name", note.id)),
            kind=str(m.get("kind", "misc")),
            value=int(m.get("value", 0)),
            effects=m.get("effects") if isinstance(m.get("effects"), dict) else {},
        )
    if note.type == "npc":
        faction = m.get("faction")
        return Npc(
            id=note.id,
            name=str(m.get("name", note.id)),
            faction_id=None if faction in (None, "null", "") else str(faction),
            role=str(m.get("role", "")),
            home_location_id=str(m["location"]) if m.get("location") else None,
            disposition_default=int(m.get("disposition_default", 0)),
            stats=m.get("stats") if isinstance(m.get("stats"), dict) else {},
            hp_max=int(m.get("hp", 0)),
            schedule=m.get("schedule") if isinstance(m.get("schedule"), dict) else {},
        )
    return None
