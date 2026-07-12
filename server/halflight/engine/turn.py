"""Turn orchestration and run lifecycle. Ties load -> resolve -> apply -> log.

One turn: build the scene, resolve the action to a TurnResult, write state changes,
append an immutable event, and end the run if the player died. No LLM here — the
narrator (M4) consumes the returned TurnResult separately.
"""

from __future__ import annotations

from sqlalchemy import func
from sqlmodel import Session, col, select

from halflight.engine.actions import Action
from halflight.engine.dice import Dice, Roller
from halflight.engine.gamestate import GameState
from halflight.engine.resolver import resolve
from halflight.engine.results import TurnResult
from halflight.engine.state import apply, load_state
from halflight.models import Event, Inventory, Npc, PlayerState, Run
from halflight.models.runtime import NpcState, utcnow


def start_run(
    session: Session,
    *,
    character_name: str,
    start_location: str,
    stats: dict[str, int],
    hp: int,
    archetype: str = "",
    credits: int = 0,
    inventory: dict[str, int] | None = None,
) -> int:
    """Create a run: player state, starting inventory, and npc_state for every NPC."""
    run = Run(character_name=character_name, archetype=archetype, started_at=utcnow())
    session.add(run)
    session.flush()  # populate run.id
    assert run.id is not None
    run_id = run.id

    session.add(
        PlayerState(
            run_id=run_id, hp=hp, hp_max=hp, credits=credits,
            location_id=start_location, stats=stats,
        )
    )
    for item_id, qty in (inventory or {}).items():
        session.add(Inventory(run_id=run_id, item_id=item_id, quantity=qty))

    for npc in session.exec(select(Npc)).all():
        session.add(
            NpcState(
                run_id=run_id,
                npc_id=npc.id,
                hp=npc.hp_max,
                alive=True,
                disposition=npc.disposition_default,
                current_location=npc.home_location_id or start_location,
            )
        )
    session.commit()
    return run_id


def take_turn(
    session: Session, run_id: int, action: Action, dice: Roller | None = None
) -> TurnResult:
    dice = dice or Dice()
    state = load_state(session, run_id)
    result = resolve(state, action, dice)
    apply(session, run_id, result)
    _decay_heat(session, run_id)
    _log_event(session, run_id, state, result)
    _end_run_if_dead(session, run_id, result)
    session.commit()
    return result


def _decay_heat(session: Session, run_id: int) -> None:
    ps = session.get(PlayerState, run_id)
    if ps is not None and ps.heat > 0:
        ps.heat = max(0, ps.heat - 1)
        session.add(ps)


def current_turn_no(session: Session, run_id: int) -> int:
    """Highest logged turn number for a run (0 if none yet)."""
    latest = session.exec(
        select(func.max(col(Event.turn_no))).where(col(Event.run_id) == run_id)
    ).one()
    return latest or 0


def _next_turn_no(session: Session, run_id: int) -> int:
    return current_turn_no(session, run_id) + 1


def _log_event(session: Session, run_id: int, state: GameState, result: TurnResult) -> None:
    session.add(
        Event(
            run_id=run_id,
            turn_no=_next_turn_no(session, run_id),
            action=result.action.model_dump(),
            result=result.model_dump(),
            significance=result.significance,
            location_id=state.location.id,
            witnesses=[nid for nid, n in state.npcs.items() if n.alive],
            ts=utcnow(),
        )
    )


def _end_run_if_dead(session: Session, run_id: int, result: TurnResult) -> None:
    death = next((e for e in result.scene_events if e.kind == "player_died"), None)
    if death is None:
        return
    run = session.get(Run, run_id)
    if run is not None and run.ended_at is None:
        run.ended_at = utcnow()
        by = death.detail.get("by")
        run.cause_of_death = f"killed by {by}" if by else "died"
        session.add(run)
