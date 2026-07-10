"""Lore retrieval: top-k cosine search over embedded chunks.

Excludes unrevealed secrets (they carry no embedding until an engine event reveals
them, and the filter is explicit for when they do). Event chunks and recency
boosting arrive in M6; this is the lore-only baseline the narrator draws on.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlmodel import Session, col, or_, select

from halflight.ingest.embedder import Embedder
from halflight.models import LoreChunk


@dataclass
class RetrievedChunk:
    source_note_id: str
    source_type: str
    body: str
    distance: float


def retrieve(
    query: str, embedder: Embedder, session: Session, *, k: int = 6
) -> list[RetrievedChunk]:
    vectors = embedder.embed([query])
    if not vectors:
        return []
    vec = vectors[0]
    distance = LoreChunk.embedding.cosine_distance(vec)  # type: ignore[union-attr]
    rows = session.exec(
        select(LoreChunk, distance.label("distance"))
        .where(col(LoreChunk.embedding).is_not(None))
        .where(or_(col(LoreChunk.is_secret).is_(False), col(LoreChunk.revealed).is_(True)))
        .order_by(distance)
        .limit(k)
    ).all()
    return [
        RetrievedChunk(
            source_note_id=chunk.source_note_id,
            source_type=chunk.source_type,
            body=chunk.body,
            distance=float(dist),
        )
        for chunk, dist in rows
    ]
