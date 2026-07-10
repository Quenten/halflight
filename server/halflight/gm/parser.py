"""Intent parsing: free player text -> one structured Action.

Grammar-constrained decoding guarantees syntactically valid JSON; Pydantic
validates it into an Action. On failure we retry once at temperature 0, then fall
through to a Custom action so a turn never dies on a parse error.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from halflight.engine.actions import Action, Custom, parse_action
from halflight.engine.gamestate import GameState
from halflight.gm.client import LLMClient

_GRAMMAR_PATH = Path(__file__).parent / "grammars" / "action.gbnf"


@lru_cache(maxsize=1)
def action_grammar() -> str:
    return _GRAMMAR_PATH.read_text(encoding="utf-8")


def render_scene(state: GameState) -> str:
    """Compact scene description: the ids the parser is allowed to target."""
    exits = ", ".join(state.location.connections) or "(none)"
    people = (
        ", ".join(f"{n.id}" + ("" if n.alive else " [dead]") for n in state.npcs.values())
        or "(no one)"
    )
    inv = ", ".join(state.player.inventory) or "(empty)"
    return (
        f"Location: {state.location.id}\n"
        f"Exits (move targets): {exits}\n"
        f"People here (talk/attack targets): {people}\n"
        f"Your inventory (use_item/sell): {inv}"
    )


def build_prompt(system: str, state: GameState, text: str) -> str:
    return (
        f"{system}\n\n"
        f"## Scene\n{render_scene(state)}\n\n"
        f'## Player input\n"{text}"\n\n'
        f"## Output exactly one action as JSON:\n"
    )


def _coerce(raw: str) -> Action | None:
    try:
        return parse_action(json.loads(raw))
    except (json.JSONDecodeError, ValueError):
        return None


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
            return action
    return Custom(description=text)
