"""Base repository implementations."""

import abc
from typing import Generic, TypeVar

import sqlalchemy
import sqlalchemy.ext.asyncio

T = TypeVar("T")
S = TypeVar("S")


class SQLAlchemyRepository(abc.ABC, Generic[T, S]):
    """Base repository for SQLAlchemy ORM operations.

    T: Domain entity type
    S: SQLAlchemy schema (ORM model) type
    """

    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        self._session = session

    @property
    @abc.abstractmethod
    def _schema_class(self) -> type[S]:
        """Return the SQLAlchemy schema class."""
        ...

    @abc.abstractmethod
    def _to_entity(self, record: S) -> T:
        """Convert ORM record to domain entity."""
        ...

    @abc.abstractmethod
    def _to_record(self, entity: T) -> S:
        """Convert domain entity to ORM record."""
        ...

    async def find_by_id(self, id: str) -> T | None:
        """Find entity by ID."""
        stmt = sqlalchemy.select(self._schema_class).where(self._schema_class.id == id)
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return self._to_entity(record)

    async def save(self, entity: T) -> T:
        """Save entity (insert or update)."""
        record = self._to_record(entity)
        merged = await self._session.merge(record)
        await self._session.flush()
        return self._to_entity(merged)

    async def delete(self, id: str) -> bool:
        """Delete entity by ID."""
        stmt = sqlalchemy.delete(self._schema_class).where(self._schema_class.id == id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0
