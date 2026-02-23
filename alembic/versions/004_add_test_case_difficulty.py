"""Add difficulty column to evaluation_test_cases.

Revision ID: 004
Revises: 003
Create Date: 2026-02-23 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "evaluation_test_cases",
        sa.Column("difficulty", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("evaluation_test_cases", "difficulty")
