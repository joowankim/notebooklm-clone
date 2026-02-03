"""Conversation API endpoints."""

import http

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Request

from src.common import PaginationSchema
from src.common.rate_limit import CONVERSATION_RATE, DEFAULT_RATE, limiter
from src.conversation.handler import handlers
from src.conversation.schema import command, query, response
from src.dependency.container import ApplicationContainer

router = APIRouter(tags=["conversations"])


@router.post(
    "/notebooks/{notebook_id}/conversations",
    response_model=response.ConversationId,
    status_code=http.HTTPStatus.CREATED,
)
@limiter.limit(DEFAULT_RATE)
@inject
async def create_conversation(
    request: Request,
    notebook_id: str,
    cmd: command.CreateConversation,
    handler: handlers.CreateConversationHandler = Depends(
        Provide[ApplicationContainer.conversation.create_conversation_handler]
    ),
):
    """Create a new conversation in a notebook."""
    return await handler.handle(notebook_id, cmd)


@router.get(
    "/notebooks/{notebook_id}/conversations",
    response_model=PaginationSchema[response.ConversationDetail],
)
@inject
async def list_conversations(
    notebook_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    handler: handlers.ListConversationsHandler = Depends(
        Provide[ApplicationContainer.conversation.list_conversations_handler]
    ),
):
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
    handler: handlers.GetConversationHandler = Depends(
        Provide[ApplicationContainer.conversation.get_conversation_handler]
    ),
):
    """Get a conversation with all messages."""
    return await handler.handle(conversation_id)


@router.delete(
    "/conversations/{conversation_id}",
    status_code=http.HTTPStatus.NO_CONTENT,
)
@inject
async def delete_conversation(
    conversation_id: str,
    handler: handlers.DeleteConversationHandler = Depends(
        Provide[ApplicationContainer.conversation.delete_conversation_handler]
    ),
):
    """Delete a conversation."""
    await handler.handle(conversation_id)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=response.MessageResponse,
    status_code=http.HTTPStatus.CREATED,
)
@limiter.limit(CONVERSATION_RATE)
@inject
async def send_message(
    request: Request,
    conversation_id: str,
    cmd: command.SendMessage,
    handler: handlers.SendMessageHandler = Depends(
        Provide[ApplicationContainer.conversation.send_message_handler]
    ),
):
    """Send a message in a conversation and get AI response."""
    return await handler.handle(conversation_id, cmd)
