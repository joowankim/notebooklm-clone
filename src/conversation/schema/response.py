"""Conversation response schemas."""

import datetime
from typing import Any, Self

import pydantic

from src.conversation.domain import model


class ConversationId(pydantic.BaseModel):
    """Response with conversation ID."""

    id: str


class MessageDetail(pydantic.BaseModel):
    """Message detail response."""

    id: str
    role: str
    content: str
    citations: list[dict[str, Any]] | None = None
    created_at: datetime.datetime

    @classmethod
    def from_model(cls, message: model.Message) -> Self:
        return cls(
            id=message.id,
            role=message.role.value,
            content=message.content,
            citations=message.citations,
            created_at=message.created_at,
        )


class ConversationDetail(pydantic.BaseModel):
    """Conversation detail response."""

    id: str
    notebook_id: str
    title: str | None
    messages: list[MessageDetail]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @classmethod
    def from_model(cls, conversation: model.Conversation) -> Self:
        return cls(
            id=conversation.id,
            notebook_id=conversation.notebook_id,
            title=conversation.title,
            messages=[MessageDetail.from_model(m) for m in conversation.messages],
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )


class MessageResponse(pydantic.BaseModel):
    """Response after sending a message (includes AI response)."""

    user_message: MessageDetail
    assistant_message: MessageDetail
