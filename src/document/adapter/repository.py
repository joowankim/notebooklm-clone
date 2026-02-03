"""Document repository implementation."""

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from src.common import ListQuery, PaginationSchema
from src.document.domain.mapper import DocumentMapper
from src.document.domain.model import Document
from src.document.domain.status import DocumentStatus
from src.infrastructure.models.document import DocumentSchema


class DocumentRepository:
    """Repository for Document persistence."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._mapper = DocumentMapper()

    async def find_by_id(self, id: str) -> Document | None:
        """Find document by ID."""
        stmt = sqlalchemy.select(DocumentSchema).where(DocumentSchema.id == id)
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return self._mapper.to_entity(record)

    async def find_by_notebook_and_url(
        self, notebook_id: str, url: str
    ) -> Document | None:
        """Find document by notebook ID and URL."""
        stmt = sqlalchemy.select(DocumentSchema).where(
            DocumentSchema.notebook_id == notebook_id,
            DocumentSchema.url == url,
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return self._mapper.to_entity(record)

    async def save(self, entity: Document) -> Document:
        """Save document (insert or update)."""
        record = self._mapper.to_record(entity)
        merged = await self._session.merge(record)
        await self._session.flush()
        return self._mapper.to_entity(merged)

    async def delete(self, id: str) -> bool:
        """Delete document by ID."""
        stmt = sqlalchemy.delete(DocumentSchema).where(DocumentSchema.id == id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0

    async def list_by_notebook(
        self, notebook_id: str, query: ListQuery
    ) -> PaginationSchema[Document]:
        """List documents for a notebook with pagination."""
        # Count total
        count_stmt = (
            sqlalchemy.select(sqlalchemy.func.count())
            .select_from(DocumentSchema)
            .where(DocumentSchema.notebook_id == notebook_id)
        )
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar_one()

        # Fetch page
        stmt = (
            sqlalchemy.select(DocumentSchema)
            .where(DocumentSchema.notebook_id == notebook_id)
            .order_by(DocumentSchema.created_at.desc())
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

    async def list_by_status(
        self, notebook_id: str, status: DocumentStatus
    ) -> list[Document]:
        """List documents by status for a notebook."""
        stmt = (
            sqlalchemy.select(DocumentSchema)
            .where(
                DocumentSchema.notebook_id == notebook_id,
                DocumentSchema.status == status.value,
            )
            .order_by(DocumentSchema.created_at.asc())
        )
        result = await self._session.execute(stmt)
        records = result.scalars().all()
        return [self._mapper.to_entity(record) for record in records]

    async def count_by_notebook(self, notebook_id: str) -> int:
        """Count documents in a notebook."""
        stmt = (
            sqlalchemy.select(sqlalchemy.func.count())
            .select_from(DocumentSchema)
            .where(DocumentSchema.notebook_id == notebook_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
