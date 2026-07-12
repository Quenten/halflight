"""npc_memories (NPC memory)

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-11

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "npc_memories",
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), primary_key=True),
        sa.Column("npc_id", sa.String(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id"), primary_key=True),
        sa.Column("how_known", sa.String(), nullable=False, server_default="witnessed"),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_npc_memories_lookup", "npc_memories", ["run_id", "npc_id"])


def downgrade() -> None:
    op.drop_table("npc_memories")
