"""Tests for BackgroundCrawlService.wait_for_all()."""

import asyncio
from unittest import mock

import pytest

from src.crawl.service import crawl_service as crawl_service_module


@pytest.fixture
def mock_crawl_service() -> mock.MagicMock:
    """Create a mock CrawlService."""
    return mock.MagicMock(spec=crawl_service_module.CrawlService)


@pytest.fixture
def mock_crawl_job() -> mock.MagicMock:
    """Create a mock CrawlJob."""
    job = mock.MagicMock()
    job.id = "job-1"
    return job


class TestBackgroundCrawlServiceWaitForAll:
    """Tests for BackgroundCrawlService.wait_for_all() method."""

    @pytest.mark.asyncio
    async def test_wait_for_all_with_no_tasks(
        self, mock_crawl_service: mock.MagicMock
    ) -> None:
        """wait_for_all should return immediately when no tasks are pending."""
        service = crawl_service_module.BackgroundCrawlService(
            crawl_service=mock_crawl_service
        )

        await service.wait_for_all()

    @pytest.mark.asyncio
    async def test_wait_for_all_waits_for_pending_tasks(
        self, mock_crawl_service: mock.MagicMock
    ) -> None:
        """wait_for_all should block until all pending crawl tasks complete."""
        completed: list[str] = []

        async def slow_execute(job_id: str) -> None:
            await asyncio.sleep(0.05)
            completed.append(job_id)
            return None

        mock_crawl_service.execute = mock.AsyncMock(side_effect=slow_execute)
        service = crawl_service_module.BackgroundCrawlService(
            crawl_service=mock_crawl_service
        )

        job1 = mock.MagicMock()
        job1.id = "job-1"
        job2 = mock.MagicMock()
        job2.id = "job-2"

        service.trigger_crawl(job1)
        service.trigger_crawl(job2)

        assert service.is_crawling("job-1")
        assert service.is_crawling("job-2")

        await service.wait_for_all()

        assert "job-1" in completed
        assert "job-2" in completed

    @pytest.mark.asyncio
    async def test_wait_for_all_handles_task_exceptions(
        self, mock_crawl_service: mock.MagicMock
    ) -> None:
        """wait_for_all should not raise even if crawl tasks fail."""
        mock_crawl_service.execute = mock.AsyncMock(
            side_effect=RuntimeError("crawl failed")
        )
        service = crawl_service_module.BackgroundCrawlService(
            crawl_service=mock_crawl_service
        )

        job = mock.MagicMock()
        job.id = "job-fail"

        service.trigger_crawl(job)
        await service.wait_for_all()

    @pytest.mark.asyncio
    async def test_wait_for_all_clears_tasks_after_completion(
        self, mock_crawl_service: mock.MagicMock
    ) -> None:
        """Tasks should be cleaned up after wait_for_all completes."""
        mock_crawl_service.execute = mock.AsyncMock(return_value=None)
        service = crawl_service_module.BackgroundCrawlService(
            crawl_service=mock_crawl_service
        )

        job = mock.MagicMock()
        job.id = "job-cleanup"

        service.trigger_crawl(job)
        await service.wait_for_all()

        assert not service.is_crawling("job-cleanup")
