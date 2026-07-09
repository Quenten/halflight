"""authored tables + lore_chunks

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-09

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBED_DIM = 1024


def upgrade() -> None:
    op.create_table(
        "note_index",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("body_hash", sa.String(), nullable=False),
    )
    op.create_table(
        "factions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("rivals", ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("allies", ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("territory", ARRAY(sa.Text()), nullable=False, server_default="{}"),
    )
    op.create_table(
        "locations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("district", sa.String(), nullable=False),
        sa.Column("danger", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("connections", ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("tags", ARRAY(sa.Text()), nullable=False, server_default="{}"),
    )
    op.create_table(
        "items",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("effects", JSONB(), nullable=False, server_default="{}"),
    )
    op.create_table(
        "npcs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("faction_id", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=False, server_default=""),
        sa.Column("home_location_id", sa.String(), nullable=True),
        sa.Column("disposition_default", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stats", JSONB(), nullable=False, server_default="{}"),
        sa.Column("hp_max", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("schedule", JSONB(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_npcs_faction_id", "npcs", ["faction_id"])
    op.create_index("ix_npcs_home_location_id", "npcs", ["home_location_id"])

    op.create_table(
        "lore_chunks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_note_id", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("chunk_ix", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(EMBED_DIM), nullable=True),
        sa.Column("is_secret", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("revealed", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index("ix_lore_chunks_source_note_id", "lore_chunks", ["source_note_id"])
    # HNSW index for cosine similarity search over embeddings.
    op.execute(
        "CREATE INDEX ix_lore_chunks_embedding ON lore_chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.drop_table("lore_chunks")
    op.drop_index("ix_npcs_home_location_id", table_name="npcs")
    op.drop_index("ix_npcs_faction_id", table_name="npcs")
    op.drop_table("npcs")
    op.drop_table("items")
    op.drop_table("locations")
    op.drop_table("factions")
    op.drop_table("note_index")
