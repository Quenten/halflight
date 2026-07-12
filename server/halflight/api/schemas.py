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


class LocationBrief(BaseModel):
    id: str
    name: str


class NpcBrief(BaseModel):
    id: str
    name: str
    alive: bool
    disposition: int  # effective: personal + faction standing


class FactionStanding(BaseModel):
    id: str
    name: str
    rep: int


class ExitBrief(BaseModel):
    id: str
    name: str


class ItemBrief(BaseModel):
    id: str
    name: str
    kind: str
    quantity: int


class ClassOut(BaseModel):
    id: str
    name: str
    hp: int
    credits: int
    items: list[str]  # display names
    blurb: str


class OptionOut(BaseModel):
    id: str
    name: str
    blurb: str
    hint: str


class StepOut(BaseModel):
    id: str
    title: str
    prompt: str
    rolls: bool
    options: list[OptionOut]


class ChargenData(BaseModel):
    classes: list[ClassOut]
    steps: list[StepOut]


class ChargenRequest(BaseModel):
    character_name: str = "Drifter"
    class_id: str
    choices: dict[str, str] = Field(default_factory=dict)


class BuildStepOut(BaseModel):
    step_title: str
    option_name: str
    outcome_kind: str
    text: str
    summary: str


class StateResponse(BaseModel):
    run_id: int
    character_name: str
    hp: int
    credits: int
    location_id: str
    location_name: str
    time_ticks: int
    heat: int
    ended: bool
    cause_of_death: str | None
    stats: dict[str, int]
    exits: list[ExitBrief]
    npcs: list[NpcBrief]
    inventory: list[ItemBrief]
    standing: list[FactionStanding]


class ChargenResult(BaseModel):
    state: StateResponse
    backstory: list[BuildStepOut]
