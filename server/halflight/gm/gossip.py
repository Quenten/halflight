"""Gossip propagation (M6). What one NPC witnessed spreads to their faction.

On each world-clock tick a rate-limited handful of witnessed memories propagate to
same-faction NPCs as `told`, so word travels the deck organically rather than
everyone knowing everything at once. Deterministic; no LLM.
"""

from __future__ import annotations

from sqlmodel import Session, col, select

from halflight.models import Npc, NpcMemory
from halflight.models.runtime import utcnow

MAX_SPREAD_PER_TICK = 2


def propagate_gossip(
    session: Session, run_id: int, *, max_spread: int = MAX_SPREAD_PER_TICK
) -> int:
    """Spread witnessed memories to same-faction peers as `told`. Returns tellings made."""
    witnessed = session.exec(
        select(NpcMemory).where(
            col(NpcMemory.run_id) == run_id, col(NpcMemory.how_known) == "witnessed"
        )
    ).all()

    spread = 0
    for mem in witnessed:
        if spread >= max_spread:
            break
        witness = session.get(Npc, mem.npc_id)
        if witness is None or witness.faction_id is None:
            continue
        peers = session.exec(
            select(Npc).where(
                col(Npc.faction_id) == witness.faction_id, col(Npc.id) != witness.id
            )
        ).all()
        for peer in peers:
            if spread >= max_spread:
                break
            if session.get(NpcMemory, (run_id, peer.id, mem.event_id)) is not None:
                continue  # already knows
            session.add(
                NpcMemory(
                    run_id=run_id, npc_id=peer.id, event_id=mem.event_id,
                    how_known="told", ts=utcnow(),
                )
            )
            spread += 1

    if spread:
        session.commit()
    return spread
