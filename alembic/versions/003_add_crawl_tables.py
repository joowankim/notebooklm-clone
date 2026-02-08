"""Add crawl_jobs and crawl_discovered_urls tables.

Revision ID: 003
Revises: d295474d0997
Create Date: 2026-02-08 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "d295474d0997"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create crawl_jobs table
    op.create_table(
        "crawl_jobs",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "notebook_id",
            sa.String(32),
            sa.ForeignKey("notebooks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("seed_url", sa.Text, nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("max_depth", sa.Integer, nullable=False),
        sa.Column("max_pages", sa.Integer, nullable=False),
        sa.Column("url_include_pattern", sa.Text, nullable=True),
        sa.Column("url_exclude_pattern", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("total_discovered", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_ingested", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_crawl_jobs_notebook_id", "crawl_jobs", ["notebook_id"])
    op.create_index("ix_crawl_jobs_status", "crawl_jobs", ["status"])

    # Create crawl_discovered_urls table
    op.create_table(
        "crawl_discovered_urls",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "crawl_job_id",
            sa.String(32),
            sa.ForeignKey("crawl_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("depth", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "document_id",
            sa.String(32),
            sa.ForeignKey("documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.UniqueConstraint("crawl_job_id", "url", name="uq_discovered_url_crawl_job_url"),
    )
    op.create_index(
        "ix_crawl_discovered_urls_crawl_job_id",
        "crawl_discovered_urls",
        ["crawl_job_id"],
    )


def downgrade() -> None:
    op.drop_table("crawl_discovered_urls")
    op.drop_table("crawl_jobs")
