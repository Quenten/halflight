"""Secret reveal (M6). A `## Secret` section stays out of retrieval (no embedding)
until an engine event uncovers it — a successful investigate. Revealing embeds the
chunk and flips its flag, so it starts surfacing in narration.

Note: `revealed` lives on lore_chunks (authored, shared) — reveals are global for
now, which is fine for single-player. A per-run reveal table is a marketplace-era
refinement.
"""

from __future__ import annotations

from sqlmodel import Session, col, select

from halflight.engine.actions import Action, Investigate
from halflight.engine.gamestate import GameState
from halflight.engine.results import TurnResult
from halflight.ingest.embedder import Embedder
from halflight.models import LoreChunk


def maybe_reveal_on_investigate(
    session: Session, embedder: Embedder, action: Action, result: TurnResult, state: GameState
) -> int:
    """On a successful investigate (wits roll met), uncover the target's secrets."""
    if not isinstance(action, Investigate):
        return 0
    if result.roll is None or result.difficulty is None or result.roll < result.difficulty:
        return 0
    target = action.target or state.location.id
    return reveal_secrets(session, embedder, target)


def reveal_secrets(session: Session, embedder: Embedder, note_id: str) -> int:
    """Embed and reveal any still-hidden secret chunks of a note. Returns the count."""
    chunks = session.exec(
        select(LoreChunk).where(
            col(LoreChunk.source_note_id) == note_id,
            col(LoreChunk.is_secret).is_(True),
            col(LoreChunk.revealed).is_(False),
        )
    ).all()
    if not chunks:
        return 0
    vectors = embedder.embed([c.body for c in chunks])
    for chunk, vec in zip(chunks, vectors, strict=True):
        chunk.revealed = True
        chunk.embedding = vec
        session.add(chunk)
    session.commit()
    return len(chunks)
