"""The city shift clock: ticks cycle Highshift -> Lowshift -> Deadshift, and
deadshift curfew makes violence hotter."""

from __future__ import annotations

from pathlib import Path

from halflight.engine.actions import Attack
from halflight.engine.clock import TICKS_PER_SHIFT, shift_for
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


def test_shift_cycles_and_wraps() -> None:
    assert shift_for(0).key == "highshift"
    assert shift_for(TICKS_PER_SHIFT).key == "lowshift"
    assert shift_for(2 * TICKS_PER_SHIFT).key == "deadshift"
    assert shift_for(3 * TICKS_PER_SHIFT).key == "highshift"  # wraps
    assert shift_for(2 * TICKS_PER_SHIFT).curfew is True
    assert shift_for(0).curfew is False


def test_turn_advances_the_clock(session: Session, fake_embedder: FakeEmbedder) -> None:
    from halflight.engine.actions import Talk

    run_ingest(FIXTURE, session, fake_embedder)
    run_id = start_run(
        session, character_name="Vex", start_location="loc_tram_hub", stats=STATS, hp=30
    )
    assert load_state(session, run_id).player.time_ticks == 0
    take_turn(session, run_id, Talk(target="npc_dax", topic="rumors"), SeqRoller([]))
    assert load_state(session, run_id).player.time_ticks == 1


def test_deadshift_curfew_raises_heat(session: Session, fake_embedder: FakeEmbedder) -> None:
    run_ingest(FIXTURE, session, fake_embedder)

    # Daytime attack: baseline heat.
    day = start_run(
        session, character_name="Day", start_location="loc_tram_hub", stats=STATS, hp=40
    )
    take_turn(session, day, Attack(target="npc_dax"), SeqRoller([15, 1]))
    day_heat = load_state(session, day).player.heat

    # Curfew attack: same roll, but time sits in deadshift -> one extra heat.
    night = start_run(
        session, character_name="Night", start_location="loc_tram_hub", stats=STATS, hp=40
    )
    _bump_to_deadshift(session, night)
    take_turn(session, night, Attack(target="npc_dax"), SeqRoller([15, 1]))
    night_heat = load_state(session, night).player.heat
    assert night_heat == day_heat + 1


def _bump_to_deadshift(session: Session, run_id: int) -> None:
    from halflight.models import PlayerState

    ps = session.get(PlayerState, run_id)
    assert ps is not None
    ps.time_ticks = 2 * TICKS_PER_SHIFT  # deadshift
    session.add(ps)
    session.commit()
