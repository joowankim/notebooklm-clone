"""Notebook repository implementation."""

import sqlalchemy
import sqlalchemy.ext.asyncio

from src.common import pagination
from src.infrastructure.models import notebook as notebook_schema
from src.notebook.domain import mapper as notebook_mapper_module
from src.notebook.domain import model


class NotebookRepository:
    """Repository for Notebook persistence."""

    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        self._session = session
        self._mapper = notebook_mapper_module.NotebookMapper()

    async def find_by_id(self, id: str) -> model.Notebook | None:
        """Find notebook by ID."""
        stmt = sqlalchemy.select(notebook_schema.NotebookSchema).where(
            notebook_schema.NotebookSchema.id == id
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return self._mapper.to_entity(record)

    async def save(self, entity: model.Notebook) -> model.Notebook:
        """Save notebook (insert or update)."""
        record = self._mapper.to_record(entity)
        merged = await self._session.merge(record)
        await self._session.flush()
        return self._mapper.to_entity(merged)

    async def delete(self, id: str) -> bool:
        """Delete notebook by ID."""
        stmt = sqlalchemy.delete(notebook_schema.NotebookSchema).where(
            notebook_schema.NotebookSchema.id == id
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0

    async def list(self, query: pagination.ListQuery) -> pagination.PaginationSchema[model.Notebook]:
        """List notebooks with pagination."""
        # Count total
        count_stmt = sqlalchemy.select(sqlalchemy.func.count()).select_from(
            notebook_schema.NotebookSchema
        )
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar_one()

        # Fetch page
        stmt = (
            sqlalchemy.select(notebook_schema.NotebookSchema)
            .order_by(notebook_schema.NotebookSchema.created_at.desc())
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
