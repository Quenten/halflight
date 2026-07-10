"""End-to-end ingestion against Postgres, with a fake embedder.

Runs inside the rolled-back `session` fixture (see conftest), so nothing is
committed to the dev database. Skipped if Postgres isn't reachable.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from halflight.ingest.runner import run_ingest
from halflight.models import Faction, Item, LoreChunk, NoteIndex, Npc
from sqlmodel import Session, select

from .conftest import FakeEmbedder

FIXTURE = Path(__file__).parent / "fixtures" / "vault_mini"


def test_ingest_populates_tables(session: Session, fake_embedder: FakeEmbedder) -> None:
    report = run_ingest(FIXTURE, session, fake_embedder)
    assert not report.aborted
    assert report.notes_total == 7
    assert report.upserted == 7 and report.skipped == 0

    assert len(session.exec(select(NoteIndex)).all()) == 7
    dax = session.get(Npc, "npc_dax")
    assert dax is not None and dax.faction_id == "fac_syndicate"
    assert session.get(Faction, "fac_syndicate") is not None


def test_secret_chunk_stored_but_not_embedded(
    session: Session, fake_embedder: FakeEmbedder
) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    secret = session.exec(
        select(LoreChunk).where(LoreChunk.source_note_id == "loc_tram_hub", LoreChunk.is_secret)
    ).all()
    assert secret and all(c.embedding is None for c in secret)
    public = session.exec(
        select(LoreChunk).where(
            LoreChunk.source_note_id == "loc_tram_hub", LoreChunk.is_secret == False  # noqa: E712
        )
    ).all()
    assert public and all(c.embedding is not None for c in public)


def test_hash_skip_on_reingest(session: Session, fake_embedder: FakeEmbedder) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    second = run_ingest(FIXTURE, session, fake_embedder)
    assert second.upserted == 0
    assert second.skipped == 7
    assert second.chunks_written == 0


def test_similarity_search_finds_self(session: Session, fake_embedder: FakeEmbedder) -> None:
    run_ingest(FIXTURE, session, fake_embedder)
    chunk = session.exec(
        select(LoreChunk).where(LoreChunk.embedding.is_not(None))  # type: ignore[union-attr]
    ).first()
    assert chunk is not None
    nearest = session.exec(
        select(LoreChunk).order_by(LoreChunk.embedding.cosine_distance(chunk.embedding)).limit(1)  # type: ignore[union-attr]
    ).first()
    assert nearest is not None and nearest.id == chunk.id


def test_deletion_of_removed_note(
    session: Session, fake_embedder: FakeEmbedder, tmp_path: Path
) -> None:
    vault = tmp_path / "vault"
    shutil.copytree(FIXTURE, vault)
    run_ingest(vault, session, fake_embedder)
    (vault / "items" / "itm_shiv.md").unlink()
    report = run_ingest(vault, session, fake_embedder)
    assert report.deleted == 1
    assert session.get(Item, "itm_shiv") is None
    assert session.get(NoteIndex, "itm_shiv") is None
