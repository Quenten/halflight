"""Runtime tables — per-playthrough state. Written by the engine, never the vault.

Timestamps are timezone-aware (TIMESTAMPTZ) and set explicitly by the engine at
insert time, sidestepping SQLModel's sa_column/default conflict.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, Column, DateTime, Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from halflight.models.authored import EMBED_DIM


def utcnow() -> datetime:
    return datetime.now(UTC)


def _ts_col(*, nullable: bool) -> Column[Any]:
    return Column(DateTime(timezone=True), nullable=nullable)


def _jsonb() -> Column[Any]:
    return Column(JSONB, nullable=False, server_default="{}")


class Run(SQLModel, table=True):
    __tablename__ = "runs"

    id: int | None = Field(default=None, primary_key=True)
    character_name: str
    archetype: str = ""
    started_at: datetime = Field(sa_column=_ts_col(nullable=False))
    ended_at: datetime | None = Field(default=None, sa_column=_ts_col(nullable=True))
    cause_of_death: str | None = None


class PlayerState(SQLModel, table=True):
    __tablename__ = "player_state"

    run_id: int = Field(primary_key=True, foreign_key="runs.id")
    hp: int
    hp_max: int = 0
    credits: int = 0
    location_id: str
    stats: dict[str, Any] = Field(default_factory=dict, sa_column=_jsonb())
    time_ticks: int = 0
    heat: int = 0  # Watch/Combine attention; rises with witnessed violence, decays over time


class Inventory(SQLModel, table=True):
    __tablename__ = "inventory"

    run_id: int = Field(primary_key=True, foreign_key="runs.id")
    item_id: str = Field(primary_key=True)
    quantity: int = 1


class NpcState(SQLModel, table=True):
    __tablename__ = "npc_state"

    run_id: int = Field(primary_key=True, foreign_key="runs.id")
    npc_id: str = Field(primary_key=True)
    hp: int
    alive: bool = True
    disposition: int = 0
    current_location: str


class FactionRep(SQLModel, table=True):
    __tablename__ = "faction_rep"

    run_id: int = Field(primary_key=True, foreign_key="runs.id")
    faction_id: str = Field(primary_key=True)
    rep: int = 0


class Event(SQLModel, table=True):
    __tablename__ = "events"
    __table_args__ = (Index("ix_events_run_turn", "run_id", "turn_no"),)

    id: int | None = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="runs.id")
    turn_no: int
    action: dict[str, Any] = Field(default_factory=dict, sa_column=_jsonb())
    result: dict[str, Any] = Field(default_factory=dict, sa_column=_jsonb())
    significance: int = 0
    location_id: str | None = None
    witnesses: list[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(Text), nullable=False, server_default="{}"),
    )
    ts: datetime = Field(sa_column=_ts_col(nullable=False))


class EventChunk(SQLModel, table=True):
    """One embedded, one-line factual memory of a significant event (M6)."""

    __tablename__ = "event_chunks"
    __table_args__ = (
        Index(
            "ix_event_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    event_id: int = Field(primary_key=True, foreign_key="events.id")
    run_id: int = Field(index=True, foreign_key="runs.id")
    turn_no: int
    description: str = Field(sa_column=Column(Text, nullable=False))
    embedding: Any | None = Field(default=None, sa_column=Column(Vector(EMBED_DIM), nullable=True))
    ts: datetime = Field(sa_column=_ts_col(nullable=False))


class NpcMemory(SQLModel, table=True):
    """What an NPC knows: an event they witnessed, were told, or is public (M6)."""

    __tablename__ = "npc_memories"
    __table_args__ = (Index("ix_npc_memories_lookup", "run_id", "npc_id"),)

    run_id: int = Field(primary_key=True, foreign_key="runs.id")
    npc_id: str = Field(primary_key=True)
    event_id: int = Field(primary_key=True, foreign_key="events.id")
    how_known: str = "witnessed"  # witnessed | told | public
    ts: datetime = Field(sa_column=_ts_col(nullable=False))


class Summary(SQLModel, table=True):
    """Rolling episodic summary of older turns (M6): facts / promises / threads."""

    __tablename__ = "summaries"

    id: int | None = Field(default=None, primary_key=True)
    run_id: int = Field(index=True, foreign_key="runs.id")
    up_to_turn: int
    body: dict[str, Any] = Field(default_factory=dict, sa_column=_jsonb())
    ts: datetime = Field(sa_column=_ts_col(nullable=False))
