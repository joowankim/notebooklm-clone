"""Tests for crawl execution service."""

import asyncio
from unittest import mock

import pytest

from src.crawl.domain import model
from src.crawl.domain.status import CrawlStatus
from src.crawl.service.crawl_service import CrawlService


def _make_mock_crawl_repo(job: model.CrawlJob) -> mock.AsyncMock:
    """Create a mock crawl repository that tracks saves."""
    repo = mock.AsyncMock()
    repo.find_by_id = mock.AsyncMock(return_value=job)

    saved_jobs: list[model.CrawlJob] = []

    async def mock_save(entity: model.CrawlJob) -> model.CrawlJob:
        saved_jobs.append(entity)
        return entity

    repo.save = mock.AsyncMock(side_effect=mock_save)
    repo.save_discovered_url = mock.AsyncMock(
        side_effect=lambda cid, e: e
    )
    repo.find_discovered_url_by_crawl_and_url = mock.AsyncMock(
        return_value=None
    )
    repo._saved_jobs = saved_jobs
    return repo


def _make_mock_doc_repo() -> mock.AsyncMock:
    """Create a mock document repository."""
    repo = mock.AsyncMock()
    repo.find_by_notebook_and_url = mock.AsyncMock(return_value=None)

    async def mock_save(entity: mock.ANY) -> mock.ANY:
        return entity

    repo.save = mock.AsyncMock(side_effect=mock_save)
    return repo


def _make_mock_link_discovery(
    link_map: dict[str, list[model.DiscoveredLink]],
) -> mock.AsyncMock:
    """Create a mock link discovery service with predefined link maps."""
    service = mock.AsyncMock()

    async def mock_discover(
        url: str, domain: str, **kwargs: mock.ANY
    ) -> list[model.DiscoveredLink]:
        return link_map.get(url, [])

    service.discover_links = mock.AsyncMock(side_effect=mock_discover)
    return service


def _make_mock_background_ingestion() -> mock.Mock:
    """Create a mock background ingestion service."""
    service = mock.Mock()
    service.trigger_ingestion = mock.Mock()
    return service


class TestCrawlService:
    """Tests for CrawlService.execute."""

    @pytest.mark.asyncio
    async def test_crawls_seed_url(self) -> None:
        # Arrange
        job = model.CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
            max_depth=1,
            max_pages=10,
        )
        crawl_repo = _make_mock_crawl_repo(job)
        doc_repo = _make_mock_doc_repo()
        link_discovery = _make_mock_link_discovery({})
        bg_ingestion = _make_mock_background_ingestion()

        service = CrawlService(
            crawl_repository=crawl_repo,
            document_repository=doc_repo,
            link_discovery=link_discovery,
            background_ingestion=bg_ingestion,
        )

        # Act
        result = await service.execute(job.id)

        # Assert
        assert result.status == CrawlStatus.COMPLETED
        assert result.total_discovered >= 1
        # Seed URL should be created as document
        assert doc_repo.save.call_count == 1

    @pytest.mark.asyncio
    async def test_discovers_nested_links(self) -> None:
        # Arrange
        job = model.CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
            max_depth=2,
            max_pages=50,
        )
        link_map = {
            "https://example.com": [
                model.DiscoveredLink(url="https://example.com/page1", anchor_text="P1"),
                model.DiscoveredLink(url="https://example.com/page2", anchor_text="P2"),
            ],
            "https://example.com/page1": [
                model.DiscoveredLink(url="https://example.com/page1/sub", anchor_text="Sub"),
            ],
            "https://example.com/page2": [],
        }
        crawl_repo = _make_mock_crawl_repo(job)
        doc_repo = _make_mock_doc_repo()
        link_discovery = _make_mock_link_discovery(link_map)
        bg_ingestion = _make_mock_background_ingestion()

        service = CrawlService(
            crawl_repository=crawl_repo,
            document_repository=doc_repo,
            link_discovery=link_discovery,
            background_ingestion=bg_ingestion,
        )

        # Act
        result = await service.execute(job.id)

        # Assert
        assert result.status == CrawlStatus.COMPLETED
        # seed + page1 + page2 + page1/sub = 4
        assert doc_repo.save.call_count == 4

    @pytest.mark.asyncio
    async def test_respects_max_depth(self) -> None:
        # Arrange
        job = model.CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
            max_depth=1,
            max_pages=50,
        )
        link_map = {
            "https://example.com": [
                model.DiscoveredLink(url="https://example.com/page1", anchor_text=None),
            ],
            "https://example.com/page1": [
                model.DiscoveredLink(url="https://example.com/page1/deep", anchor_text=None),
            ],
        }
        crawl_repo = _make_mock_crawl_repo(job)
        doc_repo = _make_mock_doc_repo()
        link_discovery = _make_mock_link_discovery(link_map)
        bg_ingestion = _make_mock_background_ingestion()

        service = CrawlService(
            crawl_repository=crawl_repo,
            document_repository=doc_repo,
            link_discovery=link_discovery,
            background_ingestion=bg_ingestion,
        )

        # Act
        result = await service.execute(job.id)

        # Assert
        # seed(depth=0) + page1(depth=1) = 2
        # page1/deep would be depth=2, exceeding max_depth=1
        assert doc_repo.save.call_count == 2

    @pytest.mark.asyncio
    async def test_respects_max_pages(self) -> None:
        # Arrange
        job = model.CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
            max_depth=5,
            max_pages=3,
        )
        link_map = {
            "https://example.com": [
                model.DiscoveredLink(url="https://example.com/p1", anchor_text=None),
                model.DiscoveredLink(url="https://example.com/p2", anchor_text=None),
                model.DiscoveredLink(url="https://example.com/p3", anchor_text=None),
                model.DiscoveredLink(url="https://example.com/p4", anchor_text=None),
            ],
        }
        crawl_repo = _make_mock_crawl_repo(job)
        doc_repo = _make_mock_doc_repo()
        link_discovery = _make_mock_link_discovery(link_map)
        bg_ingestion = _make_mock_background_ingestion()

        service = CrawlService(
            crawl_repository=crawl_repo,
            document_repository=doc_repo,
            link_discovery=link_discovery,
            background_ingestion=bg_ingestion,
        )

        # Act
        result = await service.execute(job.id)

        # Assert - max_pages=3, so only 3 docs created
        assert doc_repo.save.call_count == 3

    @pytest.mark.asyncio
    async def test_skips_already_existing_documents(self) -> None:
        # Arrange
        job = model.CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
            max_depth=1,
            max_pages=50,
        )
        link_map = {
            "https://example.com": [
                model.DiscoveredLink(url="https://example.com/existing", anchor_text=None),
            ],
        }
        crawl_repo = _make_mock_crawl_repo(job)
        doc_repo = _make_mock_doc_repo()
        # Mark "existing" as already in notebook
        doc_repo.find_by_notebook_and_url = mock.AsyncMock(
            side_effect=lambda nb_id, url: (
                mock.MagicMock(id="existing_doc") if url == "https://example.com/existing" else None
            )
        )
        link_discovery = _make_mock_link_discovery(link_map)
        bg_ingestion = _make_mock_background_ingestion()

        service = CrawlService(
            crawl_repository=crawl_repo,
            document_repository=doc_repo,
            link_discovery=link_discovery,
            background_ingestion=bg_ingestion,
        )

        # Act
        result = await service.execute(job.id)

        # Assert - seed doc created, but existing URL skipped
        assert doc_repo.save.call_count == 1

    @pytest.mark.asyncio
    async def test_handles_link_discovery_error(self) -> None:
        # Arrange
        job = model.CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
            max_depth=1,
            max_pages=50,
        )
        crawl_repo = _make_mock_crawl_repo(job)
        doc_repo = _make_mock_doc_repo()
        link_discovery = mock.AsyncMock()
        link_discovery.discover_links = mock.AsyncMock(
            side_effect=Exception("Network error")
        )
        bg_ingestion = _make_mock_background_ingestion()

        service = CrawlService(
            crawl_repository=crawl_repo,
            document_repository=doc_repo,
            link_discovery=link_discovery,
            background_ingestion=bg_ingestion,
        )

        # Act - should not raise, but complete with what it has
        result = await service.execute(job.id)

        # Assert - should still complete (seed doc was created before link discovery)
        assert result.status == CrawlStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_avoids_cycles(self) -> None:
        # Arrange
        job = model.CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
            max_depth=3,
            max_pages=50,
        )
        # Circular: A -> B -> A
        link_map = {
            "https://example.com": [
                model.DiscoveredLink(url="https://example.com/page1", anchor_text=None),
            ],
            "https://example.com/page1": [
                model.DiscoveredLink(url="https://example.com", anchor_text=None),
            ],
        }
        crawl_repo = _make_mock_crawl_repo(job)
        doc_repo = _make_mock_doc_repo()
        link_discovery = _make_mock_link_discovery(link_map)
        bg_ingestion = _make_mock_background_ingestion()

        service = CrawlService(
            crawl_repository=crawl_repo,
            document_repository=doc_repo,
            link_discovery=link_discovery,
            background_ingestion=bg_ingestion,
        )

        # Act
        result = await service.execute(job.id)

        # Assert - should only process each URL once
        assert doc_repo.save.call_count == 2
        assert result.status == CrawlStatus.COMPLETED
