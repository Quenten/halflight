"""Run lifecycle + state snapshot endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlmodel import Session

from halflight.api.deps import SessionDep
from halflight.api.schemas import NpcBrief, StartRunRequest, StateResponse
from halflight.engine.state import load_state
from halflight.engine.turn import start_run
from halflight.models import Run

router = APIRouter()


def snapshot(session: Session, run_id: int) -> StateResponse:
    run = session.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"no run {run_id}")
    state = load_state(session, run_id)
    return StateResponse(
        run_id=run_id,
        character_name=run.character_name,
        hp=state.player.hp,
        credits=state.player.credits,
        location_id=state.location.id,
        time_ticks=state.player.time_ticks,
        ended=run.ended_at is not None,
        cause_of_death=run.cause_of_death,
        exits=state.location.connections,
        npcs=[
            NpcBrief(id=n.id, alive=n.alive, disposition=n.disposition)
            for n in state.npcs.values()
        ],
        inventory=state.player.inventory,
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
