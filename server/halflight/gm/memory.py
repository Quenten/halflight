"""Event memory (M6). Significant TurnResults become embedded one-line facts.

The engine flags significance (0-3); events at >= 2 (deaths, major hits) get a
terse factual description embedded into event_chunks so they resurface in later
retrieval — the world remembering what happened. Descriptions are built
deterministically from the TurnResult; no LLM.
"""

from __future__ import annotations

from collections.abc import Iterable

from sqlmodel import Session, col, select

from halflight.engine.results import TurnResult
from halflight.ingest.embedder import Embedder
from halflight.models import Event, EventChunk, Npc, NpcMemory
from halflight.models.runtime import utcnow

SIGNIFICANCE_THRESHOLD = 2
MEMORIES_PER_NPC = 3


def _npc_name(session: Session, npc_id: str | None) -> str:
    if not npc_id:
        return "someone"
    row = session.get(Npc, npc_id)
    return row.name if row is not None else npc_id


def describe_event(
    session: Session, result: TurnResult, *, actor: str, location: str, turn_no: int
) -> str:
    detail = {e.kind: e.detail for e in result.scene_events}
    if "player_died" in detail:
        by = _npc_name(session, detail["player_died"].get("by"))
        return f"{actor} was killed by {by} at {location} (turn {turn_no})."
    if "npc_died" in detail:
        npc = _npc_name(session, detail["npc_died"].get("npc"))
        return f"{actor} killed {npc} at {location} (turn {turn_no})."
    if "attack_hit" in detail:
        npc = _npc_name(session, detail["attack_hit"].get("npc"))
        return f"{actor} wounded {npc} at {location} (turn {turn_no})."
    return f"{actor} did something notable ({result.action.kind}) at {location} (turn {turn_no})."


def record_event_memory(
    session: Session,
    embedder: Embedder,
    *,
    run_id: int,
    turn_no: int,
    result: TurnResult,
    actor: str,
    location: str,
) -> str | None:
    """Embed and store a memory for a significant turn. Returns the description or None."""
    if result.significance < SIGNIFICANCE_THRESHOLD:
        return None
    event = session.exec(
        select(Event).where(col(Event.run_id) == run_id, col(Event.turn_no) == turn_no)
    ).first()
    if event is None or event.id is None:
        return None
    description = describe_event(session, result, actor=actor, location=location, turn_no=turn_no)
    vectors = embedder.embed([description])
    session.add(
        EventChunk(
            event_id=event.id,
            run_id=run_id,
            turn_no=turn_no,
            description=description,
            embedding=vectors[0] if vectors else None,
            ts=utcnow(),
        )
    )

    # Every alive NPC who was in the scene witnesses it (the victim, being dead, does not).
    victims = {e.detail.get("npc") for e in result.scene_events if e.kind == "npc_died"}
    now = utcnow()
    for npc_id in event.witnesses:
        if npc_id in victims:
            continue
        session.add(
            NpcMemory(
                run_id=run_id, npc_id=npc_id, event_id=event.id, how_known="witnessed", ts=now
            )
        )

    session.commit()
    return description


def scene_npc_memories(
    session: Session, run_id: int, npc_ids: Iterable[str]
) -> dict[str, list[str]]:
    """Return, per present NPC, the event descriptions they know (most recent first)."""
    ids = list(npc_ids)
    if not ids:
        return {}
    rows = session.exec(
        select(NpcMemory, EventChunk.description)
        .join(EventChunk, col(EventChunk.event_id) == col(NpcMemory.event_id))
        .where(col(NpcMemory.run_id) == run_id, col(NpcMemory.npc_id).in_(ids))
        .order_by(col(NpcMemory.event_id).desc())
    ).all()
    out: dict[str, list[str]] = {}
    for mem, description in rows:
        bucket = out.setdefault(mem.npc_id, [])
        if len(bucket) < MEMORIES_PER_NPC:
            bucket.append(description)
    return out
