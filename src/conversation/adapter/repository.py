"""Conversation repository implementation."""

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from src.common import ListQuery, PaginationSchema
from src.conversation.domain.mapper import ConversationMapper
from src.conversation.domain.model import Conversation, Message
from src.infrastructure.models.conversation import ConversationSchema, MessageSchema


class ConversationRepository:
    """Repository for Conversation persistence."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._mapper = ConversationMapper()

    async def find_by_id(self, id: str) -> Conversation | None:
        """Find conversation by ID with messages."""
        stmt = sqlalchemy.select(ConversationSchema).where(ConversationSchema.id == id)
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return self._mapper.to_entity(record)

    async def save(self, entity: Conversation) -> Conversation:
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

    async def add_message(self, conversation_id: str, message: Message) -> None:
        """Add a message to an existing conversation."""
        msg_record = self._mapper.message_to_record(message, conversation_id)
        await self._session.merge(msg_record)

        # Update conversation updated_at
        stmt = (
            sqlalchemy.update(ConversationSchema)
            .where(ConversationSchema.id == conversation_id)
            .values(updated_at=sqlalchemy.func.now())
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def delete(self, id: str) -> bool:
        """Delete conversation by ID."""
        stmt = sqlalchemy.delete(ConversationSchema).where(ConversationSchema.id == id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0

    async def list_by_notebook(
        self, notebook_id: str, query: ListQuery
    ) -> PaginationSchema[Conversation]:
        """List conversations for a notebook with pagination."""
        # Count total
        count_stmt = (
            sqlalchemy.select(sqlalchemy.func.count())
            .select_from(ConversationSchema)
            .where(ConversationSchema.notebook_id == notebook_id)
        )
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar_one()

        # Fetch page
        stmt = (
            sqlalchemy.select(ConversationSchema)
            .where(ConversationSchema.notebook_id == notebook_id)
            .order_by(ConversationSchema.updated_at.desc())
            .offset(query.offset)
            .limit(query.size)
        )
        result = await self._session.execute(stmt)
        records = result.scalars().all()

        items = [self._mapper.to_entity(record) for record in records]
        return PaginationSchema.create(
            items=items,
            total=total,
            page=query.page,
            size=query.size,
        )
