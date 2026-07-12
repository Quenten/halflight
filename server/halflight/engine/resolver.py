"""The resolver — pure rules. Turns an Action + GameState into a TurnResult.

No DB, no LLM, no randomness except the injected Roller. Every mechanical
decision (hit/miss, damage, validity, plausibility) happens here and nowhere
else. Numbers are deliberately simple and tunable.
"""

from __future__ import annotations

import re

from halflight.engine.actions import (
    Action,
    Attack,
    Custom,
    Investigate,
    Move,
    Talk,
    Trade,
    UseItem,
)
from halflight.engine.dice import Roller
from halflight.engine.gamestate import BASELINE_STAT, GameState
from halflight.engine.results import SceneEvent, StateChange, TurnResult

DIFFICULTY = {"trivial": 5, "easy": 10, "medium": 15, "hard": 20, "very_hard": 25}
BASE_DEFENSE = 10
UNARMED_DAMAGE = 3

# Custom actions that try to conjure resources/items by fiat — the world won't cooperate.
# Matches an acquisition verb near a resource/valuable, regardless of a leading "I".
_IMPOSSIBLE = re.compile(
    r"\b(find|found|discover|pocket|grab|take|get|have|gain|acquire|obtain|loot"
    r"|spawn|conjure|materiali[sz]e)\b[^.]*?"
    r"\b(\d{2,}|scrip|credits?|money|cash|gun|rifle|pistol|weapon|ammo|key|keycard)\b",
    re.IGNORECASE,
)


def stat_mod(stat: int) -> int:
    """+1 per 2 points above baseline (10). 10 -> 0, 14 -> +2, 8 -> -1."""
    return (stat - BASELINE_STAT) // 2


def _invalid(action: Action, reason: str) -> TurnResult:
    return TurnResult(action=action, valid=False, reason=reason, outcome="invalid")


def _weapon_base(state: GameState, method: str | None) -> int:
    if method and method in state.items:
        dmg = state.items[method].effects.get("damage")
        if isinstance(dmg, int):
            return dmg
    return UNARMED_DAMAGE


def _resolve_move(state: GameState, action: Move) -> TurnResult:
    if action.target not in state.location.connections:
        return _invalid(action, f"no route from {state.location.id} to {action.target}")
    return TurnResult(
        action=action,
        valid=True,
        outcome="success",
        state_changes=[
            StateChange(entity="player", field="location_id", delta=action.target),
            StateChange(entity="player", field="time_ticks", delta=1),
        ],
        scene_events=[
            SceneEvent(kind="moved", detail={"from": state.location.id, "to": action.target})
        ],
    )


def _resolve_talk(state: GameState, action: Talk) -> TurnResult:
    npc = state.npcs.get(action.target)
    if npc is None:
        return _invalid(action, f"{action.target} is not here")
    if not npc.alive:
        return _invalid(action, f"{action.target} is dead")
    return TurnResult(
        action=action,
        valid=True,
        outcome="narrative_only",
        scene_events=[
            SceneEvent(kind="talked", detail={"npc": npc.id, "topic": action.topic})
        ],
    )


def _resolve_attack(state: GameState, action: Attack, dice: Roller) -> TurnResult:
    npc = state.npcs.get(action.target)
    if npc is None:
        return _invalid(action, f"{action.target} is not here")
    if not npc.alive:
        return _invalid(action, f"{action.target} is already dead")

    changes: list[StateChange] = []
    events: list[SceneEvent] = []
    significance = 1

    atk = dice.d20() + stat_mod(state.player.stat("muscle"))
    defense = BASE_DEFENSE + stat_mod(npc.stat("nerve"))
    npc_hp = npc.hp

    if atk >= defense:
        dmg = max(1, _weapon_base(state, action.method) + (atk - defense) // 2)
        npc_hp -= dmg
        changes.append(StateChange(entity=npc.id, field="hp", delta=-dmg))
        if npc_hp <= 0:
            changes.append(StateChange(entity=npc.id, field="alive", delta=False))
            events.append(SceneEvent(kind="npc_died", detail={"npc": npc.id}))
            significance = 2
        else:
            events.append(SceneEvent(kind="attack_hit", detail={"npc": npc.id, "damage": dmg}))
        outcome = "success"
    else:
        events.append(SceneEvent(kind="attack_miss", detail={"npc": npc.id}))
        outcome = "failure"

    # A surviving NPC hits back once.
    if npc_hp > 0:
        retaliation = dice.d20() + stat_mod(npc.stat("muscle"))
        player_def = BASE_DEFENSE + stat_mod(state.player.stat("nerve"))
        if retaliation >= player_def:
            rdmg = max(1, UNARMED_DAMAGE + (retaliation - player_def) // 2)
            changes.append(StateChange(entity="player", field="hp", delta=-rdmg))
            if state.player.hp - rdmg <= 0:
                events.append(SceneEvent(kind="player_died", detail={"by": npc.id}))
                significance = 3
            else:
                events.append(
                    SceneEvent(kind="player_hit", detail={"by": npc.id, "damage": rdmg})
                )

    return TurnResult(
        action=action,
        valid=True,
        roll=atk,
        difficulty=defense,
        outcome=outcome,
        state_changes=changes,
        scene_events=events,
        significance=significance,
    )


def _resolve_trade(state: GameState, action: Trade) -> TurnResult:
    item = state.items.get(action.item)
    npc = state.npcs.get(action.target)
    if npc is None:
        return _invalid(action, f"{action.target} is not here")
    if item is None:
        return _invalid(action, f"no such item {action.item}")

    if action.direction == "buy":
        if state.player.credits < item.value:
            return TurnResult(
                action=action,
                valid=True,
                outcome="failure",
                reason="not enough scrip",
                scene_events=[SceneEvent(kind="trade_refused", detail={"item": item.id})],
            )
        return TurnResult(
            action=action,
            valid=True,
            outcome="success",
            state_changes=[
                StateChange(entity="player", field="credits", delta=-item.value),
                StateChange(entity="player", field=f"inventory:{item.id}", delta=1),
            ],
            scene_events=[SceneEvent(kind="item_gained", detail={"item": item.id})],
        )

    # sell
    if state.player.inventory.get(item.id, 0) <= 0:
        return _invalid(action, f"you don't have {item.id}")
    return TurnResult(
        action=action,
        valid=True,
        outcome="success",
        state_changes=[
            StateChange(entity="player", field="credits", delta=item.value),
            StateChange(entity="player", field=f"inventory:{item.id}", delta=-1),
        ],
        scene_events=[SceneEvent(kind="item_lost", detail={"item": item.id})],
    )


def _resolve_use_item(state: GameState, action: UseItem) -> TurnResult:
    if state.player.inventory.get(action.item, 0) <= 0:
        return _invalid(action, f"you don't have {action.item}")
    item = state.items.get(action.item)
    heal = item.effects.get("heal") if item is not None else None
    if isinstance(heal, int):
        return TurnResult(
            action=action,
            valid=True,
            outcome="success",
            state_changes=[
                StateChange(entity="player", field="hp", delta=heal),
                StateChange(entity="player", field=f"inventory:{action.item}", delta=-1),
            ],
            scene_events=[SceneEvent(kind="item_used", detail={"item": action.item, "heal": heal})],
        )
    return TurnResult(
        action=action,
        valid=True,
        outcome="narrative_only",
        scene_events=[SceneEvent(kind="item_used", detail={"item": action.item})],
    )


def _resolve_investigate(state: GameState, action: Investigate, dice: Roller) -> TurnResult:
    # Narrative outcome (so questions/looks always read well), but a wits roll is
    # recorded: the GM layer uses it to gate whether a hidden secret is uncovered.
    roll = dice.d20() + stat_mod(state.player.stat("wits"))
    return TurnResult(
        action=action,
        valid=True,
        roll=roll,
        difficulty=DIFFICULTY["medium"],
        outcome="narrative_only",
        scene_events=[SceneEvent(kind="investigated", detail={"target": action.target})],
    )


def _resolve_custom(state: GameState, action: Custom, dice: Roller) -> TurnResult:
    if _IMPOSSIBLE.search(action.description):
        return TurnResult(
            action=action,
            valid=True,
            outcome="failure",
            reason="the world does not cooperate",
            scene_events=[SceneEvent(kind="no_effect", detail={"attempt": action.description})],
        )
    stat = action.stat_hint or "wits"
    difficulty = DIFFICULTY["medium"]
    roll = dice.d20() + stat_mod(state.player.stat(stat))
    outcome = "success" if roll >= difficulty else "failure"
    return TurnResult(
        action=action,
        valid=True,
        roll=roll,
        difficulty=difficulty,
        outcome=outcome,
        scene_events=[
            SceneEvent(kind="custom_" + outcome, detail={"attempt": action.description})
        ],
    )


def resolve(state: GameState, action: Action, dice: Roller) -> TurnResult:
    """Resolve one action against the scene. Pure; the only entropy is `dice`."""
    if isinstance(action, Move):
        return _resolve_move(state, action)
    if isinstance(action, Talk):
        return _resolve_talk(state, action)
    if isinstance(action, Attack):
        return _resolve_attack(state, action, dice)
    if isinstance(action, Trade):
        return _resolve_trade(state, action)
    if isinstance(action, UseItem):
        return _resolve_use_item(state, action)
    if isinstance(action, Investigate):
        return _resolve_investigate(state, action, dice)
    return _resolve_custom(state, action, dice)
