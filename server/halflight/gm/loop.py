"""Full GM turn: parse free text -> engine resolves -> retrieve lore -> narrate -> log.

This is the orchestration the API calls. The engine remains the source of truth;
the LLM only parses intent and narrates the engine's verdict. Every turn is logged
to disk. Buffered (non-streaming) variant; M5 adds SSE streaming on top.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlmodel import Session

from halflight.engine.actions import Action
from halflight.engine.dice import Roller
from halflight.engine.results import TurnResult
from halflight.engine.state import load_state
from halflight.engine.turn import current_turn_no, take_turn
from halflight.gm.client import LLMClient
from halflight.gm.context import build_context
from halflight.gm.memory import record_event_memory
from halflight.gm.narrator import narrate, system_prompt
from halflight.gm.parser import build_prompt, parse_intent
from halflight.gm.prompts import parser_prompt
from halflight.gm.retrieval import retrieve
from halflight.gm.turnlog import log_turn
from halflight.ingest.embedder import Embedder
from halflight.models import Run


@dataclass
class PlayedTurn:
    action: Action
    result: TurnResult
    narration: str
    turn_no: int


def play_turn(
    session: Session,
    run_id: int,
    text: str,
    *,
    chat: LLMClient,
    embedder: Embedder,
    vault_path: str,
    logs_dir: str | Path = "logs",
    dice: Roller | None = None,
) -> PlayedTurn:
    # Scene as it stands before the action (used for parsing and narration context).
    state = load_state(session, run_id)

    parse_system = parser_prompt(vault_path)
    action = parse_intent(text, state, chat, system=parse_system)

    # Engine resolves, applies, logs the event, and commits.
    result = take_turn(session, run_id, action, dice)

    # Retrieval (prior events + lore) happens before we record this turn's memory.
    retrieved = retrieve(text, embedder, session, k=6, run_id=run_id)
    context = build_context(state, result, retrieved, text)
    narration = narrate(chat, system=system_prompt(vault_path), context=context, result=result)

    turn_no = current_turn_no(session, run_id)
    log_turn(
        logs_dir,
        run_id,
        turn_no,
        player_text=text,
        parse_prompt=build_prompt(parse_system, state, text),
        parse_output=action.model_dump_json(),
        narration_context=context,
        narration=narration,
        action=action.model_dump(),
        result=result.model_dump(),
    )

    run = session.get(Run, run_id)
    record_event_memory(
        session, embedder, run_id=run_id, turn_no=turn_no, result=result,
        actor=run.character_name if run else "The runner",
        location=state.location.name or state.location.id,
    )
    return PlayedTurn(action=action, result=result, narration=narration, turn_no=turn_no)
