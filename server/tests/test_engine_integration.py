"""M3 exit criterion: walk the seed world, talk, move, attack, die — no LLM.

Ingests vault_mini, starts a run, and plays several turns through the real engine
+ DB (inside the rolled-back session). Scripted rolls make the death deterministic.
"""

from __future__ import annotations

from pathlib import Path

from sqlmodel import Session, col, select

from halflight.engine.actions import Attack, Move, Talk
from halflight.engine.dice import Dice
from halflight.engine.turn import start_run, take_turn
from halflight.ingest.runner import run_ingest
from halflight.models import Event, PlayerState, Run

from .conftest import FakeEmbedder

FIXTURE = Path(__file__).parent / "fixtures" / "vault_mini"
STATS = {"muscle": 10, "nerve": 10, "wits": 10, "tech": 10, "streetwise": 10, "presence": 10}


class SeqRoller:
    def __init__(self, values: list[int]) -> None:
        self._v = list(values)

    def d20(self) -> int:
        return self._v.pop(0)


def test_walk_talk_attack_die(session: Session, fake_embedder: FakeEmbedder) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    run_id = start_run(
        session,
        character_name="Vex",
        start_location="loc_tram_hub",
        stats=STATS,
        hp=3,
        inventory={"itm_shiv": 1},
    )

    # Turn 1 — talk to Dax, who is at the tram hub.
    r1 = take_turn(session, run_id, Talk(target="npc_dax", topic="the docks"), Dice(0))
    assert r1.valid and r1.outcome == "narrative_only"

    # Turn 2 — move to the under-level, where Vera holds court.
    r2 = take_turn(session, run_id, Move(target="loc_underlevel"), Dice(0))
    assert r2.outcome == "success"
    assert session.get(PlayerState, run_id).location_id == "loc_underlevel"  # type: ignore[union-attr]

    # Turn 3 — swing at Vera, miss, and take a lethal counter.
    r3 = take_turn(session, run_id, Attack(target="npc_vera"), SeqRoller([1, 20]))
    assert r3.outcome == "failure"
    assert any(e.kind == "player_died" for e in r3.scene_events)
    assert r3.significance == 3

    # The world recorded it: player dead, run ended, three events logged.
    player = session.get(PlayerState, run_id)
    assert player is not None and player.hp <= 0
    run = session.get(Run, run_id)
    assert run is not None and run.ended_at is not None
    assert run.cause_of_death == "killed by npc_vera"

    turns = session.exec(
        select(Event.turn_no).where(col(Event.run_id) == run_id).order_by(col(Event.turn_no))
    ).all()
    assert list(turns) == [1, 2, 3]


def test_move_to_unconnected_is_invalid(session: Session, fake_embedder: FakeEmbedder) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    run_id = start_run(
        session, character_name="Vex", start_location="loc_tram_hub", stats=STATS, hp=15
    )
    res = take_turn(session, run_id, Move(target="loc_nowhere"), Dice(0))
    assert not res.valid and res.outcome == "invalid"
    # Player didn't move.
    assert session.get(PlayerState, run_id).location_id == "loc_tram_hub"  # type: ignore[union-attr]
