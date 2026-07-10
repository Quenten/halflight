"""Structured player actions — the only thing the engine acts on.

A discriminated union on `kind`. The LLM parser emits one of these (grammar-
constrained) at M4; the engine resolves it. `parse_action` validates a dict into
the right variant.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter

StatName = Literal["muscle", "nerve", "wits", "tech", "streetwise", "presence"]
STAT_NAMES: tuple[StatName, ...] = (
    "muscle",
    "nerve",
    "wits",
    "tech",
    "streetwise",
    "presence",
)


class Move(BaseModel):
    kind: Literal["move"] = "move"
    target: str  # location id


class Talk(BaseModel):
    kind: Literal["talk"] = "talk"
    target: str  # npc id
    topic: str | None = None


class Attack(BaseModel):
    kind: Literal["attack"] = "attack"
    target: str  # npc id
    method: str | None = None


class Trade(BaseModel):
    kind: Literal["trade"] = "trade"
    target: str  # npc id
    item: str  # item id
    direction: Literal["buy", "sell"]


class UseItem(BaseModel):
    kind: Literal["use_item"] = "use_item"
    item: str  # item id
    target: str | None = None


class Investigate(BaseModel):
    kind: Literal["investigate"] = "investigate"
    target: str | None = None  # location/object/npc


class Custom(BaseModel):
    kind: Literal["custom"] = "custom"
    description: str
    stat_hint: StatName | None = None


Action = Annotated[
    Move | Talk | Attack | Trade | UseItem | Investigate | Custom,
    Field(discriminator="kind"),
]

_ADAPTER: TypeAdapter[Action] = TypeAdapter(Action)


def parse_action(data: dict[str, object]) -> Action:
    """Validate a raw dict into the matching Action variant."""
    return _ADAPTER.validate_python(data)
