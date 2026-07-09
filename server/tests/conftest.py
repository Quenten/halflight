"""Shared DB-test fixtures.

`session` binds to Postgres inside an outer transaction that is rolled back on
teardown (savepoint mode), so tests never commit to the dev database. Tests that
request `session` auto-skip when Postgres isn't reachable.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator

import pytest
from sqlmodel import Session

from halflight.db import engine
from halflight.models.authored import EMBED_DIM


def _db_available() -> bool:
    try:
        with engine.connect():
            return True
    except Exception:
        return False


@pytest.fixture
def session() -> Iterator[Session]:
    if not _db_available():
        pytest.skip("Postgres not reachable")
    conn = engine.connect()
    trans = conn.begin()
    s = Session(bind=conn, join_transaction_mode="create_savepoint")
    try:
        yield s
    finally:
        s.close()
        trans.rollback()
        conn.close()


class FakeEmbedder:
    """Deterministic EMBED_DIM vectors derived from the text — no server needed."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8")).digest()
            out.append([h[i % len(h)] / 255.0 for i in range(EMBED_DIM)])
        return out


@pytest.fixture
def fake_embedder() -> FakeEmbedder:
    return FakeEmbedder()
