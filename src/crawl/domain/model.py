"""Crawl domain entities."""

import datetime
import urllib.parse
import uuid
from typing import Self

import pydantic

from src import exceptions
from src.common import types as common_types
from src.crawl.domain.status import CrawlStatus, DiscoveredUrlStatus

MIN_DEPTH = 1
MIN_PAGES = 1
DEFAULT_MAX_DEPTH = 2
DEFAULT_MAX_PAGES = 50


class DiscoveredUrl(pydantic.BaseModel):
    """Value object representing a discovered URL during crawling.

    Immutable: all state changes return new instances.
    Equality is determined by value.
    """

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    url: str
    depth: int
    status: DiscoveredUrlStatus
    document_id: str | None = None

    @classmethod
    def create(cls, url: str, depth: int) -> Self:
        """Factory method to create a new discovered URL in PENDING status."""
        return cls(
            url=url,
            depth=depth,
            status=DiscoveredUrlStatus.PENDING,
            document_id=None,
        )

    def mark_ingested(self, document_id: str) -> Self:
        """Mark URL as successfully ingested."""
        return self.model_copy(
            update={
                "status": DiscoveredUrlStatus.INGESTED,
                "document_id": document_id,
            }
        )

    def mark_skipped(self) -> Self:
        """Mark URL as skipped (e.g., filtered out or already exists)."""
        return self.model_copy(
            update={"status": DiscoveredUrlStatus.SKIPPED}
        )

    def mark_failed(self) -> Self:
        """Mark URL as failed to ingest."""
        return self.model_copy(
            update={"status": DiscoveredUrlStatus.FAILED}
        )


class DiscoveredLink(pydantic.BaseModel):
    """Value object representing a link discovered on a web page."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    url: str
    anchor_text: str | None = None


class CrawlJob(pydantic.BaseModel):
    """Entity representing a URL crawling job.

    Immutable: all state changes return new instances.
    """

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    id: str
    notebook_id: str
    seed_url: str
    domain: str
    max_depth: int
    max_pages: int
    url_include_pattern: str | None = None
    url_exclude_pattern: str | None = None
    status: CrawlStatus
    total_discovered: int = 0
    total_ingested: int = 0
    error_message: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @classmethod
    def create(
        cls,
        notebook_id: str,
        seed_url: str,
        max_depth: int = DEFAULT_MAX_DEPTH,
        max_pages: int = DEFAULT_MAX_PAGES,
        url_include_pattern: str | None = None,
        url_exclude_pattern: str | None = None,
    ) -> Self:
        """Factory method to create a new crawl job in PENDING status."""
        if max_depth < MIN_DEPTH:
            raise exceptions.ValidationError(
                f"max_depth must be at least {MIN_DEPTH}, got {max_depth}"
            )
        if max_pages < MIN_PAGES:
            raise exceptions.ValidationError(
                f"max_pages must be at least {MIN_PAGES}, got {max_pages}"
            )

        parsed = urllib.parse.urlparse(seed_url)
        domain = parsed.hostname or ""

        now = common_types.utc_now()
        return cls(
            id=uuid.uuid4().hex,
            notebook_id=notebook_id,
            seed_url=seed_url,
            domain=domain,
            max_depth=max_depth,
            max_pages=max_pages,
            url_include_pattern=url_include_pattern,
            url_exclude_pattern=url_exclude_pattern,
            status=CrawlStatus.PENDING,
            total_discovered=0,
            total_ingested=0,
            error_message=None,
            created_at=now,
            updated_at=now,
        )

    def mark_in_progress(self) -> Self:
        """Mark crawl job as in progress."""
        if not self.status.is_processable:
            raise exceptions.InvalidStateError(
                f"Cannot start crawl job in status: {self.status}"
            )
        return self.model_copy(
            update={
                "status": CrawlStatus.IN_PROGRESS,
                "updated_at": common_types.utc_now(),
            }
        )

    def mark_completed(self) -> Self:
        """Mark crawl job as completed."""
        if self.status != CrawlStatus.IN_PROGRESS:
            raise exceptions.InvalidStateError(
                f"Cannot complete crawl job in status: {self.status}"
            )
        return self.model_copy(
            update={
                "status": CrawlStatus.COMPLETED,
                "updated_at": common_types.utc_now(),
            }
        )

    def mark_failed(self, error_message: str) -> Self:
        """Mark crawl job as failed."""
        if self.status != CrawlStatus.IN_PROGRESS:
            raise exceptions.InvalidStateError(
                f"Cannot fail crawl job in status: {self.status}"
            )
        return self.model_copy(
            update={
                "status": CrawlStatus.FAILED,
                "error_message": error_message,
                "updated_at": common_types.utc_now(),
            }
        )

    def mark_cancelled(self) -> Self:
        """Mark crawl job as cancelled."""
        if not self.status.can_cancel:
            raise exceptions.InvalidStateError(
                f"Cannot cancel crawl job in status: {self.status}"
            )
        return self.model_copy(
            update={
                "status": CrawlStatus.CANCELLED,
                "updated_at": common_types.utc_now(),
            }
        )

    def increment_discovered(self) -> Self:
        """Increment the total discovered URL count."""
        return self.model_copy(
            update={
                "total_discovered": self.total_discovered + 1,
                "updated_at": common_types.utc_now(),
            }
        )

    def increment_ingested(self) -> Self:
        """Increment the total ingested URL count."""
        return self.model_copy(
            update={
                "total_ingested": self.total_ingested + 1,
                "updated_at": common_types.utc_now(),
            }
        )
