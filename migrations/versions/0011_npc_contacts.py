"""npc_state: backstory-contact identity + known-journal flag

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-13

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("npc_state", sa.Column("name", sa.Text(), nullable=True))
    op.add_column("npc_state", sa.Column("relationship", sa.Text(), nullable=True))
    op.add_column("npc_state", sa.Column("note", sa.Text(), nullable=True))
    op.add_column(
        "npc_state",
        sa.Column("known", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("npc_state", "known")
    op.drop_column("npc_state", "note")
    op.drop_column("npc_state", "relationship")
    op.drop_column("npc_state", "name")
