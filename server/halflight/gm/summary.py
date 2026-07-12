"""Rolling episodic summary (M6).

Every SUMMARY_INTERVAL turns the older turns (beyond the last KEEP_VERBATIM) are
compressed by the LLM into a structured summary — facts_established, promises_made,
open_threads — so long sessions stay coherent without an unbounded transcript. The
latest summary feeds the narrator's context as "the story so far".
"""

from __future__ import annotations

import json
from typing import Any

from sqlmodel import Session, col, desc, select

from halflight.gm.client import LLMClient
from halflight.gm.narrator import strip_thinking
from halflight.models import Event, Summary
from halflight.models.runtime import utcnow

SUMMARY_INTERVAL = 20
KEEP_VERBATIM = 6
_KEYS = ("facts_established", "promises_made", "open_threads")

_SYSTEM = (
    "You compress a text-RPG transcript into a compact JSON memory. Output ONLY a JSON"
    ' object with three string arrays: {"facts_established": [], "promises_made": [],'
    ' "open_threads": []}. Facts are things now true in the world; promises are'
    " commitments made to or by the player; open threads are unresolved situations."
    " Keep each entry to one short clause. No prose outside the JSON."
)


def latest_summary(session: Session, run_id: int) -> dict[str, Any] | None:
    row = session.exec(
        select(Summary).where(col(Summary.run_id) == run_id).order_by(desc(col(Summary.up_to_turn)))
    ).first()
    return row.body if row is not None else None


def format_summary(body: dict[str, Any] | None) -> str | None:
    if not body:
        return None
    parts = []
    for key in _KEYS:
        items = body.get(key) or []
        if items:
            label = key.replace("_", " ").title()
            parts.append(f"{label}: " + "; ".join(str(i) for i in items))
    return "\n".join(parts) or None


def _last_up_to(session: Session, run_id: int) -> int:
    row = session.exec(
        select(Summary).where(col(Summary.run_id) == run_id).order_by(desc(col(Summary.up_to_turn)))
    ).first()
    return row.up_to_turn if row is not None else 0


def _transcript(events: list[Event]) -> str:
    lines = []
    for e in events:
        action = e.action.get("kind", "?") if isinstance(e.action, dict) else "?"
        result = e.result if isinstance(e.result, dict) else {}
        outcome = result.get("outcome", "?")
        kinds = [ev.get("kind") for ev in result.get("scene_events", [])]
        lines.append(f"turn {e.turn_no}: {action} -> {outcome} {kinds}")
    return "\n".join(lines)


def _compress(chat: LLMClient, prior: dict[str, Any] | None, transcript: str) -> dict[str, Any]:
    prior_text = json.dumps(prior) if prior else "{}"
    user = (
        f"Prior memory (extend, don't lose it):\n{prior_text}\n\n"
        f"New turns to fold in:\n{transcript}\n\nJSON memory:"
    )
    raw = strip_thinking(
        "".join(chat.chat_stream(
            [{"role": "system", "content": _SYSTEM}, {"role": "user", "content": user}],
            temperature=0.2, max_tokens=400,
        ))
    )
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return prior or {k: [] for k in _KEYS}
    return {k: [str(x) for x in (data.get(k) or [])] for k in _KEYS}


def maybe_summarize(session: Session, chat: LLMClient, run_id: int, current_turn: int) -> bool:
    """Summarize older turns if enough have accrued. Returns True if a summary was written."""
    last = _last_up_to(session, run_id)
    up_to = current_turn - KEEP_VERBATIM
    if up_to <= last or current_turn - last < SUMMARY_INTERVAL:
        return False
    events = session.exec(
        select(Event)
        .where(col(Event.run_id) == run_id, col(Event.turn_no) > last, col(Event.turn_no) <= up_to)
        .order_by(col(Event.turn_no))
    ).all()
    if not events:
        return False
    body = _compress(chat, latest_summary(session, run_id), _transcript(list(events)))
    session.add(Summary(run_id=run_id, up_to_turn=up_to, body=body, ts=utcnow()))
    session.commit()
    return True
