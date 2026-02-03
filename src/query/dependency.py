"""Query dependency injection container."""

from dependency_injector import containers, providers

from src.chunk.adapter.embedding.openai_embedding import OpenAIEmbeddingProvider
from src.chunk.adapter.repository import ChunkRepository
from src.document.adapter.repository import DocumentRepository
from src.notebook.adapter.repository import NotebookRepository
from src.query.adapter.pydantic_ai.agent import RAGAgent
from src.query.handler import handlers
from src.query.service.retrieval import RetrievalService


class QueryAdapterContainer(containers.DeclarativeContainer):
    """Container for query adapters."""

    rag_agent = providers.Singleton(RAGAgent)


class QueryServiceContainer(containers.DeclarativeContainer):
    """Container for query services."""

    chunk_adapter = providers.DependenciesContainer()
    document_adapter = providers.DependenciesContainer()

    embedding_provider = providers.Singleton(OpenAIEmbeddingProvider)

    retrieval_service = providers.Factory(
        RetrievalService,
        chunk_repository=chunk_adapter.repository,
        document_repository=document_adapter.repository,
        embedding_provider=embedding_provider,
    )


class QueryHandlerContainer(containers.DeclarativeContainer):
    """Container for query handlers."""

    adapter = providers.DependenciesContainer()
    service = providers.DependenciesContainer()
    notebook_adapter = providers.DependenciesContainer()

    query_notebook_handler = providers.Factory(
        handlers.QueryNotebookHandler,
        notebook_repository=notebook_adapter.repository,
        retrieval_service=service.retrieval_service,
        rag_agent=adapter.rag_agent,
    )


class QueryContainer(containers.DeclarativeContainer):
    """Root query container."""

    db_session = providers.Dependency()
    notebook_adapter = providers.DependenciesContainer()
    chunk_adapter = providers.DependenciesContainer()
    document_adapter = providers.DependenciesContainer()

    adapter = providers.Container(QueryAdapterContainer)

    service = providers.Container(
        QueryServiceContainer,
        chunk_adapter=chunk_adapter,
        document_adapter=document_adapter,
    )

    handler = providers.Container(
        QueryHandlerContainer,
        adapter=adapter,
        service=service,
        notebook_adapter=notebook_adapter,
    )
