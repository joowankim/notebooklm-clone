"""Crawl command/query handlers."""

from src import exceptions
from src.common import pagination
from src.crawl.adapter import repository as crawl_repo_module
from src.crawl.domain import model
from src.crawl.schema import command, query, response
from src.crawl.service import crawl_service as crawl_service_module
from src.notebook.adapter import repository as notebook_repo_module


class StartCrawlHandler:
    """Handle starting a new crawl job."""

    def __init__(
        self,
        notebook_repository: notebook_repo_module.NotebookRepository,
        crawl_repository: crawl_repo_module.CrawlJobRepository,
        background_crawl_service: crawl_service_module.BackgroundCrawlService,
    ) -> None:
        self._notebook_repository = notebook_repository
        self._crawl_repository = crawl_repository
        self._background_crawl_service = background_crawl_service

    async def handle(
        self, notebook_id: str, cmd: command.StartCrawl
    ) -> response.CrawlJobId:
        """Start a crawl job for a notebook."""
        notebook = await self._notebook_repository.find_by_id(notebook_id)
        if notebook is None:
            raise exceptions.NotFoundError(
                f"Notebook not found: {notebook_id}"
            )

        crawl_job = model.CrawlJob.create(
            notebook_id=notebook_id,
            seed_url=str(cmd.url),
            max_depth=cmd.max_depth,
            max_pages=cmd.max_pages,
            url_include_pattern=cmd.url_include_pattern,
            url_exclude_pattern=cmd.url_exclude_pattern,
        )
        saved = await self._crawl_repository.save(crawl_job)

        self._background_crawl_service.trigger_crawl(saved)

        return response.CrawlJobId(id=saved.id)


class GetCrawlJobHandler:
    """Handle retrieving a crawl job's details."""

    def __init__(
        self,
        crawl_repository: crawl_repo_module.CrawlJobRepository,
    ) -> None:
        self._crawl_repository = crawl_repository

    async def handle(
        self, crawl_job_id: str, include_urls: bool = False
    ) -> response.CrawlJobDetail:
        """Get crawl job details."""
        crawl_job = await self._crawl_repository.find_by_id(crawl_job_id)
        if crawl_job is None:
            raise exceptions.NotFoundError(
                f"Crawl job not found: {crawl_job_id}"
            )

        discovered_urls = None
        if include_urls:
            discovered_urls = (
                await self._crawl_repository.list_discovered_urls(crawl_job_id)
            )

        return response.CrawlJobDetail.from_entity(
            crawl_job, discovered_urls=discovered_urls
        )


class ListCrawlJobsHandler:
    """Handle listing crawl jobs for a notebook."""

    def __init__(
        self,
        notebook_repository: notebook_repo_module.NotebookRepository,
        crawl_repository: crawl_repo_module.CrawlJobRepository,
    ) -> None:
        self._notebook_repository = notebook_repository
        self._crawl_repository = crawl_repository

    async def handle(
        self, notebook_id: str, qry: query.ListCrawlJobs
    ) -> pagination.PaginationSchema[response.CrawlJobDetail]:
        """List crawl jobs for a notebook."""
        notebook = await self._notebook_repository.find_by_id(notebook_id)
        if notebook is None:
            raise exceptions.NotFoundError(
                f"Notebook not found: {notebook_id}"
            )

        result = await self._crawl_repository.list_by_notebook(
            notebook_id, qry
        )

        items = [
            response.CrawlJobDetail.from_entity(job) for job in result.items
        ]
        return pagination.PaginationSchema.create(
            items=items,
            total=result.total,
            page=result.page,
            size=result.size,
        )


class CancelCrawlHandler:
    """Handle cancelling a crawl job."""

    def __init__(
        self,
        crawl_repository: crawl_repo_module.CrawlJobRepository,
    ) -> None:
        self._crawl_repository = crawl_repository

    async def handle(self, crawl_job_id: str) -> None:
        """Cancel a crawl job."""
        crawl_job = await self._crawl_repository.find_by_id(crawl_job_id)
        if crawl_job is None:
            raise exceptions.NotFoundError(
                f"Crawl job not found: {crawl_job_id}"
            )

        cancelled = crawl_job.mark_cancelled()
        await self._crawl_repository.save(cancelled)
