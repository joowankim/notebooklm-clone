"""Query dependency injection container."""

from dependency_injector import containers, providers

from src.chunk.adapter.embedding import openai_embedding
from src.chunk.adapter import repository as chunk_repository_module
from src.document.adapter import repository as document_repository_module
from src.notebook.adapter import repository as notebook_repository_module
from src.query.adapter.pydantic_ai import agent as rag_agent_module
from src.query.handler import handlers
from src.query.service import retrieval


class QueryAdapterContainer(containers.DeclarativeContainer):
    """Container for query adapters."""

    rag_agent = providers.Singleton(rag_agent_module.RAGAgent)


class QueryServiceContainer(containers.DeclarativeContainer):
    """Container for query services."""

    chunk_adapter = providers.DependenciesContainer()
    document_adapter = providers.DependenciesContainer()

    embedding_provider = providers.Singleton(openai_embedding.OpenAIEmbeddingProvider)

    retrieval_service = providers.Factory(
        retrieval.RetrievalService,
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
