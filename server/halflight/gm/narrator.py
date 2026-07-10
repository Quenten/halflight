"""Narration: turn the TurnResult + context into prose, then fact-check it.

System prompt = gm_style + narrator_rules + few-shot examples (stable across turns,
so llama.cpp's prompt cache keeps it warm). After generating, a cheap keyword check
catches narration that contradicts the mechanical outcome (e.g. "your knife sinks
in" on a failed attack, or an invented death). On mismatch: regenerate once at low
temperature, then fall back to a terse factual paragraph.
"""

from __future__ import annotations

import re

from halflight.engine.results import SceneEvent, TurnResult
from halflight.gm.client import LLMClient
from halflight.gm.prompts import gm_style, narration_examples, narrator_rules

_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)

_HIT_WORDS = re.compile(
    r"\b(sank|sinks?|sink|connected|landed|struck|slammed|buried|drove it|split|cleaved)\b",
    re.IGNORECASE,
)
_DEATH_WORDS = re.compile(
    r"\b(killed|slain|lifeless|a corpse|went limp|crumpled dead|slumped dead|stopped moving)\b",
    re.IGNORECASE,
)
_PLAYER_DEATH_WORDS = re.compile(
    r"\byou (die|died|are dead|black out for good|bleed out)\b", re.IGNORECASE
)


def strip_thinking(text: str) -> str:
    """Remove Qwen <think> blocks defensively (enable_thinking=false should prevent them)."""
    text = _THINK.sub("", text)
    if "<think>" in text and "</think>" not in text:  # truncated/unclosed
        text = text.split("<think>", 1)[0]
    return text.strip()


def system_prompt(vault_path: str) -> str:
    return "\n\n".join(
        (gm_style(vault_path), narrator_rules(vault_path), narration_examples(vault_path))
    )


def check_consistency(text: str, result: TurnResult) -> list[str]:
    """Return contradictions between narration and the TurnResult (empty = clean)."""
    issues: list[str] = []
    kinds = {e.kind for e in result.scene_events}

    if result.action.kind == "attack" and result.outcome == "failure":
        if _HIT_WORDS.search(text):
            issues.append("narration implies a hit on a failed attack")

    if "npc_died" not in kinds and "player_died" not in kinds and _DEATH_WORDS.search(text):
        issues.append("narration implies a death that did not occur")

    if "player_died" not in kinds and _PLAYER_DEATH_WORDS.search(text):
        issues.append("narration implies the player died when they did not")

    return issues


def _event_sentence(event: SceneEvent) -> str:
    d = event.detail
    match event.kind:
        case "attack_hit":
            return f"You hit {d.get('npc')} for {d.get('damage')}."
        case "attack_miss":
            return "Your strike missed."
        case "npc_died":
            return f"{d.get('npc')} went down and did not get up."
        case "player_hit":
            return f"{d.get('by')} caught you for {d.get('damage')}."
        case "player_died":
            return "You did not get up."
        case "moved":
            return f"You moved to {d.get('to')}."
        case "talked":
            return f"You traded words with {d.get('npc')}."
        case "item_gained":
            return f"You took {d.get('item')}."
        case "item_lost":
            return f"You handed over {d.get('item')}."
        case "item_used":
            return f"You used {d.get('item')}."
        case "trade_refused":
            return "You couldn't cover the price."
        case "no_effect":
            return "Nothing came of it."
        case _:
            return ""


def factual_fallback(result: TurnResult) -> str:
    sentences = [s for e in result.scene_events if (s := _event_sentence(e))]
    if not sentences:
        default = {
            "success": "It worked.",
            "failure": "It didn't work.",
            "narrative_only": "Nothing changed.",
            "invalid": result.reason or "You couldn't do that.",
        }
        sentences = [default[result.outcome]]
    return " ".join(sentences)


def narrate(
    client: LLMClient,
    *,
    system: str,
    context: str,
    result: TurnResult,
    max_tokens: int = 350,
) -> str:
    """Generate narration, validate it, regenerate once, else fall back to facts."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": context},
    ]
    text = strip_thinking(
        "".join(client.chat_stream(messages, temperature=0.8, max_tokens=max_tokens))
    )
    if not check_consistency(text, result):
        return text

    retry = strip_thinking(
        "".join(client.chat_stream(messages, temperature=0.2, max_tokens=max_tokens))
    )
    if not check_consistency(retry, result):
        return retry

    return factual_fallback(result)
