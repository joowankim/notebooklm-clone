"""Crawl ORM schemas."""

import datetime

import sqlalchemy
import sqlalchemy.orm

from src import database as database_module


class CrawlJobSchema(database_module.Base):
    """SQLAlchemy ORM model for crawl jobs."""

    __tablename__ = "crawl_jobs"

    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32), primary_key=True
    )
    notebook_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32),
        sqlalchemy.ForeignKey("notebooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seed_url: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Text, nullable=False
    )
    domain: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(255), nullable=False
    )
    max_depth: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer, nullable=False
    )
    max_pages: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer, nullable=False
    )
    url_include_pattern: sqlalchemy.orm.Mapped[str | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Text, nullable=True
    )
    url_exclude_pattern: sqlalchemy.orm.Mapped[str | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Text, nullable=True
    )
    status: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(20),
        nullable=False,
        default="pending",
        index=True,
    )
    total_discovered: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer, nullable=False, default=0
    )
    total_ingested: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer, nullable=False, default=0
    )
    error_message: sqlalchemy.orm.Mapped[str | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Text, nullable=True
    )
    created_at: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )
    updated_at: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
        onupdate=sqlalchemy.func.now(),
    )

    discovered_urls: sqlalchemy.orm.Mapped[list["DiscoveredUrlSchema"]] = (
        sqlalchemy.orm.relationship(
            "DiscoveredUrlSchema",
            back_populates="crawl_job",
            cascade="all, delete-orphan",
        )
    )


class DiscoveredUrlSchema(database_module.Base):
    """SQLAlchemy ORM model for discovered URLs."""

    __tablename__ = "crawl_discovered_urls"

    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32), primary_key=True
    )
    crawl_job_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32),
        sqlalchemy.ForeignKey("crawl_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Text, nullable=False
    )
    depth: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer, nullable=False
    )
    status: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(20),
        nullable=False,
        default="pending",
    )
    document_id: sqlalchemy.orm.Mapped[str | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32),
        sqlalchemy.ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )

    crawl_job: sqlalchemy.orm.Mapped["CrawlJobSchema"] = sqlalchemy.orm.relationship(
        "CrawlJobSchema",
        back_populates="discovered_urls",
    )

    __table_args__ = (
        sqlalchemy.UniqueConstraint(
            "crawl_job_id", "url", name="uq_discovered_url_crawl_job_url"
        ),
    )
