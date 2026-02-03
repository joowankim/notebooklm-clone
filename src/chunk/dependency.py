"""Chunk dependency injection container."""

from dependency_injector import containers, providers

from src.chunk.adapter.embedding.openai_embedding import OpenAIEmbeddingProvider
from src.chunk.adapter.repository import ChunkRepository
from src.chunk.handler import handlers


class ChunkAdapterContainer(containers.DeclarativeContainer):
    """Container for chunk infrastructure adapters."""

    db_session = providers.Dependency()

    repository = providers.Factory(
        ChunkRepository,
        session=db_session,
    )

    embedding_provider = providers.Singleton(OpenAIEmbeddingProvider)


class ChunkHandlerContainer(containers.DeclarativeContainer):
    """Container for chunk handlers."""

    adapter = providers.DependenciesContainer()

    get_chunk_handler = providers.Factory(
        handlers.GetChunkHandler,
        repository=adapter.repository,
    )

    list_chunks_by_document_handler = providers.Factory(
        handlers.ListChunksByDocumentHandler,
        repository=adapter.repository,
    )


class ChunkContainer(containers.DeclarativeContainer):
    """Root chunk container."""

    db_session = providers.Dependency()

    adapter = providers.Container(
        ChunkAdapterContainer,
        db_session=db_session,
    )

    handler = providers.Container(
        ChunkHandlerContainer,
        adapter=adapter,
    )
