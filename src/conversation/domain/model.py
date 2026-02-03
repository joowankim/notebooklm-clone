"""Conversation domain entity."""

import datetime
import uuid
from enum import StrEnum
from typing import Self

import pydantic

from src.common.types import utc_now


class MessageRole(StrEnum):
    """Role of a message in conversation."""

    USER = "user"
    ASSISTANT = "assistant"


class Message(pydantic.BaseModel):
    """A single message in a conversation."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    id: str
    role: MessageRole
    content: str
    citations: list[dict] | None = None  # For assistant messages
    created_at: datetime.datetime

    @classmethod
    def user(cls, content: str) -> Self:
        """Create a user message."""
        return cls(
            id=uuid.uuid4().hex,
            role=MessageRole.USER,
            content=content,
            created_at=utc_now(),
        )

    @classmethod
    def assistant(cls, content: str, citations: list[dict] | None = None) -> Self:
        """Create an assistant message."""
        return cls(
            id=uuid.uuid4().hex,
            role=MessageRole.ASSISTANT,
            content=content,
            citations=citations,
            created_at=utc_now(),
        )


class Conversation(pydantic.BaseModel):
    """Conversation entity for multi-turn interactions.

    Immutable: all state changes return new instances.
    """

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    id: str
    notebook_id: str
    title: str | None = None
    messages: tuple[Message, ...] = ()
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @classmethod
    def create(cls, notebook_id: str, title: str | None = None) -> Self:
        """Factory method to create a new conversation."""
        now = utc_now()
        return cls(
            id=uuid.uuid4().hex,
            notebook_id=notebook_id,
            title=title,
            messages=(),
            created_at=now,
            updated_at=now,
        )

    def add_message(self, message: Message) -> Self:
        """Add a message to the conversation."""
        # Auto-generate title from first user message
        new_title = self.title
        if new_title is None and message.role == MessageRole.USER:
            new_title = message.content[:50] + ("..." if len(message.content) > 50 else "")

        return self.model_copy(
            update={
                "messages": self.messages + (message,),
                "title": new_title,
                "updated_at": utc_now(),
            }
        )

    def add_exchange(self, user_message: Message, assistant_message: Message) -> Self:
        """Add a Q&A exchange (user question + assistant response)."""
        return self.add_message(user_message).add_message(assistant_message)

    @property
    def message_count(self) -> int:
        """Return the number of messages."""
        return len(self.messages)

    def get_context_for_rag(self, max_turns: int = 5) -> list[dict]:
        """Get recent conversation context for RAG.

        Args:
            max_turns: Maximum number of Q&A turns to include.

        Returns:
            List of message dicts with role and content.
        """
        # Get last N*2 messages (N turns = N questions + N answers)
        recent_messages = self.messages[-(max_turns * 2) :]
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in recent_messages
        ]
