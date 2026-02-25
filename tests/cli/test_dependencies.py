"""Tests for CLI dependency factory functions."""

from unittest import mock

import pytest
import sqlalchemy.ext.asyncio

from src.cli import dependencies as deps
from src.conversation.handler import handlers as conversation_handlers
from src.crawl.handler import handlers as crawl_handlers
from src.crawl.service import crawl_service as crawl_service_module
from src.document.handler import handlers as document_handlers
from src.document.service import ingestion_pipeline as ingestion_module
from src.evaluation.handler import handlers as evaluation_handlers
from src.notebook.handler import handlers as notebook_handlers
from src.query.handler import handlers as query_handlers


@pytest.fixture
def mock_session() -> mock.MagicMock:
    """Create a mock AsyncSession."""
    return mock.MagicMock(spec=sqlalchemy.ext.asyncio.AsyncSession)


class TestNotebookHandlerBuilders:
    """Tests for notebook handler factory functions."""

    def test_build_create_notebook_handler(self, mock_session: mock.MagicMock) -> None:
        handler = deps.build_create_notebook_handler(mock_session)
        assert isinstance(handler, notebook_handlers.CreateNotebookHandler)

    def test_build_get_notebook_handler(self, mock_session: mock.MagicMock) -> None:
        handler = deps.build_get_notebook_handler(mock_session)
        assert isinstance(handler, notebook_handlers.GetNotebookHandler)

    def test_build_list_notebooks_handler(self, mock_session: mock.MagicMock) -> None:
        handler = deps.build_list_notebooks_handler(mock_session)
        assert isinstance(handler, notebook_handlers.ListNotebooksHandler)

    def test_build_delete_notebook_handler(self, mock_session: mock.MagicMock) -> None:
        handler = deps.build_delete_notebook_handler(mock_session)
        assert isinstance(handler, notebook_handlers.DeleteNotebookHandler)


class TestDocumentHandlerBuilders:
    """Tests for document (source) handler factory functions."""

    def test_build_add_source_handler_returns_tuple(self, mock_session: mock.MagicMock) -> None:
        handler, bg_service = deps.build_add_source_handler(mock_session)
        assert isinstance(handler, document_handlers.AddSourceHandler)
        assert isinstance(bg_service, ingestion_module.BackgroundIngestionService)

    def test_build_get_document_handler(self, mock_session: mock.MagicMock) -> None:
        handler = deps.build_get_document_handler(mock_session)
        assert isinstance(handler, document_handlers.GetDocumentHandler)

    def test_build_list_sources_handler(self, mock_session: mock.MagicMock) -> None:
        handler = deps.build_list_sources_handler(mock_session)
        assert isinstance(handler, document_handlers.ListSourcesHandler)


class TestConversationHandlerBuilders:
    """Tests for conversation handler factory functions."""

    def test_build_create_conversation_handler(self, mock_session: mock.MagicMock) -> None:
        handler = deps.build_create_conversation_handler(mock_session)
        assert isinstance(handler, conversation_handlers.CreateConversationHandler)

    def test_build_get_conversation_handler(self, mock_session: mock.MagicMock) -> None:
        handler = deps.build_get_conversation_handler(mock_session)
        assert isinstance(handler, conversation_handlers.GetConversationHandler)

    def test_build_list_conversations_handler(self, mock_session: mock.MagicMock) -> None:
        handler = deps.build_list_conversations_handler(mock_session)
        assert isinstance(handler, conversation_handlers.ListConversationsHandler)

    def test_build_delete_conversation_handler(self, mock_session: mock.MagicMock) -> None:
        handler = deps.build_delete_conversation_handler(mock_session)
        assert isinstance(handler, conversation_handlers.DeleteConversationHandler)

    @mock.patch("src.cli.dependencies._build_rag_agent")
    def test_build_send_message_handler(
        self, mock_rag: mock.MagicMock, mock_session: mock.MagicMock
    ) -> None:
        mock_rag.return_value = mock.MagicMock()
        handler = deps.build_send_message_handler(mock_session)
        assert isinstance(handler, conversation_handlers.SendMessageHandler)


class TestQueryHandlerBuilders:
    """Tests for query handler factory functions."""

    @mock.patch("src.cli.dependencies._build_rag_agent")
    def test_build_query_notebook_handler(
        self, mock_rag: mock.MagicMock, mock_session: mock.MagicMock
    ) -> None:
        mock_rag.return_value = mock.MagicMock()
        handler = deps.build_query_notebook_handler(mock_session)
        assert isinstance(handler, query_handlers.QueryNotebookHandler)


class TestCrawlHandlerBuilders:
    """Tests for crawl handler factory functions."""

    def test_build_start_crawl_handler_returns_tuple(self, mock_session: mock.MagicMock) -> None:
        handler, bg_service = deps.build_start_crawl_handler(mock_session)
        assert isinstance(handler, crawl_handlers.StartCrawlHandler)
        assert isinstance(bg_service, crawl_service_module.BackgroundCrawlService)

    def test_build_get_crawl_job_handler(self, mock_session: mock.MagicMock) -> None:
        handler = deps.build_get_crawl_job_handler(mock_session)
        assert isinstance(handler, crawl_handlers.GetCrawlJobHandler)

    def test_build_list_crawl_jobs_handler(self, mock_session: mock.MagicMock) -> None:
        handler = deps.build_list_crawl_jobs_handler(mock_session)
        assert isinstance(handler, crawl_handlers.ListCrawlJobsHandler)

    def test_build_cancel_crawl_handler(self, mock_session: mock.MagicMock) -> None:
        handler = deps.build_cancel_crawl_handler(mock_session)
        assert isinstance(handler, crawl_handlers.CancelCrawlHandler)


class TestEvaluationHandlerBuilders:
    """Tests for evaluation handler factory functions."""

    @mock.patch("src.evaluation.adapter.generator.SyntheticTestGenerator.__init__", return_value=None)
    def test_build_generate_dataset_handler(
        self, mock_gen: mock.MagicMock, mock_session: mock.MagicMock
    ) -> None:
        handler = deps.build_generate_dataset_handler(mock_session)
        assert isinstance(handler, evaluation_handlers.GenerateDatasetHandler)

    def test_build_list_datasets_handler(self, mock_session: mock.MagicMock) -> None:
        handler = deps.build_list_datasets_handler(mock_session)
        assert isinstance(handler, evaluation_handlers.ListDatasetsHandler)

    def test_build_run_evaluation_handler(self, mock_session: mock.MagicMock) -> None:
        handler = deps.build_run_evaluation_handler(mock_session)
        assert isinstance(handler, evaluation_handlers.RunEvaluationHandler)

    def test_build_get_run_handler(self, mock_session: mock.MagicMock) -> None:
        handler = deps.build_get_run_handler(mock_session)
        assert isinstance(handler, evaluation_handlers.GetRunHandler)

    def test_build_compare_runs_handler(self, mock_session: mock.MagicMock) -> None:
        handler = deps.build_compare_runs_handler(mock_session)
        assert isinstance(handler, evaluation_handlers.CompareRunsHandler)

    def test_build_run_evaluation_handler_with_optional_deps(
        self, mock_session: mock.MagicMock
    ) -> None:
        rag_agent = mock.MagicMock()
        llm_judge = mock.MagicMock()
        handler = deps.build_run_evaluation_handler(
            mock_session, rag_agent=rag_agent, llm_judge=llm_judge,
        )
        assert isinstance(handler, evaluation_handlers.RunEvaluationHandler)
