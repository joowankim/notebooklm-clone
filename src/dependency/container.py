"""Application dependency injection container."""

from dependency_injector import containers, providers

from src.chunk.dependency import ChunkContainer
from src.conversation.dependency import ConversationContainer
from src.document.dependency import DocumentContainer
from src.notebook.dependency import NotebookContainer
from src.query.dependency import QueryContainer


class ApplicationContainer(containers.DeclarativeContainer):
    """Root application container."""

    config = providers.Configuration()

    # Database session - provided per request
    db_session = providers.Dependency()

    # Domain containers
    notebook = providers.Container(
        NotebookContainer,
        db_session=db_session,
    )

    chunk = providers.Container(
        ChunkContainer,
        db_session=db_session,
    )

    document = providers.Container(
        DocumentContainer,
        db_session=db_session,
        notebook_adapter=notebook.adapter,
    )

    query = providers.Container(
        QueryContainer,
        db_session=db_session,
        notebook_adapter=notebook.adapter,
        chunk_adapter=chunk.adapter,
        document_adapter=document.adapter,
    )

    conversation = providers.Container(
        ConversationContainer,
        db_session=db_session,
        notebook_repository=notebook.adapter.repository,
        retrieval_service=query.service.retrieval_service,
        rag_agent=query.adapter.rag_agent,
    )
