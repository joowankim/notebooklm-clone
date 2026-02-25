"""Tests for BackgroundIngestionService.wait_for_all()."""

import asyncio
from unittest import mock

import pytest

from src.document.service import ingestion_pipeline as ingestion_module


@pytest.fixture
def mock_pipeline() -> mock.MagicMock:
    """Create a mock IngestionPipeline."""
    return mock.MagicMock(spec=ingestion_module.IngestionPipeline)


class TestBackgroundIngestionServiceWaitForAll:
    """Tests for BackgroundIngestionService.wait_for_all() method."""

    @pytest.mark.asyncio
    async def test_wait_for_all_with_no_tasks(self, mock_pipeline: mock.MagicMock) -> None:
        """wait_for_all should return immediately when no tasks are pending."""
        service = ingestion_module.BackgroundIngestionService(pipeline=mock_pipeline)

        await service.wait_for_all()

    @pytest.mark.asyncio
    async def test_wait_for_all_waits_for_pending_tasks(
        self, mock_pipeline: mock.MagicMock
    ) -> None:
        """wait_for_all should block until all pending tasks complete."""
        completed: list[str] = []

        async def slow_process(doc_id: str) -> None:
            await asyncio.sleep(0.05)
            completed.append(doc_id)
            return None

        mock_pipeline.process = mock.AsyncMock(side_effect=slow_process)
        service = ingestion_module.BackgroundIngestionService(pipeline=mock_pipeline)

        doc1 = mock.MagicMock()
        doc1.id = "doc-1"
        doc2 = mock.MagicMock()
        doc2.id = "doc-2"

        service.trigger_ingestion(doc1)
        service.trigger_ingestion(doc2)

        assert service.is_processing("doc-1")
        assert service.is_processing("doc-2")

        await service.wait_for_all()

        assert "doc-1" in completed
        assert "doc-2" in completed

    @pytest.mark.asyncio
    async def test_wait_for_all_handles_task_exceptions(
        self, mock_pipeline: mock.MagicMock
    ) -> None:
        """wait_for_all should not raise even if tasks fail."""
        mock_pipeline.process = mock.AsyncMock(side_effect=RuntimeError("boom"))
        service = ingestion_module.BackgroundIngestionService(pipeline=mock_pipeline)

        doc = mock.MagicMock()
        doc.id = "doc-fail"

        service.trigger_ingestion(doc)
        await service.wait_for_all()

    @pytest.mark.asyncio
    async def test_wait_for_all_clears_tasks_after_completion(
        self, mock_pipeline: mock.MagicMock
    ) -> None:
        """Tasks should be cleaned up after wait_for_all completes."""
        mock_pipeline.process = mock.AsyncMock(return_value=None)
        service = ingestion_module.BackgroundIngestionService(pipeline=mock_pipeline)

        doc = mock.MagicMock()
        doc.id = "doc-cleanup"

        service.trigger_ingestion(doc)
        await service.wait_for_all()

        assert not service.is_processing("doc-cleanup")
