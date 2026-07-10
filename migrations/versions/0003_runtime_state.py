"""runtime state tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-09

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("character_name", sa.String(), nullable=False),
        sa.Column("archetype", sa.String(), nullable=False, server_default=""),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cause_of_death", sa.String(), nullable=True),
    )
    op.create_table(
        "player_state",
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), primary_key=True),
        sa.Column("hp", sa.Integer(), nullable=False),
        sa.Column("credits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("location_id", sa.String(), nullable=False),
        sa.Column("stats", JSONB(), nullable=False, server_default="{}"),
        sa.Column("time_ticks", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "inventory",
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), primary_key=True),
        sa.Column("item_id", sa.String(), primary_key=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_table(
        "npc_state",
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), primary_key=True),
        sa.Column("npc_id", sa.String(), primary_key=True),
        sa.Column("hp", sa.Integer(), nullable=False),
        sa.Column("alive", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("disposition", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_location", sa.String(), nullable=False),
    )
    op.create_table(
        "faction_rep",
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), primary_key=True),
        sa.Column("faction_id", sa.String(), primary_key=True),
        sa.Column("rep", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("turn_no", sa.Integer(), nullable=False),
        sa.Column("action", JSONB(), nullable=False, server_default="{}"),
        sa.Column("result", JSONB(), nullable=False, server_default="{}"),
        sa.Column("significance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("location_id", sa.String(), nullable=True),
        sa.Column("witnesses", ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_events_run_turn", "events", ["run_id", "turn_no"])


def downgrade() -> None:
    op.drop_table("events")
    op.drop_table("faction_rep")
    op.drop_table("npc_state")
    op.drop_table("inventory")
    op.drop_table("player_state")
    op.drop_table("runs")
