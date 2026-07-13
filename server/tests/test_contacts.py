"""Backstory contacts: seeded from the lifepath into the run as real NPCs and
surfaced in the Known-NPCs journal."""

from __future__ import annotations

from pathlib import Path

from halflight.api.runs import snapshot
from halflight.engine.actions import Talk
from halflight.engine.lifepath import ContactSpec, resolve_build
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


def test_lifepath_collects_contacts_on_negative_rolls() -> None:
    # Three low rolls -> all negative outcomes, each of which seeds a contact.
    build = resolve_build(
        "enforcer",
        {"upbringing": "sump", "marked": "betrayal", "ran_with": "fixer", "last_job": "protection"},
        SeqRoller([1, 1, 1]),
    )
    rels = {c.name: c.relationship for c in build.contacts}
    assert rels == {"Wick": "enemy", "Corva": "enemy", "Dr. Sabec": "missing"}


def test_neutral_rolls_leave_no_contact() -> None:
    # Mid rolls -> neutral outcomes, which carry no contact.
    build = resolve_build(
        "enforcer",
        {"upbringing": "sump", "marked": "betrayal", "ran_with": "fixer", "last_job": "protection"},
        SeqRoller([10, 10, 10]),
    )
    assert build.contacts == []


def test_contacts_seed_the_journal(session: Session, fake_embedder: FakeEmbedder) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    contacts = [
        ContactSpec("Corva", "enemy", "set you up as the fall", location=""),
        ContactSpec("Sabec", "ally", "owes you a clinic debt", location="loc_tram_hub"),
        ContactSpec("Ghost", "missing", "never found the body", location=""),
    ]
    run_id = start_run(
        session, character_name="Vex", start_location="loc_underlevel",
        stats=STATS, hp=20, contacts=contacts,
    )
    journal = {k.name: k for k in snapshot(session, run_id).known_npcs}

    assert set(journal) == {"Corva", "Sabec", "Ghost"}
    assert journal["Corva"].relationship == "enemy"
    assert journal["Corva"].disposition == -15
    assert journal["Corva"].last_seen == "Unknown"  # location "" -> unknown
    assert journal["Sabec"].disposition == 15  # ally
    assert journal["Ghost"].alive is False  # 'missing' contacts start not-alive
    assert journal["Corva"].note == "set you up as the fall"


def test_meeting_an_npc_adds_them_to_the_journal(
    session: Session, fake_embedder: FakeEmbedder
) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    run_id = start_run(
        session, character_name="Vex", start_location="loc_tram_hub", stats=STATS, hp=20
    )
    # Dax isn't known until you share a scene with him.
    assert "Dax" not in {k.name for k in snapshot(session, run_id).known_npcs}
    take_turn(session, run_id, Talk(target="npc_dax", topic="rumors"), SeqRoller([]))
    assert "Dax" in {k.name for k in snapshot(session, run_id).known_npcs}
