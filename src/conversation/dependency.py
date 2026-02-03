"""Conversation dependency injection container."""

from dependency_injector import containers, providers

from src.conversation.adapter.repository import ConversationRepository
from src.conversation.handler import handlers


class ConversationContainer(containers.DeclarativeContainer):
    """Container for conversation dependencies."""

    # External dependencies
    db_session = providers.Dependency()
    notebook_repository = providers.Dependency()
    retrieval_service = providers.Dependency()
    rag_agent = providers.Dependency()

    # Repository
    conversation_repository = providers.Factory(
        ConversationRepository,
        session=db_session,
    )

    # Handlers
    create_conversation_handler = providers.Factory(
        handlers.CreateConversationHandler,
        notebook_repository=notebook_repository,
        conversation_repository=conversation_repository,
    )

    get_conversation_handler = providers.Factory(
        handlers.GetConversationHandler,
        conversation_repository=conversation_repository,
    )

    list_conversations_handler = providers.Factory(
        handlers.ListConversationsHandler,
        conversation_repository=conversation_repository,
    )

    delete_conversation_handler = providers.Factory(
        handlers.DeleteConversationHandler,
        conversation_repository=conversation_repository,
    )

    send_message_handler = providers.Factory(
        handlers.SendMessageHandler,
        conversation_repository=conversation_repository,
        retrieval_service=retrieval_service,
        rag_agent=rag_agent,
    )
