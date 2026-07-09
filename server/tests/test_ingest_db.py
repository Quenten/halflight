"""End-to-end ingestion against Postgres, with a fake embedder.

Each test runs inside an outer transaction that is rolled back on teardown
(savepoint mode), so nothing is committed to the dev database. Skipped if
Postgres isn't reachable.
"""

from __future__ import annotations

import hashlib
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from halflight.db import engine
from halflight.ingest.runner import run_ingest
from halflight.models import Faction, LoreChunk, NoteIndex, Npc
from halflight.models.authored import EMBED_DIM
from sqlmodel import Session, select

FIXTURE = Path(__file__).parent / "fixtures" / "vault_mini"


def _db_available() -> bool:
    try:
        with engine.connect():
            return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _db_available(), reason="Postgres not reachable")


class FakeEmbedder:
    """Deterministic EMBED_DIM vectors derived from the text — no server needed."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8")).digest()
            out.append([h[i % len(h)] / 255.0 for i in range(EMBED_DIM)])
        return out


@pytest.fixture
def session() -> Iterator[Session]:
    conn = engine.connect()
    trans = conn.begin()
    s = Session(bind=conn, join_transaction_mode="create_savepoint")
    try:
        yield s
    finally:
        s.close()
        trans.rollback()
        conn.close()


def test_ingest_populates_tables(session: Session) -> None:
    report = run_ingest(FIXTURE, session, FakeEmbedder())
    assert not report.aborted
    assert report.notes_total == 7
    assert report.upserted == 7 and report.skipped == 0

    assert len(session.exec(select(NoteIndex)).all()) == 7
    dax = session.get(Npc, "npc_dax")
    assert dax is not None and dax.faction_id == "fac_syndicate"
    assert session.get(Faction, "fac_syndicate") is not None


def test_secret_chunk_stored_but_not_embedded(session: Session) -> None:
    run_ingest(FIXTURE, session, FakeEmbedder())
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


def test_hash_skip_on_reingest(session: Session) -> None:
    run_ingest(FIXTURE, session, FakeEmbedder())
    second = run_ingest(FIXTURE, session, FakeEmbedder())
    assert second.upserted == 0
    assert second.skipped == 7
    assert second.chunks_written == 0


def test_similarity_search_finds_self(session: Session) -> None:
    run_ingest(FIXTURE, session, FakeEmbedder())
    chunk = session.exec(
        select(LoreChunk).where(LoreChunk.embedding.is_not(None))  # type: ignore[union-attr]
    ).first()
    assert chunk is not None
    nearest = session.exec(
        select(LoreChunk).order_by(LoreChunk.embedding.cosine_distance(chunk.embedding)).limit(1)  # type: ignore[union-attr]
    ).first()
    assert nearest is not None and nearest.id == chunk.id


def test_deletion_of_removed_note(session: Session, tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    shutil.copytree(FIXTURE, vault)
    run_ingest(vault, session, FakeEmbedder())
    (vault / "items" / "itm_shiv.md").unlink()
    report = run_ingest(vault, session, FakeEmbedder())
    assert report.deleted == 1
    from halflight.models import Item

    assert session.get(Item, "itm_shiv") is None
    assert session.get(NoteIndex, "itm_shiv") is None
