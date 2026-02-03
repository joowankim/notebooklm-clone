"""Notebook repository implementation."""

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from src.common import ListQuery, PaginationSchema
from src.infrastructure.models.notebook import NotebookSchema
from src.notebook.domain.mapper import NotebookMapper
from src.notebook.domain.model import Notebook


class NotebookRepository:
    """Repository for Notebook persistence."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._mapper = NotebookMapper()

    async def find_by_id(self, id: str) -> Notebook | None:
        """Find notebook by ID."""
        stmt = sqlalchemy.select(NotebookSchema).where(NotebookSchema.id == id)
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return self._mapper.to_entity(record)

    async def save(self, entity: Notebook) -> Notebook:
        """Save notebook (insert or update)."""
        record = self._mapper.to_record(entity)
        merged = await self._session.merge(record)
        await self._session.flush()
        return self._mapper.to_entity(merged)

    async def delete(self, id: str) -> bool:
        """Delete notebook by ID."""
        stmt = sqlalchemy.delete(NotebookSchema).where(NotebookSchema.id == id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0

    async def list(self, query: ListQuery) -> PaginationSchema[Notebook]:
        """List notebooks with pagination."""
        # Count total
        count_stmt = sqlalchemy.select(sqlalchemy.func.count()).select_from(NotebookSchema)
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar_one()

        # Fetch page
        stmt = (
            sqlalchemy.select(NotebookSchema)
            .order_by(NotebookSchema.created_at.desc())
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
