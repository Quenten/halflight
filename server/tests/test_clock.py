"""The city shift clock: ticks cycle Highshift -> Lowshift -> Deadshift."""

from __future__ import annotations

from pathlib import Path

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
