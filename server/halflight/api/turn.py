"""POST /turn — resolve a turn and stream the narration over SSE.

All DB work (parse, engine resolve, retrieve, snapshot) happens before streaming
starts, so the request's session isn't used once the streaming body begins. The
narration streams token-by-token; a post-stream fact-check appends a correction on
the rare occasion the prose contradicts the engine.

SSE events (data is JSON): `token` {text}, `correction` {text}, `state` {snapshot},
`done` {}.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from halflight.api.deps import ChatDep, EmbedderDep, SessionDep
from halflight.api.runs import snapshot
from halflight.api.schemas import TurnRequest
from halflight.config import get_settings
from halflight.engine.state import load_state
from halflight.engine.turn import current_turn_no, take_turn
from halflight.gm.context import build_context
from halflight.gm.memory import record_event_memory, scene_npc_memories
from halflight.gm.narrator import check_consistency, factual_fallback, strip_thinking, system_prompt
from halflight.gm.parser import build_prompt, parse_intent
from halflight.gm.prompts import parser_prompt
from halflight.gm.retrieval import retrieve
from halflight.gm.turnlog import log_turn
from halflight.models import Run

router = APIRouter()


def _sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/turn")
def turn(
    req: TurnRequest, session: SessionDep, chat: ChatDep, embedder: EmbedderDep
) -> StreamingResponse:
    settings = get_settings()
    vault = settings.vault_path

    run = session.get(Run, req.run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"no run {req.run_id}")
    if run.ended_at is not None:
        raise HTTPException(status_code=409, detail="run has ended")

    # --- everything that needs the DB, done before streaming ---
    state = load_state(session, req.run_id)
    parse_system = parser_prompt(vault)
    try:
        action = parse_intent(req.text, state, chat, system=parse_system)
        result = take_turn(session, req.run_id, action, None)
        # Retrieval + NPC memories reflect the state before this turn's event is recorded.
        retrieved = retrieve(req.text, embedder, session, k=6, run_id=req.run_id)
        npc_mems = scene_npc_memories(session, req.run_id, [n.id for n in state.npcs.values()])
        context = build_context(state, result, retrieved, req.text, npc_mems)
        record_event_memory(
            session, embedder, run_id=req.run_id, turn_no=current_turn_no(session, req.run_id),
            result=result, actor=run.character_name,
            location=state.location.name or state.location.id,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail="model server unreachable — is llama-server running? (see README)",
        ) from exc
    narrate_system = system_prompt(vault)
    parse_prompt_text = build_prompt(parse_system, state, req.text)
    snap = snapshot(session, req.run_id).model_dump()
    turn_no = current_turn_no(session, req.run_id)

    def gen() -> Iterator[str]:
        messages = [
            {"role": "system", "content": narrate_system},
            {"role": "user", "content": context},
        ]
        acc: list[str] = []
        for token in chat.chat_stream(messages, temperature=0.8, max_tokens=200):
            acc.append(token)
            yield _sse("token", {"text": token})

        narration = strip_thinking("".join(acc))
        if check_consistency(narration, result):
            correction = factual_fallback(result)
            narration = f"{narration}\n\n{correction}"
            yield _sse("correction", {"text": correction})

        log_turn(
            settings.logs_dir, req.run_id, turn_no,
            player_text=req.text, parse_prompt=parse_prompt_text,
            parse_output=action.model_dump_json(), narration_context=context,
            narration=narration, action=action.model_dump(), result=result.model_dump(),
        )
        yield _sse("state", snap)
        yield _sse("done", {})

    return StreamingResponse(gen(), media_type="text/event-stream")
