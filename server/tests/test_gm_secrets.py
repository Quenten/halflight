"""Secret reveal: hidden until uncovered by a successful investigate."""

from __future__ import annotations

from pathlib import Path

from halflight.engine.actions import Investigate
from halflight.engine.gamestate import GameState, LocationView, PlayerView
from halflight.engine.results import TurnResult
from halflight.gm.retrieval import retrieve
from halflight.gm.secrets import maybe_reveal_on_investigate, reveal_secrets
from halflight.ingest.runner import run_ingest
from sqlmodel import Session

from .conftest import FakeEmbedder

FIXTURE = Path(__file__).parent / "fixtures" / "vault_mini"
QUERY = "east maintenance shaft skips the fare gates"


def test_reveal_makes_secret_retrievable(session: Session, fake_embedder: FakeEmbedder) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    before = retrieve(QUERY, fake_embedder, session, k=10)
    assert all("maintenance shaft" not in h.body for h in before)  # hidden

    assert reveal_secrets(session, fake_embedder, "loc_tram_hub") == 1

    after = retrieve(QUERY, fake_embedder, session, k=10)
    assert any("maintenance shaft" in h.body for h in after)  # now surfaces


def test_reveal_noop_without_secrets(session: Session, fake_embedder: FakeEmbedder) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    assert reveal_secrets(session, fake_embedder, "loc_underlevel") == 0


def test_investigate_gates_reveal(session: Session, fake_embedder: FakeEmbedder) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    state = GameState(
        player=PlayerView(hp=15, location_id="loc_tram_hub", stats={}),
        location=LocationView(id="loc_tram_hub", name="Tram Hub"),
    )
    action = Investigate(target="loc_tram_hub")

    failed = TurnResult(action=action, valid=True, roll=5, difficulty=15, outcome="narrative_only")
    assert maybe_reveal_on_investigate(session, fake_embedder, action, failed, state) == 0

    passed = TurnResult(action=action, valid=True, roll=18, difficulty=15, outcome="narrative_only")
    assert maybe_reveal_on_investigate(session, fake_embedder, action, passed, state) == 1
