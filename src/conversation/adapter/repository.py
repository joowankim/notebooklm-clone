"""Conversation repository implementation."""

import sqlalchemy
import sqlalchemy.ext.asyncio

from src.common import pagination
from src.conversation.domain import mapper as conversation_mapper_module
from src.conversation.domain import model
from src.infrastructure.models import conversation as conversation_schema


class ConversationRepository:
    """Repository for Conversation persistence."""

    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        self._session = session
        self._mapper = conversation_mapper_module.ConversationMapper()

    async def find_by_id(self, id: str) -> model.Conversation | None:
        """Find conversation by ID with messages."""
        stmt = sqlalchemy.select(conversation_schema.ConversationSchema).where(conversation_schema.ConversationSchema.id == id)
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return self._mapper.to_entity(record)

    async def save(self, entity: model.Conversation) -> model.Conversation:
        """Save conversation (insert or update)."""
        record = self._mapper.to_record(entity)
        merged = await self._session.merge(record)
        await self._session.flush()

        # Save messages
        for message in entity.messages:
            msg_record = self._mapper.message_to_record(message, entity.id)
            await self._session.merge(msg_record)

        await self._session.flush()
        return entity

    async def add_message(self, conversation_id: str, message: model.Message) -> None:
        """Add a message to an existing conversation."""
        msg_record = self._mapper.message_to_record(message, conversation_id)
        await self._session.merge(msg_record)

        # Update conversation updated_at
        stmt = (
            sqlalchemy.update(conversation_schema.ConversationSchema)
            .where(conversation_schema.ConversationSchema.id == conversation_id)
            .values(updated_at=sqlalchemy.func.now())
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def delete(self, id: str) -> bool:
        """Delete conversation by ID."""
        stmt = sqlalchemy.delete(conversation_schema.ConversationSchema).where(conversation_schema.ConversationSchema.id == id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0

    async def list_by_notebook(
        self, notebook_id: str, query: pagination.ListQuery
    ) -> pagination.PaginationSchema[model.Conversation]:
        """List conversations for a notebook with pagination."""
        # Count total
        count_stmt = (
            sqlalchemy.select(sqlalchemy.func.count())
            .select_from(conversation_schema.ConversationSchema)
            .where(conversation_schema.ConversationSchema.notebook_id == notebook_id)
        )
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar_one()

        # Fetch page
        stmt = (
            sqlalchemy.select(conversation_schema.ConversationSchema)
            .where(conversation_schema.ConversationSchema.notebook_id == notebook_id)
            .order_by(conversation_schema.ConversationSchema.updated_at.desc())
            .offset(query.offset)
            .limit(query.size)
        )
        result = await self._session.execute(stmt)
        records = result.scalars().all()

        items = [self._mapper.to_entity(record) for record in records]
        return pagination.PaginationSchema.create(
            items=items,
            total=total,
            page=query.page,
            size=query.size,
        )
