"""Conversation schemas."""

from src.conversation.schema.command import CreateConversation, SendMessage
from src.conversation.schema.query import ListConversations
from src.conversation.schema.response import (
    ConversationDetail,
    ConversationId,
    MessageDetail,
    MessageResponse,
)

__all__ = [
    "CreateConversation",
    "SendMessage",
    "ListConversations",
    "ConversationId",
    "ConversationDetail",
    "MessageDetail",
    "MessageResponse",
]
