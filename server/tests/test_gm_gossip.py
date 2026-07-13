"""Gossip: a witnessed memory spreads to same-faction NPCs as 'told'."""

from __future__ import annotations

from pathlib import Path

from halflight.engine.turn import start_run
from halflight.gm.gossip import propagate_gossip
from halflight.ingest.runner import run_ingest
from halflight.models import Event, Npc, NpcMemory
from halflight.models.runtime import utcnow
from sqlmodel import Session, col, select

from .conftest import FakeEmbedder

# The real vault has several Keelrat NPCs (rook, bosun_grey, mira); vault_mini doesn't.
REPO_VAULT = Path(__file__).parents[2] / "vault"
STATS = {"muscle": 10, "nerve": 10, "wits": 10, "tech": 10, "streetwise": 10, "presence": 10}


def test_gossip_spreads_within_faction(session: Session, fake_embedder: FakeEmbedder) -> None:
    run_ingest(REPO_VAULT, session, fake_embedder)
    run_id = start_run(
        session, character_name="Vex", start_location="loc_rings_lower", stats=STATS, hp=15
    )

    rook = session.get(Npc, "npc_rook")
    assert rook is not None and rook.faction_id == "fac_keelrats"

    event = Event(
        run_id=run_id, turn_no=1, significance=2, location_id="loc_scrapmarket",
        witnesses=["npc_rook"], ts=utcnow(),
    )
    session.add(event)
    session.commit()
    session.add(
        NpcMemory(run_id=run_id, npc_id="npc_rook", event_id=event.id, how_known="witnessed",
                  ts=utcnow())
    )
    session.commit()

    spread = propagate_gossip(session, run_id, max_spread=5)
    assert spread >= 1

    told = session.exec(
        select(NpcMemory).where(
            col(NpcMemory.run_id) == run_id, col(NpcMemory.how_known) == "told"
        )
    ).all()
    assert told
    # Word reached other Keelrat NPCs, not the original witness.
    for m in told:
        assert m.npc_id != "npc_rook"
        peer = session.get(Npc, m.npc_id)
        assert peer is not None and peer.faction_id == "fac_keelrats"


def test_gossip_is_rate_limited(session: Session, fake_embedder: FakeEmbedder) -> None:
    run_ingest(REPO_VAULT, session, fake_embedder)
    run_id = start_run(
        session, character_name="Vex", start_location="loc_rings_lower", stats=STATS, hp=15
    )
    event = Event(run_id=run_id, turn_no=1, significance=2, location_id="loc_scrapmarket",
                  witnesses=["npc_rook"], ts=utcnow())
    session.add(event)
    session.commit()
    session.add(
        NpcMemory(run_id=run_id, npc_id="npc_rook", event_id=event.id, how_known="witnessed",
                  ts=utcnow())
    )
    session.commit()

    assert propagate_gossip(session, run_id, max_spread=1) == 1
