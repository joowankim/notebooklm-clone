"""Crawl response schemas (output DTOs)."""

import datetime
from typing import Self

import pydantic

from src.crawl.domain import model


class CrawlJobId(pydantic.BaseModel):
    """Response containing crawl job ID."""

    id: str


class DiscoveredUrlDetail(pydantic.BaseModel):
    """Detail of a discovered URL."""

    url: str
    depth: int
    status: str
    document_id: str | None

    @classmethod
    def from_entity(cls, entity: model.DiscoveredUrl) -> Self:
        """Create response from domain value object."""
        return cls(
            url=entity.url,
            depth=entity.depth,
            status=entity.status.value,
            document_id=entity.document_id,
        )


class CrawlJobDetail(pydantic.BaseModel):
    """Detailed crawl job response."""

    id: str
    notebook_id: str
    seed_url: str
    domain: str
    max_depth: int
    max_pages: int
    url_include_pattern: str | None
    url_exclude_pattern: str | None
    status: str
    total_discovered: int
    total_ingested: int
    error_message: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    discovered_urls: list[DiscoveredUrlDetail] | None = None

    @classmethod
    def from_entity(
        cls,
        entity: model.CrawlJob,
        discovered_urls: list[model.DiscoveredUrl] | None = None,
    ) -> Self:
        """Create response from domain entity."""
        url_details = None
        if discovered_urls is not None:
            url_details = [
                DiscoveredUrlDetail.from_entity(u) for u in discovered_urls
            ]

        return cls(
            id=entity.id,
            notebook_id=entity.notebook_id,
            seed_url=entity.seed_url,
            domain=entity.domain,
            max_depth=entity.max_depth,
            max_pages=entity.max_pages,
            url_include_pattern=entity.url_include_pattern,
            url_exclude_pattern=entity.url_exclude_pattern,
            status=entity.status.value,
            total_discovered=entity.total_discovered,
            total_ingested=entity.total_ingested,
            error_message=entity.error_message,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            discovered_urls=url_details,
        )
