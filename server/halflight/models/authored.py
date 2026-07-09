"""Authored tables — mirror of the vault, populated one-way by ingestion.

Referential integrity between notes (npc.faction_id, connections, etc.) is
enforced by the vault linter, not by DB foreign keys: a full re-ingest upserts
in arbitrary order and arrays can't carry FK constraints anyway. The DB stores
what the vault says; the linter guarantees it's consistent first.

`note_index` is the authoritative per-note record (every type, including lore).
It carries the content hash for change-detection/skip and lets ingestion detect
notes deleted from the vault.
"""

from __future__ import annotations

from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, Boolean, Column, Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

EMBED_DIM = 1024  # bge-m3


def _text_array() -> Column[Any]:
    return Column(ARRAY(Text), nullable=False, server_default="{}")


def _jsonb() -> Column[Any]:
    return Column(JSONB, nullable=False, server_default="{}")


class NoteIndex(SQLModel, table=True):
    __tablename__ = "note_index"

    id: str = Field(primary_key=True)
    type: str
    body_hash: str


class Faction(SQLModel, table=True):
    __tablename__ = "factions"

    id: str = Field(primary_key=True)
    name: str
    rivals: list[str] = Field(default_factory=list, sa_column=_text_array())
    allies: list[str] = Field(default_factory=list, sa_column=_text_array())
    territory: list[str] = Field(default_factory=list, sa_column=_text_array())


class Location(SQLModel, table=True):
    __tablename__ = "locations"

    id: str = Field(primary_key=True)
    name: str
    district: str
    danger: int = 0
    connections: list[str] = Field(default_factory=list, sa_column=_text_array())
    tags: list[str] = Field(default_factory=list, sa_column=_text_array())


class Item(SQLModel, table=True):
    __tablename__ = "items"

    id: str = Field(primary_key=True)
    name: str
    kind: str
    value: int = 0
    effects: dict[str, Any] = Field(default_factory=dict, sa_column=_jsonb())


class Npc(SQLModel, table=True):
    __tablename__ = "npcs"

    id: str = Field(primary_key=True)
    name: str
    faction_id: str | None = Field(default=None, index=True)
    role: str = ""
    home_location_id: str | None = Field(default=None, index=True)
    disposition_default: int = 0
    stats: dict[str, Any] = Field(default_factory=dict, sa_column=_jsonb())
    hp_max: int = 0
    schedule: dict[str, Any] = Field(default_factory=dict, sa_column=_jsonb())


class LoreChunk(SQLModel, table=True):
    __tablename__ = "lore_chunks"
    __table_args__ = (
        # HNSW index for cosine similarity. Declared here so metadata matches the DB
        # (migration 0002 creates it) and `alembic check` sees no drift.
        Index(
            "ix_lore_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    source_note_id: str = Field(index=True)
    source_type: str
    chunk_ix: int
    body: str = Field(sa_column=Column(Text, nullable=False))
    # Null until embedded. Secret chunks are stored but not embedded until revealed.
    embedding: Any | None = Field(default=None, sa_column=Column(Vector(EMBED_DIM), nullable=True))
    is_secret: bool = Field(
        default=False, sa_column=Column(Boolean, nullable=False, server_default="false")
    )
    revealed: bool = Field(
        default=False, sa_column=Column(Boolean, nullable=False, server_default="false")
    )
