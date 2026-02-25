"""CLI dependency factory functions for building handlers from a session."""

import sqlalchemy.ext.asyncio

from src import settings as settings_module
from src.chunk.adapter import repository as chunk_repository_module
from src.chunk.adapter.embedding import openai_embedding
from src.conversation.adapter import repository as conversation_repository_module
from src.conversation.handler import handlers as conversation_handlers
from src.crawl.adapter import repository as crawl_repository_module
from src.crawl.handler import handlers as crawl_handlers
from src.crawl.service import crawl_service as crawl_service_module
from src.crawl.service import link_discovery as link_discovery_module
from src.document.adapter import repository as document_repository_module
from src.document.adapter.extractor import composite as composite_module
from src.document.handler import handlers as document_handlers
from src.document.service import ingestion_pipeline as ingestion_module
from src.document.service.chunking import service as chunking_service_module
from src.evaluation.adapter import generator as generator_module
from src.evaluation.adapter import judge as judge_module
from src.evaluation.adapter import repository as evaluation_repository_module
from src.evaluation.handler import handlers as evaluation_handlers
from src.notebook.adapter import repository as notebook_repository_module
from src.notebook.handler import handlers as notebook_handlers
from src.query.adapter.pydantic_ai import agent as rag_agent_module
from src.query.handler import handlers as query_handlers
from src.query.service import retrieval as retrieval_module


def _build_retrieval_service(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> retrieval_module.RetrievalService:
    """Build retrieval service with required dependencies."""
    return retrieval_module.RetrievalService(
        chunk_repository=chunk_repository_module.ChunkRepository(session),
        document_repository=document_repository_module.DocumentRepository(session),
        embedding_provider=openai_embedding.OpenAIEmbeddingProvider(),
    )


def _build_rag_agent() -> rag_agent_module.RAGAgent:
    """Build RAG agent."""
    return rag_agent_module.RAGAgent()


def _build_background_ingestion_service() -> ingestion_module.BackgroundIngestionService:
    """Build background ingestion service with full pipeline."""
    content_extractor = composite_module.CompositeExtractor(
        jina_api_key=settings_module.settings.jina_api_key,
    )
    chunking_service = chunking_service_module.ChunkingService()
    embedding_provider = openai_embedding.OpenAIEmbeddingProvider()
    pipeline = ingestion_module.IngestionPipeline(
        content_extractor=content_extractor,
        embedding_provider=embedding_provider,
        chunking_service=chunking_service,
    )
    return ingestion_module.BackgroundIngestionService(pipeline=pipeline)


def _build_background_crawl_service(
    session: sqlalchemy.ext.asyncio.AsyncSession,
    background_ingestion: ingestion_module.BackgroundIngestionService,
) -> crawl_service_module.BackgroundCrawlService:
    """Build background crawl service."""
    crawl_service = crawl_service_module.CrawlService(
        crawl_repository=crawl_repository_module.CrawlJobRepository(session),
        document_repository=document_repository_module.DocumentRepository(session),
        link_discovery=link_discovery_module.LinkDiscoveryService(),
        background_ingestion=background_ingestion,
    )
    return crawl_service_module.BackgroundCrawlService(crawl_service=crawl_service)


# --- Notebook handlers ---


def build_create_notebook_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> notebook_handlers.CreateNotebookHandler:
    """Build CreateNotebookHandler."""
    return notebook_handlers.CreateNotebookHandler(
        repository=notebook_repository_module.NotebookRepository(session),
    )


def build_get_notebook_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> notebook_handlers.GetNotebookHandler:
    """Build GetNotebookHandler."""
    return notebook_handlers.GetNotebookHandler(
        repository=notebook_repository_module.NotebookRepository(session),
    )


def build_list_notebooks_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> notebook_handlers.ListNotebooksHandler:
    """Build ListNotebooksHandler."""
    return notebook_handlers.ListNotebooksHandler(
        repository=notebook_repository_module.NotebookRepository(session),
    )


def build_delete_notebook_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> notebook_handlers.DeleteNotebookHandler:
    """Build DeleteNotebookHandler."""
    return notebook_handlers.DeleteNotebookHandler(
        repository=notebook_repository_module.NotebookRepository(session),
    )


# --- Document (Source) handlers ---


def build_add_source_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> tuple[document_handlers.AddSourceHandler, ingestion_module.BackgroundIngestionService]:
    """Build AddSourceHandler with background ingestion service.

    Returns a tuple of (handler, background_service) so CLI can await wait_for_all().
    """
    background_ingestion = _build_background_ingestion_service()
    handler = document_handlers.AddSourceHandler(
        document_repository=document_repository_module.DocumentRepository(session),
        notebook_repository=notebook_repository_module.NotebookRepository(session),
        background_ingestion=background_ingestion,
    )
    return handler, background_ingestion


def build_get_document_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> document_handlers.GetDocumentHandler:
    """Build GetDocumentHandler."""
    return document_handlers.GetDocumentHandler(
        repository=document_repository_module.DocumentRepository(session),
    )


def build_list_sources_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> document_handlers.ListSourcesHandler:
    """Build ListSourcesHandler."""
    return document_handlers.ListSourcesHandler(
        document_repository=document_repository_module.DocumentRepository(session),
        notebook_repository=notebook_repository_module.NotebookRepository(session),
    )


# --- Conversation handlers ---


def build_create_conversation_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> conversation_handlers.CreateConversationHandler:
    """Build CreateConversationHandler."""
    return conversation_handlers.CreateConversationHandler(
        notebook_repository=notebook_repository_module.NotebookRepository(session),
        conversation_repository=conversation_repository_module.ConversationRepository(session),
    )


def build_get_conversation_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> conversation_handlers.GetConversationHandler:
    """Build GetConversationHandler."""
    return conversation_handlers.GetConversationHandler(
        conversation_repository=conversation_repository_module.ConversationRepository(session),
    )


def build_list_conversations_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> conversation_handlers.ListConversationsHandler:
    """Build ListConversationsHandler."""
    return conversation_handlers.ListConversationsHandler(
        conversation_repository=conversation_repository_module.ConversationRepository(session),
    )


def build_delete_conversation_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> conversation_handlers.DeleteConversationHandler:
    """Build DeleteConversationHandler."""
    return conversation_handlers.DeleteConversationHandler(
        conversation_repository=conversation_repository_module.ConversationRepository(session),
    )


def build_send_message_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> conversation_handlers.SendMessageHandler:
    """Build SendMessageHandler."""
    return conversation_handlers.SendMessageHandler(
        conversation_repository=conversation_repository_module.ConversationRepository(session),
        retrieval_service=_build_retrieval_service(session),
        rag_agent=_build_rag_agent(),
    )


# --- Query handlers ---


def build_query_notebook_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> query_handlers.QueryNotebookHandler:
    """Build QueryNotebookHandler."""
    return query_handlers.QueryNotebookHandler(
        notebook_repository=notebook_repository_module.NotebookRepository(session),
        retrieval_service=_build_retrieval_service(session),
        rag_agent=_build_rag_agent(),
    )


# --- Crawl handlers ---


def build_start_crawl_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> tuple[crawl_handlers.StartCrawlHandler, crawl_service_module.BackgroundCrawlService]:
    """Build StartCrawlHandler with background crawl service.

    Returns a tuple of (handler, background_service) so CLI can await wait_for_all().
    """
    background_ingestion = _build_background_ingestion_service()
    background_crawl = _build_background_crawl_service(session, background_ingestion)
    handler = crawl_handlers.StartCrawlHandler(
        notebook_repository=notebook_repository_module.NotebookRepository(session),
        crawl_repository=crawl_repository_module.CrawlJobRepository(session),
        background_crawl_service=background_crawl,
    )
    return handler, background_crawl


def build_get_crawl_job_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> crawl_handlers.GetCrawlJobHandler:
    """Build GetCrawlJobHandler."""
    return crawl_handlers.GetCrawlJobHandler(
        crawl_repository=crawl_repository_module.CrawlJobRepository(session),
    )


def build_list_crawl_jobs_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> crawl_handlers.ListCrawlJobsHandler:
    """Build ListCrawlJobsHandler."""
    return crawl_handlers.ListCrawlJobsHandler(
        notebook_repository=notebook_repository_module.NotebookRepository(session),
        crawl_repository=crawl_repository_module.CrawlJobRepository(session),
    )


def build_cancel_crawl_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> crawl_handlers.CancelCrawlHandler:
    """Build CancelCrawlHandler."""
    return crawl_handlers.CancelCrawlHandler(
        crawl_repository=crawl_repository_module.CrawlJobRepository(session),
    )


# --- Evaluation handlers ---


def build_generate_dataset_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> evaluation_handlers.GenerateDatasetHandler:
    """Build GenerateDatasetHandler."""
    return evaluation_handlers.GenerateDatasetHandler(
        notebook_repository=notebook_repository_module.NotebookRepository(session),
        document_repository=document_repository_module.DocumentRepository(session),
        chunk_repository=chunk_repository_module.ChunkRepository(session),
        dataset_repository=evaluation_repository_module.DatasetRepository(session),
        test_generator=generator_module.SyntheticTestGenerator(
            eval_model=settings_module.settings.eval_model,
        ),
    )


def build_list_datasets_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> evaluation_handlers.ListDatasetsHandler:
    """Build ListDatasetsHandler."""
    return evaluation_handlers.ListDatasetsHandler(
        notebook_repository=notebook_repository_module.NotebookRepository(session),
        dataset_repository=evaluation_repository_module.DatasetRepository(session),
    )


def build_run_evaluation_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
    rag_agent: rag_agent_module.RAGAgent | None = None,
    llm_judge: judge_module.LLMJudge | None = None,
) -> evaluation_handlers.RunEvaluationHandler:
    """Build RunEvaluationHandler."""
    return evaluation_handlers.RunEvaluationHandler(
        dataset_repository=evaluation_repository_module.DatasetRepository(session),
        run_repository=evaluation_repository_module.RunRepository(session),
        retrieval_service=_build_retrieval_service(session),
        rag_agent=rag_agent,
        llm_judge=llm_judge,
    )


def build_get_run_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> evaluation_handlers.GetRunHandler:
    """Build GetRunHandler."""
    return evaluation_handlers.GetRunHandler(
        run_repository=evaluation_repository_module.RunRepository(session),
        dataset_repository=evaluation_repository_module.DatasetRepository(session),
    )


def build_compare_runs_handler(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> evaluation_handlers.CompareRunsHandler:
    """Build CompareRunsHandler."""
    return evaluation_handlers.CompareRunsHandler(
        run_repository=evaluation_repository_module.RunRepository(session),
        dataset_repository=evaluation_repository_module.DatasetRepository(session),
    )
