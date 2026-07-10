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
    loc = state.location.name or state.location.id
    parts: list[str] = [
        f"## Your state\nHP {p.hp} · Scrip {p.credits} · Time {p.time_ticks}",
        f"## Where you are\nThe scene takes place at: {loc}. The narration stays here.",
    ]

    if state.npcs:
        who = ", ".join(
            f"{n.name or n.id} ({'alive' if n.alive else 'dead'})" for n in state.npcs.values()
        )
        present = (
            "## Who is physically present (the ONLY characters in the scene)\n" + who + "\n"
            "No one else is here. Do NOT bring other named characters into the scene."
        )
    else:
        present = (
            "## Who is physically present\nNo one. You are alone here — do not introduce"
            " any named character into the scene."
        )
    parts.append(present)

    if retrieved:
        lore = "\n\n".join(f"- {c.body}" for c in retrieved)
        parts.append(
            "## Background lore you may know (NOT necessarily present or nearby)\n"
            "Use only for what the character knows or recalls. It does not put any person or"
            " place into the current scene. If it doesn't fit, ignore it. If the player asks about"
            " something not covered here, the character does not know.\n\n" + lore
        )
    else:
        parts.append(
            "## Background lore\n(nothing retrieved — the character does not know; say so if asked)"
        )

    parts.append(
        "## What just happened (absolute truth; never contradict)\n" + describe_result(result)
    )
    parts.append(
        "Narrate this turn. Second person, past tense. Keep it TIGHT — 40 to 110 words, one or"
        " two short paragraphs. Err short. Stay at the current location with only the people listed"
        " as present. If the player asks who or what something is, answer briefly from the"
        " background lore (what the character knows); if it isn't there, they don't know."
        " Do not ask questions."
    )
    return "\n\n".join(parts)
