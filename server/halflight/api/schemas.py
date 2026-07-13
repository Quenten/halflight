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


class KnownNpc(BaseModel):
    id: str
    name: str
    relationship: str  # ally/enemy/fearful/... for contacts; a mood label for met NPCs
    disposition: int
    last_seen: str  # location name, or "Unknown"
    note: str | None
    alive: bool


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
    contact: str | None = None  # e.g. "Corva (enemy)"


class StateResponse(BaseModel):
    run_id: int
    character_name: str
    origin: str
    hp: int
    hp_max: int
    credits: int
    location_id: str
    location_name: str
    time_ticks: int
    shift: str  # display name of the current city shift (Highshift/Lowshift/Deadshift)
    curfew: bool  # deadshift curfew is in effect
    heat: int
    ended: bool
    cause_of_death: str | None
    stats: dict[str, int]
    exits: list[ExitBrief]
    npcs: list[NpcBrief]
    inventory: list[ItemBrief]
    standing: list[FactionStanding]
    known_npcs: list[KnownNpc]


class ChargenResult(BaseModel):
    state: StateResponse
    backstory: list[BuildStepOut]


class TurnRecord(BaseModel):
    turn_no: int
    player_text: str
    narration: str


class HistoryResponse(BaseModel):
    run_id: int
    turns: list[TurnRecord]
