"""Tests for crawl handlers."""

from unittest import mock

import pytest

from src import exceptions
from src.crawl.domain import model
from src.crawl.domain.status import CrawlStatus, DiscoveredUrlStatus
from src.crawl.handler import handlers
from src.crawl.schema import command, query, response
from src.common import pagination


def _make_notebook_repo(
    notebook_exists: bool = True,
) -> mock.AsyncMock:
    repo = mock.AsyncMock()
    if notebook_exists:
        repo.find_by_id = mock.AsyncMock(
            return_value=mock.MagicMock(id="nb1", name="Test Notebook")
        )
    else:
        repo.find_by_id = mock.AsyncMock(return_value=None)
    return repo


def _make_crawl_repo(
    crawl_job: model.CrawlJob | None = None,
) -> mock.AsyncMock:
    repo = mock.AsyncMock()
    repo.find_by_id = mock.AsyncMock(return_value=crawl_job)
    repo.save = mock.AsyncMock(side_effect=lambda e: e)
    repo.list_discovered_urls = mock.AsyncMock(return_value=[])
    repo.list_by_notebook = mock.AsyncMock(
        return_value=pagination.PaginationSchema.create(
            items=[], total=0, page=1, size=10
        )
    )
    return repo


def _make_bg_crawl_service() -> mock.Mock:
    return mock.Mock()


class TestStartCrawlHandler:
    """Tests for StartCrawlHandler."""

    @pytest.mark.asyncio
    async def test_creates_crawl_job(self) -> None:
        # Arrange
        notebook_repo = _make_notebook_repo(notebook_exists=True)
        crawl_repo = _make_crawl_repo()
        bg_service = _make_bg_crawl_service()

        handler = handlers.StartCrawlHandler(
            notebook_repository=notebook_repo,
            crawl_repository=crawl_repo,
            background_crawl_service=bg_service,
        )
        cmd = command.StartCrawl(
            url="https://example.com",  # type: ignore[arg-type]
            max_depth=3,
            max_pages=100,
        )

        # Act
        result = await handler.handle("nb1", cmd)

        # Assert
        assert isinstance(result, response.CrawlJobId)
        assert len(result.id) == 32
        crawl_repo.save.assert_called_once()
        bg_service.trigger_crawl.assert_called_once()

        saved_job = crawl_repo.save.call_args[0][0]
        assert saved_job.notebook_id == "nb1"
        assert saved_job.seed_url == "https://example.com/"
        assert saved_job.max_depth == 3
        assert saved_job.max_pages == 100
        assert saved_job.status == CrawlStatus.PENDING

    @pytest.mark.asyncio
    async def test_raises_not_found_for_missing_notebook(self) -> None:
        # Arrange
        notebook_repo = _make_notebook_repo(notebook_exists=False)
        crawl_repo = _make_crawl_repo()
        bg_service = _make_bg_crawl_service()

        handler = handlers.StartCrawlHandler(
            notebook_repository=notebook_repo,
            crawl_repository=crawl_repo,
            background_crawl_service=bg_service,
        )
        cmd = command.StartCrawl(url="https://example.com")  # type: ignore[arg-type]

        # Act & Assert
        with pytest.raises(exceptions.NotFoundError):
            await handler.handle("nonexistent", cmd)

    @pytest.mark.asyncio
    async def test_passes_url_patterns(self) -> None:
        # Arrange
        notebook_repo = _make_notebook_repo(notebook_exists=True)
        crawl_repo = _make_crawl_repo()
        bg_service = _make_bg_crawl_service()

        handler = handlers.StartCrawlHandler(
            notebook_repository=notebook_repo,
            crawl_repository=crawl_repo,
            background_crawl_service=bg_service,
        )
        cmd = command.StartCrawl(
            url="https://example.com",  # type: ignore[arg-type]
            url_include_pattern=r"/docs/.*",
            url_exclude_pattern=r".*\.pdf$",
        )

        # Act
        await handler.handle("nb1", cmd)

        # Assert
        saved_job = crawl_repo.save.call_args[0][0]
        assert saved_job.url_include_pattern == r"/docs/.*"
        assert saved_job.url_exclude_pattern == r".*\.pdf$"


class TestGetCrawlJobHandler:
    """Tests for GetCrawlJobHandler."""

    @pytest.mark.asyncio
    async def test_returns_crawl_job_detail(self) -> None:
        # Arrange
        job = model.CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
        )
        crawl_repo = _make_crawl_repo(crawl_job=job)

        handler = handlers.GetCrawlJobHandler(crawl_repository=crawl_repo)

        # Act
        result = await handler.handle(job.id)

        # Assert
        assert isinstance(result, response.CrawlJobDetail)
        assert result.id == job.id
        assert result.seed_url == "https://example.com"
        assert result.discovered_urls is None

    @pytest.mark.asyncio
    async def test_includes_discovered_urls(self) -> None:
        # Arrange
        job = model.CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
        )
        discovered = [
            model.DiscoveredUrl(
                url="https://example.com/page1",
                depth=1,
                status=DiscoveredUrlStatus.INGESTED,
                document_id="doc1",
            )
        ]
        crawl_repo = _make_crawl_repo(crawl_job=job)
        crawl_repo.list_discovered_urls = mock.AsyncMock(
            return_value=discovered
        )

        handler = handlers.GetCrawlJobHandler(crawl_repository=crawl_repo)

        # Act
        result = await handler.handle(job.id, include_urls=True)

        # Assert
        assert result.discovered_urls is not None
        assert len(result.discovered_urls) == 1
        assert result.discovered_urls[0].url == "https://example.com/page1"

    @pytest.mark.asyncio
    async def test_raises_not_found(self) -> None:
        # Arrange
        crawl_repo = _make_crawl_repo(crawl_job=None)
        handler = handlers.GetCrawlJobHandler(crawl_repository=crawl_repo)

        # Act & Assert
        with pytest.raises(exceptions.NotFoundError):
            await handler.handle("nonexistent")


class TestListCrawlJobsHandler:
    """Tests for ListCrawlJobsHandler."""

    @pytest.mark.asyncio
    async def test_returns_paginated_list(self) -> None:
        # Arrange
        notebook_repo = _make_notebook_repo(notebook_exists=True)
        crawl_repo = _make_crawl_repo()
        handler = handlers.ListCrawlJobsHandler(
            notebook_repository=notebook_repo,
            crawl_repository=crawl_repo,
        )
        qry = query.ListCrawlJobs(notebook_id="nb1")

        # Act
        result = await handler.handle("nb1", qry)

        # Assert
        assert isinstance(result, pagination.PaginationSchema)
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_raises_not_found_for_missing_notebook(self) -> None:
        # Arrange
        notebook_repo = _make_notebook_repo(notebook_exists=False)
        crawl_repo = _make_crawl_repo()
        handler = handlers.ListCrawlJobsHandler(
            notebook_repository=notebook_repo,
            crawl_repository=crawl_repo,
        )
        qry = query.ListCrawlJobs(notebook_id="nonexistent")

        # Act & Assert
        with pytest.raises(exceptions.NotFoundError):
            await handler.handle("nonexistent", qry)


class TestCancelCrawlHandler:
    """Tests for CancelCrawlHandler."""

    @pytest.mark.asyncio
    async def test_cancels_pending_job(self) -> None:
        # Arrange
        job = model.CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
        )
        crawl_repo = _make_crawl_repo(crawl_job=job)
        handler = handlers.CancelCrawlHandler(crawl_repository=crawl_repo)

        # Act
        await handler.handle(job.id)

        # Assert
        saved_job = crawl_repo.save.call_args[0][0]
        assert saved_job.status == CrawlStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_raises_not_found(self) -> None:
        # Arrange
        crawl_repo = _make_crawl_repo(crawl_job=None)
        handler = handlers.CancelCrawlHandler(crawl_repository=crawl_repo)

        # Act & Assert
        with pytest.raises(exceptions.NotFoundError):
            await handler.handle("nonexistent")

    @pytest.mark.asyncio
    async def test_raises_invalid_state_for_completed_job(self) -> None:
        # Arrange
        job = model.CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
        )
        completed = job.mark_in_progress().mark_completed()
        crawl_repo = _make_crawl_repo(crawl_job=completed)
        handler = handlers.CancelCrawlHandler(crawl_repository=crawl_repo)

        # Act & Assert
        with pytest.raises(exceptions.InvalidStateError):
            await handler.handle(completed.id)
