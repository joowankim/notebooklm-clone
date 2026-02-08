"""Tests for crawl domain models."""

import pytest

from src.crawl.domain.model import CrawlJob, DiscoveredUrl
from src.crawl.domain.status import CrawlStatus, DiscoveredUrlStatus
from src import exceptions


class TestCrawlStatus:
    """Tests for CrawlStatus enum."""

    def test_pending_is_processable(self) -> None:
        # Arrange & Act & Assert
        assert CrawlStatus.PENDING.is_processable is True

    def test_in_progress_is_not_processable(self) -> None:
        assert CrawlStatus.IN_PROGRESS.is_processable is False

    def test_completed_is_terminal(self) -> None:
        assert CrawlStatus.COMPLETED.is_terminal is True

    def test_failed_is_terminal(self) -> None:
        assert CrawlStatus.FAILED.is_terminal is True

    def test_pending_is_not_terminal(self) -> None:
        assert CrawlStatus.PENDING.is_terminal is False

    def test_in_progress_is_not_terminal(self) -> None:
        assert CrawlStatus.IN_PROGRESS.is_terminal is False

    def test_pending_can_cancel(self) -> None:
        assert CrawlStatus.PENDING.can_cancel is True

    def test_in_progress_can_cancel(self) -> None:
        assert CrawlStatus.IN_PROGRESS.can_cancel is True

    def test_completed_cannot_cancel(self) -> None:
        assert CrawlStatus.COMPLETED.can_cancel is False

    def test_cancelled_is_terminal(self) -> None:
        assert CrawlStatus.CANCELLED.is_terminal is True


class TestDiscoveredUrlStatus:
    """Tests for DiscoveredUrlStatus enum."""

    def test_pending_is_processable(self) -> None:
        assert DiscoveredUrlStatus.PENDING.is_processable is True

    def test_ingested_is_not_processable(self) -> None:
        assert DiscoveredUrlStatus.INGESTED.is_processable is False

    def test_skipped_is_not_processable(self) -> None:
        assert DiscoveredUrlStatus.SKIPPED.is_processable is False

    def test_failed_is_not_processable(self) -> None:
        assert DiscoveredUrlStatus.FAILED.is_processable is False


class TestDiscoveredUrl:
    """Tests for DiscoveredUrl value object."""

    def test_create(self) -> None:
        # Arrange & Act
        discovered = DiscoveredUrl.create(
            url="https://example.com/page",
            depth=1,
        )

        # Assert
        expected = DiscoveredUrl(
            url="https://example.com/page",
            depth=1,
            status=DiscoveredUrlStatus.PENDING,
            document_id=None,
        )
        assert discovered == expected

    def test_mark_ingested(self) -> None:
        # Arrange
        discovered = DiscoveredUrl.create(
            url="https://example.com/page",
            depth=0,
        )

        # Act
        ingested = discovered.mark_ingested(document_id="doc123")

        # Assert
        assert discovered.status == DiscoveredUrlStatus.PENDING
        assert ingested.status == DiscoveredUrlStatus.INGESTED
        assert ingested.document_id == "doc123"

    def test_mark_skipped(self) -> None:
        # Arrange
        discovered = DiscoveredUrl.create(
            url="https://example.com/page",
            depth=0,
        )

        # Act
        skipped = discovered.mark_skipped()

        # Assert
        assert discovered.status == DiscoveredUrlStatus.PENDING
        assert skipped.status == DiscoveredUrlStatus.SKIPPED

    def test_mark_failed(self) -> None:
        # Arrange
        discovered = DiscoveredUrl.create(
            url="https://example.com/page",
            depth=0,
        )

        # Act
        failed = discovered.mark_failed()

        # Assert
        assert discovered.status == DiscoveredUrlStatus.PENDING
        assert failed.status == DiscoveredUrlStatus.FAILED

    def test_immutability(self) -> None:
        # Arrange
        discovered = DiscoveredUrl.create(
            url="https://example.com/page",
            depth=0,
        )

        # Act & Assert
        with pytest.raises(Exception):
            discovered.url = "https://other.com"

    def test_equality_by_value(self) -> None:
        # Arrange
        url_a = DiscoveredUrl(
            url="https://example.com",
            depth=0,
            status=DiscoveredUrlStatus.PENDING,
            document_id=None,
        )
        url_b = DiscoveredUrl(
            url="https://example.com",
            depth=0,
            status=DiscoveredUrlStatus.PENDING,
            document_id=None,
        )

        # Assert
        assert url_a == url_b


class TestCrawlJob:
    """Tests for CrawlJob entity."""

    def test_create_with_defaults(self) -> None:
        # Arrange & Act
        job = CrawlJob.create(
            notebook_id="notebook123",
            seed_url="https://example.com",
        )

        # Assert
        assert len(job.id) == 32
        assert job.notebook_id == "notebook123"
        assert job.seed_url == "https://example.com"
        assert job.domain == "example.com"
        assert job.max_depth == 2
        assert job.max_pages == 50
        assert job.url_include_pattern is None
        assert job.url_exclude_pattern is None
        assert job.status == CrawlStatus.PENDING
        assert job.total_discovered == 0
        assert job.total_ingested == 0
        assert job.error_message is None

    def test_create_with_custom_params(self) -> None:
        # Arrange & Act
        job = CrawlJob.create(
            notebook_id="notebook123",
            seed_url="https://docs.example.com/guide",
            max_depth=3,
            max_pages=100,
            url_include_pattern=r"/guide/.*",
            url_exclude_pattern=r".*\.pdf$",
        )

        # Assert
        assert job.domain == "docs.example.com"
        assert job.max_depth == 3
        assert job.max_pages == 100
        assert job.url_include_pattern == r"/guide/.*"
        assert job.url_exclude_pattern == r".*\.pdf$"

    def test_create_extracts_domain_from_url(self) -> None:
        # Arrange & Act
        job = CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://sub.domain.example.com/path/to/page?q=1",
        )

        # Assert
        assert job.domain == "sub.domain.example.com"

    def test_create_rejects_invalid_max_depth(self) -> None:
        # Act & Assert
        with pytest.raises(exceptions.ValidationError):
            CrawlJob.create(
                notebook_id="nb1",
                seed_url="https://example.com",
                max_depth=0,
            )

    def test_create_rejects_invalid_max_pages(self) -> None:
        # Act & Assert
        with pytest.raises(exceptions.ValidationError):
            CrawlJob.create(
                notebook_id="nb1",
                seed_url="https://example.com",
                max_pages=0,
            )

    def test_mark_in_progress(self) -> None:
        # Arrange
        job = CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
        )

        # Act
        updated = job.mark_in_progress()

        # Assert
        assert job.status == CrawlStatus.PENDING
        assert updated.status == CrawlStatus.IN_PROGRESS

    def test_mark_in_progress_from_non_pending_raises(self) -> None:
        # Arrange
        job = CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
        )
        in_progress = job.mark_in_progress()

        # Act & Assert
        with pytest.raises(exceptions.InvalidStateError):
            in_progress.mark_in_progress()

    def test_mark_completed(self) -> None:
        # Arrange
        job = CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
        )
        in_progress = job.mark_in_progress()

        # Act
        completed = in_progress.mark_completed()

        # Assert
        assert completed.status == CrawlStatus.COMPLETED

    def test_mark_completed_from_pending_raises(self) -> None:
        # Arrange
        job = CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
        )

        # Act & Assert
        with pytest.raises(exceptions.InvalidStateError):
            job.mark_completed()

    def test_mark_failed(self) -> None:
        # Arrange
        job = CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
        )
        in_progress = job.mark_in_progress()

        # Act
        failed = in_progress.mark_failed("Connection timeout")

        # Assert
        assert failed.status == CrawlStatus.FAILED
        assert failed.error_message == "Connection timeout"

    def test_mark_failed_from_pending_raises(self) -> None:
        # Arrange
        job = CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
        )

        # Act & Assert
        with pytest.raises(exceptions.InvalidStateError):
            job.mark_failed("error")

    def test_mark_cancelled_from_pending(self) -> None:
        # Arrange
        job = CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
        )

        # Act
        cancelled = job.mark_cancelled()

        # Assert
        assert cancelled.status == CrawlStatus.CANCELLED

    def test_mark_cancelled_from_in_progress(self) -> None:
        # Arrange
        job = CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
        )
        in_progress = job.mark_in_progress()

        # Act
        cancelled = in_progress.mark_cancelled()

        # Assert
        assert cancelled.status == CrawlStatus.CANCELLED

    def test_mark_cancelled_from_completed_raises(self) -> None:
        # Arrange
        job = CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
        )
        completed = job.mark_in_progress().mark_completed()

        # Act & Assert
        with pytest.raises(exceptions.InvalidStateError):
            completed.mark_cancelled()

    def test_increment_discovered(self) -> None:
        # Arrange
        job = CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
        )

        # Act
        updated = job.increment_discovered()

        # Assert
        assert job.total_discovered == 0
        assert updated.total_discovered == 1

    def test_increment_ingested(self) -> None:
        # Arrange
        job = CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
        )

        # Act
        updated = job.increment_ingested()

        # Assert
        assert job.total_ingested == 0
        assert updated.total_ingested == 1

    def test_immutability(self) -> None:
        # Arrange
        job = CrawlJob.create(
            notebook_id="nb1",
            seed_url="https://example.com",
        )

        # Act & Assert
        with pytest.raises(Exception):
            job.status = CrawlStatus.IN_PROGRESS
