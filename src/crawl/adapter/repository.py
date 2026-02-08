"""Crawl job repository implementation."""

import sqlalchemy
import sqlalchemy.ext.asyncio

from src.common import pagination
from src.crawl.domain import mapper as crawl_mapper_module
from src.crawl.domain import model
from src.crawl.domain import status as crawl_status_module
from src.infrastructure.models import crawl as crawl_schema


class CrawlJobRepository:
    """Repository for CrawlJob persistence."""

    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        self._session = session
        self._job_mapper = crawl_mapper_module.CrawlJobMapper()
        self._url_mapper = crawl_mapper_module.DiscoveredUrlMapper()

    async def find_by_id(self, id: str) -> model.CrawlJob | None:
        """Find crawl job by ID."""
        stmt = sqlalchemy.select(crawl_schema.CrawlJobSchema).where(
            crawl_schema.CrawlJobSchema.id == id
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return self._job_mapper.to_entity(record)

    async def save(self, entity: model.CrawlJob) -> model.CrawlJob:
        """Save crawl job (insert or update)."""
        record = self._job_mapper.to_record(entity)
        merged = await self._session.merge(record)
        await self._session.flush()
        return self._job_mapper.to_entity(merged)

    async def delete(self, id: str) -> bool:
        """Delete crawl job by ID (cascades to discovered URLs)."""
        stmt = sqlalchemy.delete(crawl_schema.CrawlJobSchema).where(
            crawl_schema.CrawlJobSchema.id == id
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0

    async def list_by_notebook(
        self, notebook_id: str, query: pagination.ListQuery
    ) -> pagination.PaginationSchema[model.CrawlJob]:
        """List crawl jobs for a notebook with pagination."""
        count_stmt = (
            sqlalchemy.select(sqlalchemy.func.count())
            .select_from(crawl_schema.CrawlJobSchema)
            .where(crawl_schema.CrawlJobSchema.notebook_id == notebook_id)
        )
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = (
            sqlalchemy.select(crawl_schema.CrawlJobSchema)
            .where(crawl_schema.CrawlJobSchema.notebook_id == notebook_id)
            .order_by(crawl_schema.CrawlJobSchema.created_at.desc())
            .offset(query.offset)
            .limit(query.size)
        )
        result = await self._session.execute(stmt)
        records = result.scalars().all()

        items = [self._job_mapper.to_entity(record) for record in records]
        return pagination.PaginationSchema.create(
            items=items,
            total=total,
            page=query.page,
            size=query.size,
        )

    async def save_discovered_url(
        self, crawl_job_id: str, entity: model.DiscoveredUrl
    ) -> model.DiscoveredUrl:
        """Save a discovered URL record."""
        record = self._url_mapper.to_record(
            entity=entity, crawl_job_id=crawl_job_id
        )
        merged = await self._session.merge(record)
        await self._session.flush()
        return self._url_mapper.to_entity(merged)

    async def save_discovered_urls_batch(
        self, crawl_job_id: str, entities: list[model.DiscoveredUrl]
    ) -> list[model.DiscoveredUrl]:
        """Save multiple discovered URLs in a batch."""
        results: list[model.DiscoveredUrl] = []
        for entity in entities:
            saved = await self.save_discovered_url(crawl_job_id, entity)
            results.append(saved)
        return results

    async def list_discovered_urls(
        self,
        crawl_job_id: str,
        status: crawl_status_module.DiscoveredUrlStatus | None = None,
    ) -> list[model.DiscoveredUrl]:
        """List discovered URLs for a crawl job, optionally filtered by status."""
        stmt = sqlalchemy.select(crawl_schema.DiscoveredUrlSchema).where(
            crawl_schema.DiscoveredUrlSchema.crawl_job_id == crawl_job_id
        )
        if status is not None:
            stmt = stmt.where(
                crawl_schema.DiscoveredUrlSchema.status == status.value
            )
        stmt = stmt.order_by(crawl_schema.DiscoveredUrlSchema.depth.asc())

        result = await self._session.execute(stmt)
        records = result.scalars().all()
        return [self._url_mapper.to_entity(record) for record in records]

    async def find_discovered_url_by_crawl_and_url(
        self, crawl_job_id: str, url: str
    ) -> model.DiscoveredUrl | None:
        """Find a discovered URL by crawl job ID and URL."""
        stmt = sqlalchemy.select(crawl_schema.DiscoveredUrlSchema).where(
            crawl_schema.DiscoveredUrlSchema.crawl_job_id == crawl_job_id,
            crawl_schema.DiscoveredUrlSchema.url == url,
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return self._url_mapper.to_entity(record)
