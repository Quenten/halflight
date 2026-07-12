"""Event memory: significant turns get embedded and resurface in retrieval."""

from __future__ import annotations

from pathlib import Path

from halflight.engine.actions import Attack, Move
from halflight.engine.gamestate import GameState, LocationView, NpcView, PlayerView
from halflight.engine.results import SceneEvent, TurnResult
from halflight.engine.turn import start_run
from halflight.gm.context import build_context
from halflight.gm.memory import record_event_memory, scene_npc_memories
from halflight.gm.retrieval import retrieve
from halflight.ingest.runner import run_ingest
from halflight.models import Event
from halflight.models.runtime import utcnow
from sqlmodel import Session

from .conftest import FakeEmbedder

FIXTURE = Path(__file__).parent / "fixtures" / "vault_mini"
STATS = {"muscle": 10, "nerve": 10, "wits": 10, "tech": 10, "streetwise": 10, "presence": 10}


def _kill_result() -> TurnResult:
    return TurnResult(
        action=Attack(target="npc_dax"),
        valid=True,
        outcome="success",
        scene_events=[SceneEvent(kind="npc_died", detail={"npc": "npc_dax"})],
        significance=2,
    )


def test_records_and_retrieves_event(session: Session, fake_embedder: FakeEmbedder) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    run_id = start_run(
        session, character_name="Vex", start_location="loc_tram_hub", stats=STATS, hp=15
    )
    session.add(
        Event(run_id=run_id, turn_no=1, significance=2, location_id="loc_tram_hub", ts=utcnow())
    )
    session.commit()

    desc = record_event_memory(
        session, fake_embedder, run_id=run_id, turn_no=1, result=_kill_result(),
        actor="Vex", location="Tram Hub",
    )
    assert desc is not None
    assert "killed" in desc and "Dax" in desc  # npc id resolved to display name

    hits = retrieve(desc, fake_embedder, session, k=6, run_id=run_id)
    assert any(h.source_type == "event" for h in hits)

    # Without a run scope, event memory is not surfaced.
    lore_only = retrieve(desc, fake_embedder, session, k=6)
    assert all(h.source_type != "event" for h in lore_only)


def test_insignificant_event_not_recorded(
    session: Session, fake_embedder: FakeEmbedder
) -> None:
    run_id = start_run(
        session, character_name="Vex", start_location="loc_tram_hub", stats=STATS, hp=15
    )
    trivial = TurnResult(action=Move(target="loc_underlevel"), valid=True, outcome="success")
    assert record_event_memory(
        session, fake_embedder, run_id=run_id, turn_no=1, result=trivial,
        actor="Vex", location="Tram Hub",
    ) is None


def test_witness_remembers_and_reaches_context(
    session: Session, fake_embedder: FakeEmbedder
) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    run_id = start_run(
        session, character_name="Vex", start_location="loc_underlevel", stats=STATS, hp=15
    )
    # Vera was present when the player killed Dax.
    session.add(
        Event(run_id=run_id, turn_no=1, significance=2, location_id="loc_underlevel",
              witnesses=["npc_vera"], ts=utcnow())
    )
    session.commit()
    record_event_memory(
        session, fake_embedder, run_id=run_id, turn_no=1, result=_kill_result(),
        actor="Vex", location="Under-level 3",
    )

    mems = scene_npc_memories(session, run_id, ["npc_vera"])
    assert "npc_vera" in mems and any("killed" in m for m in mems["npc_vera"])

    state = GameState(
        player=PlayerView(hp=15, location_id="loc_underlevel", stats={}),
        location=LocationView(id="loc_underlevel", name="Under-level 3"),
        npcs={"npc_vera": NpcView(id="npc_vera", name="Vera", hp=18, stats={},
                                  location_id="loc_underlevel")},
    )
    ctx = build_context(state, _kill_result(), [], "size up Vera", mems)
    assert "Vera remembers" in ctx


def test_victim_does_not_remember(session: Session, fake_embedder: FakeEmbedder) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    run_id = start_run(
        session, character_name="Vex", start_location="loc_tram_hub", stats=STATS, hp=15
    )
    # Dax is listed as a witness but dies this turn — the dead don't remember.
    session.add(
        Event(run_id=run_id, turn_no=1, significance=2, location_id="loc_tram_hub",
              witnesses=["npc_dax"], ts=utcnow())
    )
    session.commit()
    record_event_memory(
        session, fake_embedder, run_id=run_id, turn_no=1, result=_kill_result(),
        actor="Vex", location="Tram Hub",
    )
    assert "npc_dax" not in scene_npc_memories(session, run_id, ["npc_dax"])
