"""Document dependency injection container."""

from dependency_injector import containers, providers

from src.chunk.adapter.embedding.openai_embedding import OpenAIEmbeddingProvider
from src.document.adapter.extractor.composite import CompositeExtractor
from src.document.adapter.repository import DocumentRepository
from src.document.handler import handlers
from src.document.service.chunking.service import ChunkingService
from src.document.service.ingestion_pipeline import (
    BackgroundIngestionService,
    IngestionPipeline,
)
from src.settings import settings


class DocumentAdapterContainer(containers.DeclarativeContainer):
    """Container for document infrastructure adapters."""

    db_session = providers.Dependency()

    repository = providers.Factory(
        DocumentRepository,
        session=db_session,
    )

    content_extractor = providers.Singleton(
        CompositeExtractor,
        jina_api_key=settings.jina_api_key,
    )


class DocumentServiceContainer(containers.DeclarativeContainer):
    """Container for document services."""

    adapter = providers.DependenciesContainer()

    chunking_service = providers.Singleton(ChunkingService)

    embedding_provider = providers.Singleton(OpenAIEmbeddingProvider)

    ingestion_pipeline = providers.Singleton(
        IngestionPipeline,
        content_extractor=adapter.content_extractor,
        embedding_provider=embedding_provider,
        chunking_service=chunking_service,
    )

    background_ingestion = providers.Singleton(
        BackgroundIngestionService,
        pipeline=ingestion_pipeline,
    )


class DocumentHandlerContainer(containers.DeclarativeContainer):
    """Container for document handlers."""

    adapter = providers.DependenciesContainer()
    notebook_adapter = providers.DependenciesContainer()
    service = providers.DependenciesContainer()

    add_source_handler = providers.Factory(
        handlers.AddSourceHandler,
        document_repository=adapter.repository,
        notebook_repository=notebook_adapter.repository,
        background_ingestion=service.background_ingestion,
    )

    get_document_handler = providers.Factory(
        handlers.GetDocumentHandler,
        repository=adapter.repository,
    )

    list_sources_handler = providers.Factory(
        handlers.ListSourcesHandler,
        document_repository=adapter.repository,
        notebook_repository=notebook_adapter.repository,
    )


class DocumentContainer(containers.DeclarativeContainer):
    """Root document container."""

    db_session = providers.Dependency()
    notebook_adapter = providers.DependenciesContainer()

    adapter = providers.Container(
        DocumentAdapterContainer,
        db_session=db_session,
    )

    service = providers.Container(
        DocumentServiceContainer,
        adapter=adapter,
    )

    handler = providers.Container(
        DocumentHandlerContainer,
        adapter=adapter,
        notebook_adapter=notebook_adapter,
        service=service,
    )
