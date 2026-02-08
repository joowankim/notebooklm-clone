"""Crawl execution service - BFS traversal and document creation."""

import asyncio
import collections
import logging

from src.crawl.adapter import repository as crawl_repo_module
from src.crawl.domain import model
from src.crawl.service import link_discovery as link_discovery_module
from src.document.adapter import repository as doc_repo_module
from src.document.domain import model as doc_model
from src.document.service import ingestion_pipeline as ingestion_module

logger = logging.getLogger(__name__)


class CrawlService:
    """Orchestrates BFS crawling and document creation."""

    def __init__(
        self,
        crawl_repository: crawl_repo_module.CrawlJobRepository,
        document_repository: doc_repo_module.DocumentRepository,
        link_discovery: link_discovery_module.LinkDiscoveryService,
        background_ingestion: ingestion_module.BackgroundIngestionService,
    ) -> None:
        self._crawl_repository = crawl_repository
        self._document_repository = document_repository
        self._link_discovery = link_discovery
        self._background_ingestion = background_ingestion

    async def execute(self, crawl_job_id: str) -> model.CrawlJob:
        """Execute a crawl job using BFS traversal."""
        job = await self._crawl_repository.find_by_id(crawl_job_id)
        if job is None:
            raise ValueError(f"CrawlJob not found: {crawl_job_id}")

        job = job.mark_in_progress()
        job = await self._crawl_repository.save(job)

        try:
            job = await self._bfs_crawl(job)
            job = job.mark_completed()
        except Exception as exc:
            logger.error(f"Crawl failed for {crawl_job_id}: {exc}")
            job = job.mark_failed(str(exc))

        job = await self._crawl_repository.save(job)
        return job

    async def _bfs_crawl(self, job: model.CrawlJob) -> model.CrawlJob:
        """Perform BFS traversal starting from the seed URL."""
        visited: set[str] = set()
        queue: collections.deque[tuple[str, int]] = collections.deque()
        queue.append((job.seed_url, 0))
        pages_created = 0

        while queue and pages_created < job.max_pages:
            url, depth = queue.popleft()

            if url in visited:
                continue
            if depth > job.max_depth:
                continue

            visited.add(url)

            # Create document for this URL
            created = await self._create_document_if_new(
                notebook_id=job.notebook_id,
                url=url,
                crawl_job_id=job.id,
                depth=depth,
            )

            if created:
                pages_created += 1
                job = job.increment_discovered()
                job = job.increment_ingested()

                if pages_created >= job.max_pages:
                    break

            # Discover links if not at max depth
            if depth < job.max_depth:
                new_links = await self._discover_links_safe(
                    url=url,
                    job=job,
                )
                for link in new_links:
                    if link.url not in visited:
                        queue.append((link.url, depth + 1))

        return job

    async def _create_document_if_new(
        self,
        notebook_id: str,
        url: str,
        crawl_job_id: str,
        depth: int,
    ) -> bool:
        """Create a document if it doesn't already exist in the notebook."""
        existing = await self._document_repository.find_by_notebook_and_url(
            notebook_id, url
        )
        if existing is not None:
            # URL already exists - record as skipped
            discovered = model.DiscoveredUrl.create(url=url, depth=depth)
            discovered = discovered.mark_skipped()
            await self._crawl_repository.save_discovered_url(
                crawl_job_id, discovered
            )
            return False

        # Create new document
        document = doc_model.Document.create(
            notebook_id=notebook_id,
            url=url,
        )
        saved_doc = await self._document_repository.save(document)

        # Trigger background ingestion
        self._background_ingestion.trigger_ingestion(saved_doc)

        # Record discovered URL
        discovered = model.DiscoveredUrl.create(url=url, depth=depth)
        discovered = discovered.mark_ingested(document_id=saved_doc.id)
        await self._crawl_repository.save_discovered_url(
            crawl_job_id, discovered
        )

        return True

    async def _discover_links_safe(
        self,
        url: str,
        job: model.CrawlJob,
    ) -> list[model.DiscoveredLink]:
        """Discover links on a page, handling errors gracefully."""
        try:
            return await self._link_discovery.discover_links(
                url=url,
                domain=job.domain,
                include_pattern=job.url_include_pattern,
                exclude_pattern=job.url_exclude_pattern,
            )
        except Exception as exc:
            logger.warning(f"Failed to discover links on {url}: {exc}")
            return []


class BackgroundCrawlService:
    """Service for triggering background crawl jobs."""

    def __init__(self, crawl_service: CrawlService) -> None:
        self._crawl_service = crawl_service
        self._tasks: dict[str, asyncio.Task] = {}  # type: ignore[type-arg]

    def trigger_crawl(self, crawl_job: model.CrawlJob) -> None:
        """Trigger async crawl job in the background."""
        if crawl_job.id in self._tasks:
            return

        task = asyncio.create_task(
            self._process_with_cleanup(crawl_job.id)
        )
        self._tasks[crawl_job.id] = task

    async def _process_with_cleanup(self, crawl_job_id: str) -> None:
        """Execute crawl and clean up task reference."""
        try:
            await self._crawl_service.execute(crawl_job_id)
        except Exception as exc:
            logger.error(f"Background crawl error for {crawl_job_id}: {exc}")
        finally:
            self._tasks.pop(crawl_job_id, None)

    def is_crawling(self, crawl_job_id: str) -> bool:
        """Check if a crawl job is currently running."""
        return crawl_job_id in self._tasks
