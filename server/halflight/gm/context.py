"""Assemble the narrator's user-message: hard state + retrieved lore + TurnResult.

The TurnResult section is authoritative and must not be contradicted. Retrieved
lore is the ONLY source of world facts — if it's empty, the character knows
nothing more (a hard narrator rule). Episodic summary and recent-turn history
arrive in M6; this is the M4 bundle.
"""

from __future__ import annotations

from halflight.engine.gamestate import GameState, NpcView, effective_disposition
from halflight.engine.results import TurnResult
from halflight.gm.retrieval import RetrievedChunk


def _attitude(disposition: int) -> str:
    if disposition <= -10:
        return "hostile"
    if disposition < 0:
        return "wary"
    if disposition >= 10:
        return "warm"
    return "neutral"


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
    state: GameState,
    result: TurnResult,
    retrieved: list[RetrievedChunk],
    player_text: str,
    npc_memories: dict[str, list[str]] | None = None,
    story_so_far: str | None = None,
) -> str:
    p = state.player
    loc = state.location.name or state.location.id
    parts: list[str] = [
        f"## Your state\nHP {p.hp} · Scrip {p.credits} · Time {p.time_ticks}",
        f"## Where you are\nThe scene takes place at: {loc}. The narration stays here.",
    ]
    if story_so_far:
        parts.append("## The story so far (established; stay consistent with it)\n" + story_so_far)

    def _describe_npc(n: NpcView) -> str:
        if not n.alive:
            return f"{n.name or n.id} (dead)"
        mood = _attitude(effective_disposition(n, state.faction_rep))
        return f"{n.name or n.id} ({mood} toward you)"

    if state.npcs:
        who = ", ".join(_describe_npc(n) for n in state.npcs.values())
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

    if npc_memories:
        lines = [
            f"- {n.name or n.id} remembers: " + " ".join(npc_memories[n.id])
            for n in state.npcs.values()
            if npc_memories.get(n.id)
        ]
        if lines:
            parts.append(
                "## What the people here remember about you (react in character to this)\n"
                + "\n".join(lines)
            )

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
        f'## What the player just did (their exact words)\n"{player_text}"\n'
        "Narrate THIS specifically — engage with what they actually said or did, do not give a"
        " generic scene description. If they asked a question, ANSWER it: have a present character"
        " reply in their own voice, or the character recalls it from the background lore above"
        " (if it isn't known, say plainly that they don't know). If they attempted an action,"
        " describe that attempt and how it went."
    )
    parts.append(
        "## Mechanical outcome (absolute truth; never contradict)\n" + describe_result(result)
    )
    parts.append(
        "Write the narration now. Second person, past tense, 40-110 words, err short. Respond"
        " directly to the player's words above. Stay at the current location with only the people"
        " listed as present. Do not ask the player questions."
    )
    return "\n\n".join(parts)
