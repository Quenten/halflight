"""Retrieval over ingested lore_chunks (rolled-back DB session, fake embedder)."""

from __future__ import annotations

from pathlib import Path

from halflight.gm.retrieval import retrieve
from halflight.ingest.runner import run_ingest
from sqlmodel import Session

from .conftest import FakeEmbedder

FIXTURE = Path(__file__).parent / "fixtures" / "vault_mini"


def test_retrieve_returns_chunks(session: Session, fake_embedder: FakeEmbedder) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    results = retrieve("who runs the under-level", fake_embedder, session, k=3)
    assert results
    assert len(results) <= 3
    # ordered by ascending distance
    assert results == sorted(results, key=lambda r: r.distance)


def test_secret_chunks_excluded(session: Session, fake_embedder: FakeEmbedder) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    results = retrieve("maintenance shaft fare gates", fake_embedder, session, k=10)
    # The secret section of loc_tram_hub is never embedded, so it can't surface.
    assert all("maintenance shaft" not in r.body for r in results)
