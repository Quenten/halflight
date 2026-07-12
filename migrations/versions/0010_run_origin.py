"""run origin: persist the character's chargen backstory as a prose blurb

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-12

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "runs",
        sa.Column("origin", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("runs", "origin")
