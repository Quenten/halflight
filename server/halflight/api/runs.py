"""Run lifecycle + state snapshot endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, SQLModel, col, select

from halflight.api.deps import SessionDep
from halflight.api.schemas import (
    BuildStepOut,
    ChargenData,
    ChargenRequest,
    ChargenResult,
    ClassOut,
    ExitBrief,
    FactionStanding,
    HistoryResponse,
    ItemBrief,
    KnownNpc,
    LocationBrief,
    NpcBrief,
    OptionOut,
    StartRunRequest,
    StateResponse,
    StepOut,
    TurnRecord,
)
from halflight.engine.clock import shift_for
from halflight.engine.dice import Dice
from halflight.engine.gamestate import effective_disposition
from halflight.engine.lifepath import CLASSES, STEPS, resolve_build
from halflight.engine.state import load_state
from halflight.engine.turn import start_run
from halflight.models import Faction, Item, Location, Narration, Npc, NpcState, Run

router = APIRouter()


@router.get("/locations", response_model=list[LocationBrief])
def list_locations(session: SessionDep) -> list[LocationBrief]:
    rows = session.exec(select(Location).order_by(col(Location.name))).all()
    return [LocationBrief(id=r.id, name=r.name) for r in rows]


@router.get("/chargen", response_model=ChargenData)
def chargen_data(session: SessionDep) -> ChargenData:
    classes = [
        ClassOut(
            id=c.id, name=c.name, hp=c.hp, credits=c.credits,
            items=[_name(session, Item, i) for i in c.items], blurb=c.blurb,
        )
        for c in CLASSES
    ]
    steps = [
        StepOut(
            id=s.id, title=s.title, prompt=s.prompt, rolls=s.rolls,
            options=[
                OptionOut(id=o.id, name=o.name, blurb=o.blurb, hint=o.hint) for o in s.options
            ],
        )
        for s in STEPS
    ]
    return ChargenData(classes=classes, steps=steps)


@router.post("/runs/chargen", response_model=ChargenResult)
def create_run_chargen(req: ChargenRequest, session: SessionDep) -> ChargenResult:
    try:
        build = resolve_build(req.class_id, req.choices, Dice())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    origin = " ".join(b.text.strip() for b in build.backstory if b.text.strip())
    run_id = start_run(
        session,
        character_name=req.character_name,
        start_location=build.start_location,
        stats=build.stats,
        hp=build.hp,
        archetype=req.class_id,
        credits=build.credits,
        inventory=build.inventory,
        origin=origin,
        contacts=build.contacts,
    )
    backstory = [
        BuildStepOut(
            step_title=b.step_title, option_name=b.option_name,
            outcome_kind=b.outcome_kind, text=b.text, summary=b.summary,
            contact=f"{b.contact.name} ({b.contact.relationship})" if b.contact else None,
        )
        for b in build.backstory
    ]
    return ChargenResult(state=snapshot(session, run_id), backstory=backstory)


def _name(session: Session, model: type[SQLModel], id_: str) -> str:
    name = getattr(session.get(model, id_), "name", None)
    return name if isinstance(name, str) else id_


def _mood_label(disp: int) -> str:
    if disp <= -10:
        return "hostile"
    if disp < 0:
        return "wary"
    if disp >= 15:
        return "ally"
    if disp >= 5:
        return "friendly"
    return "neutral"


def _known_npcs(session: Session, run_id: int, faction_rep: dict[str, int]) -> list[KnownNpc]:
    rows = session.exec(
        select(NpcState).where(
            col(NpcState.run_id) == run_id, col(NpcState.known).is_(True)
        )
    ).all()
    out: list[KnownNpc] = []
    for ns in rows:
        authored = session.get(Npc, ns.npc_id)
        faction_id = authored.faction_id if authored else None
        disp = ns.disposition + (faction_rep.get(faction_id, 0) if faction_id else 0)
        out.append(
            KnownNpc(
                id=ns.npc_id,
                name=ns.name or (authored.name if authored else ns.npc_id),
                relationship=ns.relationship or _mood_label(disp),
                disposition=disp,
                last_seen=_name(session, Location, ns.current_location)
                if ns.current_location else "Unknown",
                note=ns.note,
                alive=ns.alive,
            )
        )
    out.sort(key=lambda k: (not k.alive, k.name))
    return out


def snapshot(session: Session, run_id: int) -> StateResponse:
    run = session.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"no run {run_id}")
    state = load_state(session, run_id)
    shift = shift_for(state.player.time_ticks)

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
        origin=run.origin,
        hp=state.player.hp,
        hp_max=state.player.hp_max,
        credits=state.player.credits,
        location_id=state.location.id,
        location_name=_name(session, Location, state.location.id),
        time_ticks=state.player.time_ticks,
        shift=shift.name,
        curfew=shift.curfew,
        heat=state.player.heat,
        ended=run.ended_at is not None,
        cause_of_death=run.cause_of_death,
        stats=state.player.stats,
        exits=[
            ExitBrief(id=e, name=_name(session, Location, e))
            for e in state.location.connections
        ],
        npcs=[
            NpcBrief(
                id=n.id, name=n.name or _name(session, Npc, n.id), alive=n.alive,
                disposition=effective_disposition(n, state.faction_rep),
            )
            for n in state.npcs.values()
        ],
        inventory=inventory,
        standing=[
            FactionStanding(id=fid, name=_name(session, Faction, fid), rep=rep)
            for fid, rep in sorted(state.faction_rep.items())
            if rep != 0
        ],
        known_npcs=_known_npcs(session, run_id, state.faction_rep),
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


@router.get("/history", response_model=HistoryResponse)
def get_history(run_id: int, session: SessionDep, limit: int = 20) -> HistoryResponse:
    """The last `limit` turns of prose, oldest first, so a resumed run replays its log."""
    rows = session.exec(
        select(Narration)
        .where(col(Narration.run_id) == run_id)
        .order_by(col(Narration.turn_no).desc())
        .limit(limit)
    ).all()
    turns = [
        TurnRecord(turn_no=r.turn_no, player_text=r.player_text, narration=r.body)
        for r in reversed(rows)
    ]
    return HistoryResponse(run_id=run_id, turns=turns)
