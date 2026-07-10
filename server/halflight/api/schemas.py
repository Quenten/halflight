"""Request/response models for the API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from halflight.engine.actions import STAT_NAMES


def _default_stats() -> dict[str, int]:
    return {name: 10 for name in STAT_NAMES}


class StartRunRequest(BaseModel):
    character_name: str = "Drifter"
    start_location: str
    archetype: str = ""
    stats: dict[str, int] = Field(default_factory=_default_stats)
    hp: int = 15
    credits: int = 20
    inventory: dict[str, int] = Field(default_factory=dict)


class TurnRequest(BaseModel):
    run_id: int
    text: str


class NpcBrief(BaseModel):
    id: str
    name: str
    alive: bool
    disposition: int


class ExitBrief(BaseModel):
    id: str
    name: str


class ItemBrief(BaseModel):
    id: str
    name: str
    kind: str
    quantity: int


class StateResponse(BaseModel):
    run_id: int
    character_name: str
    hp: int
    credits: int
    location_id: str
    location_name: str
    time_ticks: int
    ended: bool
    cause_of_death: str | None
    stats: dict[str, int]
    exits: list[ExitBrief]
    npcs: list[NpcBrief]
    inventory: list[ItemBrief]
