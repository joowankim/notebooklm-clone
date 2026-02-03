"""Mapper between Conversation entity and ORM schema."""

import json

from src.conversation.domain.model import Conversation, Message, MessageRole
from src.infrastructure.models.conversation import ConversationSchema, MessageSchema


class ConversationMapper:
    """Maps between Conversation domain entity and ORM schema."""

    @staticmethod
    def to_entity(record: ConversationSchema) -> Conversation:
        """Convert ORM record to domain entity."""
        messages = tuple(
            Message(
                id=msg.id,
                role=MessageRole(msg.role),
                content=msg.content,
                citations=json.loads(msg.citations) if msg.citations else None,
                created_at=msg.created_at,
            )
            for msg in sorted(record.messages, key=lambda m: m.created_at)
        )

        return Conversation(
            id=record.id,
            notebook_id=record.notebook_id,
            title=record.title,
            messages=messages,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def to_record(entity: Conversation) -> ConversationSchema:
        """Convert domain entity to ORM record."""
        return ConversationSchema(
            id=entity.id,
            notebook_id=entity.notebook_id,
            title=entity.title,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def message_to_record(message: Message, conversation_id: str) -> MessageSchema:
        """Convert Message to ORM record."""
        return MessageSchema(
            id=message.id,
            conversation_id=conversation_id,
            role=message.role.value,
            content=message.content,
            citations=json.dumps(message.citations) if message.citations else None,
            created_at=message.created_at,
        )
