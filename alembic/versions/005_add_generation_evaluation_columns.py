"""Add generation evaluation columns to evaluation tables.

Revision ID: 005
Revises: 004
Create Date: 2026-02-23 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "evaluation_runs",
        sa.Column(
            "evaluation_type",
            sa.String(20),
            nullable=False,
            server_default="retrieval_only",
        ),
    )
    op.add_column(
        "evaluation_runs",
        sa.Column("mean_faithfulness", sa.Float(), nullable=True),
    )
    op.add_column(
        "evaluation_runs",
        sa.Column("mean_answer_relevancy", sa.Float(), nullable=True),
    )

    op.add_column(
        "evaluation_test_case_results",
        sa.Column("generated_answer", sa.Text(), nullable=True),
    )
    op.add_column(
        "evaluation_test_case_results",
        sa.Column("faithfulness", sa.Float(), nullable=True),
    )
    op.add_column(
        "evaluation_test_case_results",
        sa.Column("answer_relevancy", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("evaluation_test_case_results", "answer_relevancy")
    op.drop_column("evaluation_test_case_results", "faithfulness")
    op.drop_column("evaluation_test_case_results", "generated_answer")

    op.drop_column("evaluation_runs", "mean_answer_relevancy")
    op.drop_column("evaluation_runs", "mean_faithfulness")
    op.drop_column("evaluation_runs", "evaluation_type")
