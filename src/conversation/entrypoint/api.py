"""Conversation API endpoints."""

import http

import fastapi
from dependency_injector.wiring import Provide, inject

from src.common import pagination, rate_limit
from src.conversation.handler import handlers
from src.conversation.schema import command, query, response
from src.dependency import container as container_module

router = fastapi.APIRouter(tags=["conversations"])


@router.post(
    "/notebooks/{notebook_id}/conversations",
    response_model=response.ConversationId,
    status_code=http.HTTPStatus.CREATED,
)
@rate_limit.limiter.limit(rate_limit.DEFAULT_RATE)
@inject
async def create_conversation(
    request: fastapi.Request,
    notebook_id: str,
    cmd: command.CreateConversation,
    handler: handlers.CreateConversationHandler = fastapi.Depends(
        Provide[container_module.ApplicationContainer.conversation.create_conversation_handler]
    ),
) -> response.ConversationId:
    """Create a new conversation in a notebook."""
    return await handler.handle(notebook_id, cmd)


@router.get(
    "/notebooks/{notebook_id}/conversations",
    response_model=pagination.PaginationSchema[response.ConversationDetail],
)
@inject
async def list_conversations(
    notebook_id: str,
    page: int = fastapi.Query(1, ge=1),
    size: int = fastapi.Query(10, ge=1, le=100),
    handler: handlers.ListConversationsHandler = fastapi.Depends(
        Provide[container_module.ApplicationContainer.conversation.list_conversations_handler]
    ),
) -> pagination.PaginationSchema[response.ConversationDetail]:
    """List conversations for a notebook."""
    qry = query.ListConversations(notebook_id=notebook_id, page=page, size=size)
    return await handler.handle(qry)


@router.get(
    "/conversations/{conversation_id}",
    response_model=response.ConversationDetail,
)
@inject
async def get_conversation(
    conversation_id: str,
    handler: handlers.GetConversationHandler = fastapi.Depends(
        Provide[container_module.ApplicationContainer.conversation.get_conversation_handler]
    ),
) -> response.ConversationDetail:
    """Get a conversation with all messages."""
    return await handler.handle(conversation_id)


@router.delete(
    "/conversations/{conversation_id}",
    status_code=http.HTTPStatus.NO_CONTENT,
)
@inject
async def delete_conversation(
    conversation_id: str,
    handler: handlers.DeleteConversationHandler = fastapi.Depends(
        Provide[container_module.ApplicationContainer.conversation.delete_conversation_handler]
    ),
) -> None:
    """Delete a conversation."""
    await handler.handle(conversation_id)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=response.MessageResponse,
    status_code=http.HTTPStatus.CREATED,
)
@rate_limit.limiter.limit(rate_limit.CONVERSATION_RATE)
@inject
async def send_message(
    request: fastapi.Request,
    conversation_id: str,
    cmd: command.SendMessage,
    handler: handlers.SendMessageHandler = fastapi.Depends(
        Provide[container_module.ApplicationContainer.conversation.send_message_handler]
    ),
) -> response.MessageResponse:
    """Send a message in a conversation and get AI response."""
    return await handler.handle(conversation_id, cmd)
