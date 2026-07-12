"""Intent parsing: free player text -> one structured Action.

Grammar-constrained decoding guarantees syntactically valid JSON; Pydantic
validates it into an Action. On failure we retry once at temperature 0, then fall
through to a Custom action so a turn never dies on a parse error.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from halflight.engine.actions import Action, Attack, Custom, Investigate, Move, Talk, parse_action
from halflight.engine.gamestate import GameState
from halflight.gm.client import LLMClient

_GRAMMAR_PATH = Path(__file__).parent / "grammars" / "action.gbnf"

# Movement cues. A `move` the model picks without one of these is treated as a
# spurious teleport and re-interpreted, keeping the player where they are.
_TRAVEL = re.compile(
    r"\b(go|going|goes|head|heading|move|moving|walk|walking|run|running|enter|"
    r"leave|leaving|travel|descend|climb|sneak|creep|return|toward|towards|into|"
    r"back to|down to|up to|over to|out to)\b",
    re.IGNORECASE,
)
_TALK = re.compile(
    r"\b(ask|asks|tell|tells|talk|talking|speak|say|says|question|greet|greets|nod|"
    r"hail|answer|reply|chat|whisper|demand|beg|threaten)\b",
    re.IGNORECASE,
)
# Violence at a present NPC is an attack, whatever the model guessed.
_VIOLENCE = re.compile(
    r"\b(attack|attacks|kill|kills|shoot|shoots|gun|stab|stabs|knife|knifes|hit|hits|"
    r"strike|strikes|punch|punches|beat|beats|slug|club|maul|choke|gut|murder|"
    r"fight|fire on|open fire|swing at|lunge at|jump)\b",
    re.IGNORECASE,
)


@lru_cache(maxsize=1)
def action_grammar() -> str:
    return _GRAMMAR_PATH.read_text(encoding="utf-8")


def render_scene(state: GameState) -> str:
    """Compact scene description: the ids the parser may target, with display names."""
    exits = ", ".join(state.location.connections) or "(none)"
    people = (
        ", ".join(
            f"{n.id} ({n.name or n.id})" + ("" if n.alive else " [dead]")
            for n in state.npcs.values()
        )
        or "(no one)"
    )
    inv = ", ".join(state.player.inventory) or "(empty)"
    return (
        f"Location: {state.location.id} ({state.location.name or state.location.id})\n"
        f"Exits (move targets): {exits}\n"
        f"People here (talk/attack targets): {people}\n"
        f"Your inventory (use_item/sell): {inv}"
    )


def build_prompt(system: str, state: GameState, text: str) -> str:
    return (
        f"{system}\n\n"
        f"## Scene\n{render_scene(state)}\n\n"
        f'## Player input\n"{text}"\n\n'
        f"## Targeting rules\n"
        f"- Use 'move' ONLY when the player explicitly travels to one of the Exits listed above"
        f" (e.g. 'go to the market', 'head down'). Never relocate the player otherwise.\n"
        f"- A question about a person or place ('who is X', 'what is Y', 'describe here') is"
        f" 'investigate' — never 'move'.\n"
        f"- 'talk' only targets someone in People here; if absent, use 'investigate'.\n"
        f"- Targets must be ids from the Scene above.\n\n"
        f"## Output exactly one action as JSON:\n"
    )


def _coerce(raw: str) -> Action | None:
    try:
        return parse_action(json.loads(raw))
    except (json.JSONDecodeError, ValueError):
        return None


def _present_npc(text: str, state: GameState) -> str | None:
    low = text.lower()
    for n in state.npcs.values():
        short = n.id.split("_", 1)[-1]  # npc_dax -> dax
        if short in low or n.id in low or (n.name and n.name.lower() in low):
            return n.id
    return None


def _guard(action: Action, text: str, state: GameState) -> Action:
    """Correct the model's most common misfires against the actual scene, in priority
    order: violence at a present NPC is an attack; addressing one is talk; a `move`
    with no travel cue is a spurious teleport."""
    npc = _present_npc(text, state)

    # Violence toward a present NPC — unless they're only being spoken about.
    if npc is not None and _VIOLENCE.search(text) and not _TALK.search(text):
        if not isinstance(action, Attack):
            return Attack(target=npc)
        return action

    # Addressing a present NPC that the model turned into a move.
    if npc is not None and _TALK.search(text) and isinstance(action, Move):
        return Talk(target=npc)

    # A move with no travel cue at all is a spurious teleport.
    if isinstance(action, Move) and not _TRAVEL.search(text):
        if npc is not None and _TALK.search(text):
            return Talk(target=npc)
        return Investigate()

    return action


def parse_intent(
    text: str,
    state: GameState,
    client: LLMClient,
    *,
    system: str,
    grammar: str | None = None,
) -> Action:
    grammar = grammar if grammar is not None else action_grammar()
    prompt = build_prompt(system, state, text)
    for temperature in (0.2, 0.0):
        raw = client.complete(prompt, grammar=grammar, temperature=temperature)
        action = _coerce(raw)
        if action is not None:
            return _guard(action, text, state)
    return Custom(description=text)
