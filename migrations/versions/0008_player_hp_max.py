"""player hp_max

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-12

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "player_state",
        sa.Column("hp_max", sa.Integer(), nullable=False, server_default="0"),
    )
    # Backfill existing runs: cap = current hp.
    op.execute("UPDATE player_state SET hp_max = hp WHERE hp_max = 0")


def downgrade() -> None:
    op.drop_column("player_state", "hp_max")
