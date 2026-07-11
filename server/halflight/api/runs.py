"""Run lifecycle + state snapshot endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, SQLModel, col, select

from halflight.api.deps import SessionDep
from halflight.api.schemas import (
    ExitBrief,
    ItemBrief,
    LocationBrief,
    NpcBrief,
    StartRunRequest,
    StateResponse,
)
from halflight.engine.state import load_state
from halflight.engine.turn import start_run
from halflight.models import Item, Location, Npc, Run

router = APIRouter()


@router.get("/locations", response_model=list[LocationBrief])
def list_locations(session: SessionDep) -> list[LocationBrief]:
    rows = session.exec(select(Location).order_by(col(Location.name))).all()
    return [LocationBrief(id=r.id, name=r.name) for r in rows]


def _name(session: Session, model: type[SQLModel], id_: str) -> str:
    name = getattr(session.get(model, id_), "name", None)
    return name if isinstance(name, str) else id_


def snapshot(session: Session, run_id: int) -> StateResponse:
    run = session.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"no run {run_id}")
    state = load_state(session, run_id)

    inventory = []
    for item_id, qty in state.player.inventory.items():
        item = session.get(Item, item_id)
        inventory.append(
            ItemBrief(
                id=item_id,
                name=item.name if item else item_id,
                kind=item.kind if item else "misc",
                quantity=qty,
            )
        )

    return StateResponse(
        run_id=run_id,
        character_name=run.character_name,
        hp=state.player.hp,
        credits=state.player.credits,
        location_id=state.location.id,
        location_name=_name(session, Location, state.location.id),
        time_ticks=state.player.time_ticks,
        ended=run.ended_at is not None,
        cause_of_death=run.cause_of_death,
        stats=state.player.stats,
        exits=[
            ExitBrief(id=e, name=_name(session, Location, e))
            for e in state.location.connections
        ],
        npcs=[
            NpcBrief(
                id=n.id, name=_name(session, Npc, n.id), alive=n.alive, disposition=n.disposition
            )
            for n in state.npcs.values()
        ],
        inventory=inventory,
    )


@router.post("/runs", response_model=StateResponse)
def create_run(req: StartRunRequest, session: SessionDep) -> StateResponse:
    run_id = start_run(
        session,
        character_name=req.character_name,
        start_location=req.start_location,
        stats=req.stats,
        hp=req.hp,
        archetype=req.archetype,
        credits=req.credits,
        inventory=req.inventory,
    )
    return snapshot(session, run_id)


@router.get("/state", response_model=StateResponse)
def get_state(run_id: int, session: SessionDep) -> StateResponse:
    return snapshot(session, run_id)
