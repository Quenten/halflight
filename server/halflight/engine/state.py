"""State layer: build a GameState from the DB and write a TurnResult back.

This is the only engine module that touches the DB. The resolver stays pure; this
translates between persistent rows and the in-memory snapshot, and applies the
resolver's state_changes. Delta convention: location_id and alive are absolute
values; everything else (hp, credits, disposition, time_ticks, inventory:*) is an
additive delta.
"""

from __future__ import annotations

from sqlmodel import Session, col, select

from halflight.engine.gamestate import (
    GameState,
    ItemView,
    LocationView,
    NpcView,
    PlayerView,
)
from halflight.engine.results import StateChange, TurnResult
from halflight.models import Inventory, Item, Location, Npc, NpcState, PlayerState


def load_state(session: Session, run_id: int) -> GameState:
    ps = session.get(PlayerState, run_id)
    if ps is None:
        raise ValueError(f"no player_state for run {run_id}")

    inv = {
        r.item_id: r.quantity
        for r in session.exec(select(Inventory).where(col(Inventory.run_id) == run_id)).all()
    }

    loc = session.get(Location, ps.location_id)
    location = LocationView(
        id=ps.location_id,
        name=loc.name if loc else ps.location_id,
        connections=list(loc.connections) if loc else [],
        danger=loc.danger if loc else 0,
    )

    scene_npcs = session.exec(
        select(NpcState).where(
            col(NpcState.run_id) == run_id,
            col(NpcState.current_location) == ps.location_id,
        )
    ).all()
    npcs: dict[str, NpcView] = {}
    for ns in scene_npcs:
        authored = session.get(Npc, ns.npc_id)
        npcs[ns.npc_id] = NpcView(
            id=ns.npc_id,
            name=authored.name if authored else ns.npc_id,
            hp=ns.hp,
            stats=dict(authored.stats) if authored else {},
            location_id=ns.current_location,
            alive=ns.alive,
            disposition=ns.disposition,
            faction_id=authored.faction_id if authored else None,
        )

    items = {
        it.id: ItemView(id=it.id, kind=it.kind, value=it.value, effects=dict(it.effects))
        for it in session.exec(select(Item)).all()
    }

    player = PlayerView(
        hp=ps.hp,
        location_id=ps.location_id,
        stats=dict(ps.stats),
        inventory=inv,
        credits=ps.credits,
        time_ticks=ps.time_ticks,
    )
    return GameState(player=player, location=location, npcs=npcs, items=items)


def apply(session: Session, run_id: int, result: TurnResult) -> None:
    for change in result.state_changes:
        if change.entity == "player":
            _apply_player(session, run_id, change)
        else:
            _apply_npc(session, run_id, change)


def _apply_player(session: Session, run_id: int, change: StateChange) -> None:
    ps = session.get(PlayerState, run_id)
    if ps is None:
        return
    field = change.field
    if field == "location_id":
        ps.location_id = str(change.delta)
    elif field == "hp":
        ps.hp += int(change.delta)
    elif field == "credits":
        ps.credits += int(change.delta)
    elif field == "time_ticks":
        ps.time_ticks += int(change.delta)
    elif field.startswith("inventory:"):
        _adjust_inventory(session, run_id, field.split(":", 1)[1], int(change.delta))
        return
    session.add(ps)


def _adjust_inventory(session: Session, run_id: int, item_id: str, delta: int) -> None:
    row = session.get(Inventory, (run_id, item_id))
    if row is None:
        if delta > 0:
            session.add(Inventory(run_id=run_id, item_id=item_id, quantity=delta))
        return
    row.quantity += delta
    if row.quantity <= 0:
        session.delete(row)
    else:
        session.add(row)


def _apply_npc(session: Session, run_id: int, change: StateChange) -> None:
    ns = session.get(NpcState, (run_id, change.entity))
    if ns is None:
        return
    if change.field == "hp":
        ns.hp += int(change.delta)
    elif change.field == "alive":
        ns.alive = bool(change.delta)
    elif change.field == "disposition":
        ns.disposition += int(change.delta)
    session.add(ns)
