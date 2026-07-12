"""Faction reputation: violence lowers standing, which shifts NPC attitude."""

from __future__ import annotations

from pathlib import Path

from halflight.engine.actions import Attack
from halflight.engine.gamestate import effective_disposition
from halflight.engine.state import load_state
from halflight.engine.turn import start_run, take_turn
from halflight.ingest.runner import run_ingest
from sqlmodel import Session

from .conftest import FakeEmbedder

FIXTURE = Path(__file__).parent / "fixtures" / "vault_mini"
STATS = {"muscle": 10, "nerve": 10, "wits": 10, "tech": 10, "streetwise": 10, "presence": 10}


class SeqRoller:
    def __init__(self, values: list[int]) -> None:
        self._v = list(values)

    def d20(self) -> int:
        return self._v.pop(0)


def test_attack_lowers_standing_and_attitude(
    session: Session, fake_embedder: FakeEmbedder
) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    run_id = start_run(
        session, character_name="Vex", start_location="loc_tram_hub", stats=STATS, hp=30
    )
    before = load_state(session, run_id).npcs["npc_dax"]
    before_att = effective_disposition(before, {})

    # Hit Dax (fac_syndicate) but don't kill; his faction's standing drops.
    take_turn(session, run_id, Attack(target="npc_dax"), SeqRoller([15, 1]))

    state = load_state(session, run_id)
    assert state.faction_rep.get("fac_syndicate", 0) < 0
    dax = state.npcs["npc_dax"]
    assert effective_disposition(dax, state.faction_rep) < before_att
