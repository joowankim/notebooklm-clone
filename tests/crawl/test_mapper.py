"""Tests for crawl domain mappers."""

import datetime

from src.crawl.domain import mapper as crawl_mapper_module
from src.crawl.domain import model
from src.crawl.domain.status import CrawlStatus, DiscoveredUrlStatus
from src.infrastructure.models import crawl as crawl_schema


class TestCrawlJobMapper:
    """Tests for CrawlJobMapper."""

    def test_to_entity(self) -> None:
        # Arrange
        now = datetime.datetime.now(datetime.timezone.utc)
        record = crawl_schema.CrawlJobSchema(
            id="abc123def456",
            notebook_id="notebook1",
            seed_url="https://example.com",
            domain="example.com",
            max_depth=3,
            max_pages=100,
            url_include_pattern=r"/docs/.*",
            url_exclude_pattern=r".*\.pdf$",
            status="in_progress",
            total_discovered=5,
            total_ingested=3,
            error_message=None,
            created_at=now,
            updated_at=now,
        )

        # Act
        entity = crawl_mapper_module.CrawlJobMapper.to_entity(record)

        # Assert
        expected = model.CrawlJob(
            id="abc123def456",
            notebook_id="notebook1",
            seed_url="https://example.com",
            domain="example.com",
            max_depth=3,
            max_pages=100,
            url_include_pattern=r"/docs/.*",
            url_exclude_pattern=r".*\.pdf$",
            status=CrawlStatus.IN_PROGRESS,
            total_discovered=5,
            total_ingested=3,
            error_message=None,
            created_at=now,
            updated_at=now,
        )
        assert entity == expected

    def test_to_record(self) -> None:
        # Arrange
        now = datetime.datetime.now(datetime.timezone.utc)
        entity = model.CrawlJob(
            id="abc123def456",
            notebook_id="notebook1",
            seed_url="https://example.com",
            domain="example.com",
            max_depth=2,
            max_pages=50,
            url_include_pattern=None,
            url_exclude_pattern=None,
            status=CrawlStatus.PENDING,
            total_discovered=0,
            total_ingested=0,
            error_message=None,
            created_at=now,
            updated_at=now,
        )

        # Act
        record = crawl_mapper_module.CrawlJobMapper.to_record(entity)

        # Assert
        assert record.id == "abc123def456"
        assert record.notebook_id == "notebook1"
        assert record.seed_url == "https://example.com"
        assert record.domain == "example.com"
        assert record.max_depth == 2
        assert record.max_pages == 50
        assert record.url_include_pattern is None
        assert record.url_exclude_pattern is None
        assert record.status == "pending"
        assert record.total_discovered == 0
        assert record.total_ingested == 0
        assert record.error_message is None

    def test_roundtrip(self) -> None:
        # Arrange
        now = datetime.datetime.now(datetime.timezone.utc)
        original = model.CrawlJob(
            id="roundtrip123",
            notebook_id="nb1",
            seed_url="https://docs.example.com/guide",
            domain="docs.example.com",
            max_depth=3,
            max_pages=25,
            url_include_pattern=r"/guide/.*",
            url_exclude_pattern=None,
            status=CrawlStatus.COMPLETED,
            total_discovered=10,
            total_ingested=8,
            error_message=None,
            created_at=now,
            updated_at=now,
        )

        # Act
        record = crawl_mapper_module.CrawlJobMapper.to_record(original)
        restored = crawl_mapper_module.CrawlJobMapper.to_entity(record)

        # Assert
        assert restored == original


class TestDiscoveredUrlMapper:
    """Tests for DiscoveredUrlMapper."""

    def test_to_entity(self) -> None:
        # Arrange
        record = crawl_schema.DiscoveredUrlSchema(
            id="url123",
            crawl_job_id="job456",
            url="https://example.com/page1",
            depth=1,
            status="ingested",
            document_id="doc789",
        )

        # Act
        entity = crawl_mapper_module.DiscoveredUrlMapper.to_entity(record)

        # Assert
        expected = model.DiscoveredUrl(
            url="https://example.com/page1",
            depth=1,
            status=DiscoveredUrlStatus.INGESTED,
            document_id="doc789",
        )
        assert entity == expected

    def test_to_record(self) -> None:
        # Arrange
        entity = model.DiscoveredUrl(
            url="https://example.com/page2",
            depth=2,
            status=DiscoveredUrlStatus.PENDING,
            document_id=None,
        )

        # Act
        record = crawl_mapper_module.DiscoveredUrlMapper.to_record(
            entity=entity,
            crawl_job_id="job456",
        )

        # Assert
        assert len(record.id) == 32
        assert record.crawl_job_id == "job456"
        assert record.url == "https://example.com/page2"
        assert record.depth == 2
        assert record.status == "pending"
        assert record.document_id is None

    def test_to_entity_with_none_document_id(self) -> None:
        # Arrange
        record = crawl_schema.DiscoveredUrlSchema(
            id="url999",
            crawl_job_id="job123",
            url="https://example.com/skip",
            depth=0,
            status="skipped",
            document_id=None,
        )

        # Act
        entity = crawl_mapper_module.DiscoveredUrlMapper.to_entity(record)

        # Assert
        assert entity.document_id is None
        assert entity.status == DiscoveredUrlStatus.SKIPPED
