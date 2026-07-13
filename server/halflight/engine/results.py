"""TurnResult — the engine's verdict on one turn. Fed to the narrator, never contradicted."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from halflight.engine.actions import Action

Outcome = Literal["success", "failure", "invalid", "narrative_only"]


class StateChange(BaseModel):
    entity: str  # "player" or an npc id
    field: str  # e.g. "hp", "credits", "location_id", "disposition"
    delta: Any  # numeric delta or absolute value depending on field


class SceneEvent(BaseModel):
    kind: str  # "attack_hit", "npc_died", "item_gained", ...
    detail: dict[str, Any] = Field(default_factory=dict)


class TurnResult(BaseModel):
    action: Action
    valid: bool
    reason: str | None = None
    roll: int | None = None
    difficulty: int | None = None
    outcome: Outcome
    roll_base: int | None = None  # the raw d20, before the stat modifier
    roll_mod: int | None = None  # the stat modifier applied to this check
    state_changes: list[StateChange] = Field(default_factory=list)
    scene_events: list[SceneEvent] = Field(default_factory=list)
    significance: int = 0  # 0-3; drives whether the event gets embedded
