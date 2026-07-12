"""Retrieval: top-k merged lore + event memory.

Lore chunks are ranked by cosine similarity. Event memories (M6, scoped to the
run) get a recency boost — recent significant events surface even against
slightly-more-similar lore — following the handoff formula
`similarity * (1 + 0.1 * ln(1 + recency))`. Unrevealed secrets are excluded.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from sqlmodel import Session, col, or_, select

from halflight.ingest.embedder import Embedder
from halflight.models import EventChunk, LoreChunk

RECENCY_WEIGHT = 0.1


@dataclass
class RetrievedChunk:
    source_note_id: str
    source_type: str  # "location" | "npc" | ... | "lore" | "event"
    body: str
    distance: float
    score: float = 0.0


def _lore_candidates(vec: list[float], session: Session, k: int) -> list[RetrievedChunk]:
    distance = LoreChunk.embedding.cosine_distance(vec)  # type: ignore[union-attr]
    rows = session.exec(
        select(LoreChunk, distance.label("distance"))
        .where(col(LoreChunk.embedding).is_not(None))
        .where(or_(col(LoreChunk.is_secret).is_(False), col(LoreChunk.revealed).is_(True)))
        .order_by(distance)
        .limit(k)
    ).all()
    return [
        RetrievedChunk(c.source_note_id, c.source_type, c.body, float(d), score=1.0 - float(d))
        for c, d in rows
    ]


def _event_candidates(
    vec: list[float], session: Session, run_id: int, k: int
) -> list[RetrievedChunk]:
    distance = EventChunk.embedding.cosine_distance(vec)  # type: ignore[union-attr]
    rows = session.exec(
        select(EventChunk, distance.label("distance"))
        .where(col(EventChunk.run_id) == run_id)
        .where(col(EventChunk.embedding).is_not(None))
        .order_by(distance)
        .limit(k)
    ).all()
    out: list[RetrievedChunk] = []
    for chunk, d in rows:
        similarity = 1.0 - float(d)
        boost = 1.0 + RECENCY_WEIGHT * math.log1p(chunk.turn_no)
        out.append(
            RetrievedChunk(
                source_note_id=f"event:{chunk.event_id}",
                source_type="event",
                body=chunk.description,
                distance=float(d),
                score=similarity * boost,
            )
        )
    return out


def location_lore(session: Session, location_id: str) -> list[str]:
    """The current location's own (non-secret, revealed) description chunks."""
    rows = session.exec(
        select(LoreChunk)
        .where(col(LoreChunk.source_note_id) == location_id)
        .where(or_(col(LoreChunk.is_secret).is_(False), col(LoreChunk.revealed).is_(True)))
        .order_by(col(LoreChunk.chunk_ix))
    ).all()
    return [c.body for c in rows]


def retrieve(
    query: str,
    embedder: Embedder,
    session: Session,
    *,
    k: int = 6,
    run_id: int | None = None,
) -> list[RetrievedChunk]:
    vectors = embedder.embed([query])
    if not vectors:
        return []
    vec = vectors[0]

    candidates = _lore_candidates(vec, session, k)
    if run_id is not None:
        candidates += _event_candidates(vec, session, run_id, k)

    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates[:k]
