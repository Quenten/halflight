"""Assemble the narrator's user-message: hard state + retrieved lore + TurnResult.

The TurnResult section is authoritative and must not be contradicted. Retrieved
lore is the ONLY source of world facts — if it's empty, the character knows
nothing more (a hard narrator rule). Episodic summary and recent-turn history
arrive in M6; this is the M4 bundle.
"""

from __future__ import annotations

from halflight.engine.gamestate import GameState
from halflight.engine.results import TurnResult
from halflight.gm.retrieval import RetrievedChunk


def describe_result(result: TurnResult) -> str:
    lines = [f"action: {result.action.kind}", f"outcome: {result.outcome}"]
    if result.roll is not None:
        lines.append(f"roll: {result.roll} vs difficulty {result.difficulty}")
    if result.reason:
        lines.append(f"reason: {result.reason}")
    for event in result.scene_events:
        lines.append(f"event: {event.kind} {event.detail}")
    for change in result.state_changes:
        lines.append(f"change: {change.entity}.{change.field} = {change.delta}")
    return "\n".join(lines)


def build_context(
    state: GameState, result: TurnResult, retrieved: list[RetrievedChunk]
) -> str:
    p = state.player
    parts: list[str] = [
        f"## Your state\nHP {p.hp} · Scrip {p.credits} · Location {state.location.id}",
    ]

    if state.npcs:
        who = ", ".join(
            f"{n.id} (hp {n.hp}, {'alive' if n.alive else 'dead'})" for n in state.npcs.values()
        )
        parts.append(f"## People here\n{who}")

    if retrieved:
        lore = "\n\n".join(f"- {c.body}" for c in retrieved)
        parts.append(
            "## Relevant lore (the ONLY source of world facts; do not invent beyond it)\n" + lore
        )
    else:
        parts.append(
            "## Relevant lore\n(nothing retrieved — the character does not know; say so if asked)"
        )

    parts.append(
        "## What just happened (absolute truth; never contradict)\n" + describe_result(result)
    )
    parts.append(
        "Narrate this turn. Second person, past tense, 100-250 words. Do not ask questions."
    )
    return "\n\n".join(parts)
