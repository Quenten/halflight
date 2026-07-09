"""Parser tests: frontmatter -> typed rows, hash stability."""

from __future__ import annotations

from pathlib import Path

from halflight.ingest.linter import Note, lint_vault
from halflight.ingest.parser import note_hash, to_row
from halflight.models import Faction, Item, Location, Npc

FIXTURE = Path(__file__).parent / "fixtures" / "vault_mini"


def _notes() -> dict[str, Note]:
    return {n.id: n for n in lint_vault(FIXTURE).notes}


def test_npc_row_mapping() -> None:
    row = to_row(_notes()["npc_dax"])
    assert isinstance(row, Npc)
    assert row.faction_id == "fac_syndicate"
    assert row.home_location_id == "loc_tram_hub"
    assert row.hp_max == 15
    assert row.stats["streetwise"] == 13
    assert row.schedule["night"] == "loc_underlevel"


def test_npc_null_faction_becomes_none() -> None:
    row = to_row(_notes()["npc_vera"])
    assert isinstance(row, Npc)
    assert row.faction_id is None


def test_faction_and_location_and_item_rows() -> None:
    fac = to_row(_notes()["fac_syndicate"])
    assert isinstance(fac, Faction)
    assert "loc_tram_hub" in fac.territory

    loc = to_row(_notes()["loc_tram_hub"])
    assert isinstance(loc, Location)
    assert loc.district == "spindle"
    assert loc.connections == ["loc_underlevel"]

    itm = to_row(_notes()["itm_shiv"])
    assert isinstance(itm, Item)
    assert itm.kind == "weapon"
    assert itm.effects == {"damage": 4}


def test_lore_note_has_no_row() -> None:
    assert to_row(_notes()["lore_colony"]) is None


def test_note_hash_changes_with_body() -> None:
    meta = {"id": "x", "type": "lore"}
    assert note_hash(meta, "a") == note_hash(meta, "a")
    assert note_hash(meta, "a") != note_hash(meta, "b")
    assert note_hash(meta, "a") != note_hash({"id": "y"}, "a")
