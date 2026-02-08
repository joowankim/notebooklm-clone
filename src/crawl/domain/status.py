"""Crawl domain status enums."""

import enum


class CrawlStatus(enum.StrEnum):
    """Crawl job processing status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_processable(self) -> bool:
        """Check if crawl job can be started."""
        return self == CrawlStatus.PENDING

    @property
    def is_terminal(self) -> bool:
        """Check if status is terminal (cannot change)."""
        return self in (
            CrawlStatus.COMPLETED,
            CrawlStatus.FAILED,
            CrawlStatus.CANCELLED,
        )

    @property
    def can_cancel(self) -> bool:
        """Check if crawl job can be cancelled."""
        return self in (CrawlStatus.PENDING, CrawlStatus.IN_PROGRESS)


class DiscoveredUrlStatus(enum.StrEnum):
    """Status of a discovered URL during crawling."""

    PENDING = "pending"
    INGESTED = "ingested"
    SKIPPED = "skipped"
    FAILED = "failed"

    @property
    def is_processable(self) -> bool:
        """Check if URL can be processed."""
        return self == DiscoveredUrlStatus.PENDING
