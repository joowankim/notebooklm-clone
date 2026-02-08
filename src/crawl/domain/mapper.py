"""Mapper between crawl domain entities and ORM schemas."""

import uuid

from src.crawl.domain import model
from src.crawl.domain.status import CrawlStatus, DiscoveredUrlStatus
from src.infrastructure.models import crawl as crawl_schema


class CrawlJobMapper:
    """Maps between CrawlJob domain entity and ORM schema."""

    @staticmethod
    def to_entity(record: crawl_schema.CrawlJobSchema) -> model.CrawlJob:
        """Convert ORM record to domain entity."""
        return model.CrawlJob(
            id=record.id,
            notebook_id=record.notebook_id,
            seed_url=record.seed_url,
            domain=record.domain,
            max_depth=record.max_depth,
            max_pages=record.max_pages,
            url_include_pattern=record.url_include_pattern,
            url_exclude_pattern=record.url_exclude_pattern,
            status=CrawlStatus(record.status),
            total_discovered=record.total_discovered,
            total_ingested=record.total_ingested,
            error_message=record.error_message,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def to_record(entity: model.CrawlJob) -> crawl_schema.CrawlJobSchema:
        """Convert domain entity to ORM record."""
        return crawl_schema.CrawlJobSchema(
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
        )


class DiscoveredUrlMapper:
    """Maps between DiscoveredUrl value object and ORM schema."""

    @staticmethod
    def to_entity(record: crawl_schema.DiscoveredUrlSchema) -> model.DiscoveredUrl:
        """Convert ORM record to domain value object."""
        return model.DiscoveredUrl(
            url=record.url,
            depth=record.depth,
            status=DiscoveredUrlStatus(record.status),
            document_id=record.document_id,
        )

    @staticmethod
    def to_record(
        entity: model.DiscoveredUrl,
        crawl_job_id: str,
    ) -> crawl_schema.DiscoveredUrlSchema:
        """Convert domain value object to ORM record."""
        return crawl_schema.DiscoveredUrlSchema(
            id=uuid.uuid4().hex,
            crawl_job_id=crawl_job_id,
            url=entity.url,
            depth=entity.depth,
            status=entity.status.value,
            document_id=entity.document_id,
        )
