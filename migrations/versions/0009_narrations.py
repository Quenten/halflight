"""narrations: persist per-turn prose so a resumed run can replay its story log

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-12

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "narrations",
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), primary_key=True),
        sa.Column("turn_no", sa.Integer(), primary_key=True),
        sa.Column("player_text", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_narrations_run_turn", "narrations", ["run_id", "turn_no"])


def downgrade() -> None:
    op.drop_index("ix_narrations_run_turn", table_name="narrations")
    op.drop_table("narrations")
