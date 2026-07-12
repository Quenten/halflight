"""Event memory (M6). Significant TurnResults become embedded one-line facts.

The engine flags significance (0-3); events at >= 2 (deaths, major hits) get a
terse factual description embedded into event_chunks so they resurface in later
retrieval — the world remembering what happened. Descriptions are built
deterministically from the TurnResult; no LLM.
"""

from __future__ import annotations

from sqlmodel import Session, col, select

from halflight.engine.results import TurnResult
from halflight.ingest.embedder import Embedder
from halflight.models import Event, EventChunk, Npc
from halflight.models.runtime import utcnow

SIGNIFICANCE_THRESHOLD = 2


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
    session.commit()
    return description
