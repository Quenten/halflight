"""Turn receipt: a compact, plain list of what mechanically changed this turn.

Driven entirely off the engine's TurnResult (the source of truth), not the prose —
so the "what happened" line under a narration can never disagree with the state.
Each item is {text, tone} where tone in {good, bad, neutral} drives UI colour.
"""

from __future__ import annotations

from sqlmodel import Session

from halflight.engine.results import TurnResult
from halflight.models import Faction, Item, Location, Npc

Item_ = dict[str, str]


def _name(session: Session, model: type, id_: object) -> str:
    if not id_:
        return "someone"
    obj = session.get(model, id_)
    name = getattr(obj, "name", None)
    return name if isinstance(name, str) else str(id_)


def build_receipt(session: Session, result: TurnResult) -> list[Item_]:
    items: list[Item_] = []

    for c in result.state_changes:
        entity, field, delta = c.entity, c.field, c.delta
        if entity == "player":
            if field == "hp":
                d = int(delta)
                if d < 0:
                    items.append({"text": f"You took {-d} damage", "tone": "bad"})
                elif d > 0:
                    items.append({"text": f"Healed {d} HP", "tone": "good"})
            elif field == "credits":
                d = int(delta)
                if d < 0:
                    items.append({"text": f"Spent {-d} scrip", "tone": "bad"})
                elif d > 0:
                    items.append({"text": f"Gained {d} scrip", "tone": "good"})
            elif field.startswith("inventory:"):
                d = int(delta)
                name = _name(session, Item, field.split(":", 1)[1])
                if d > 0:
                    qty = f" x{d}" if d > 1 else ""
                    items.append({"text": f"Picked up {name}{qty}", "tone": "good"})
                elif d < 0:
                    qty = f" x{-d}" if -d > 1 else ""
                    items.append({"text": f"Lost {name}{qty}", "tone": "bad"})
        elif entity.startswith("faction:"):
            if field == "rep":
                d = int(delta)
                name = _name(session, Faction, entity.split(":", 1)[1])
                sign = "+" if d > 0 else ""
                items.append(
                    {"text": f"{name} standing {sign}{d}", "tone": "good" if d > 0 else "bad"}
                )
        else:  # an NPC
            if field == "hp" and int(delta) < 0:
                items.append({"text": f"{_name(session, Npc, entity)} took {-int(delta)} damage",
                              "tone": "neutral"})

    for ev in result.scene_events:
        detail = ev.detail
        if ev.kind == "npc_died":
            items.append(
                {"text": f"{_name(session, Npc, detail.get('npc'))} killed", "tone": "bad"}
            )
        elif ev.kind == "player_died":
            items.append({"text": "You died", "tone": "bad"})
        elif ev.kind == "moved":
            items.append({"text": f"Moved to {_name(session, Location, detail.get('to'))}",
                          "tone": "neutral"})
        elif ev.kind == "trade_refused":
            items.append({"text": "Couldn't cover the price", "tone": "neutral"})

    return items
