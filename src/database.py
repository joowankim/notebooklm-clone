"""Database configuration and session management."""

from collections.abc import AsyncGenerator

import sqlalchemy
import sqlalchemy.ext.asyncio
import sqlalchemy.orm

from src import settings as settings_module


class Base(sqlalchemy.orm.DeclarativeBase):
    """Base class for all ORM models."""

    pass


# Create async engine
engine = sqlalchemy.ext.asyncio.create_async_engine(
    settings_module.settings.database_url,
    echo=settings_module.settings.debug,
    pool_pre_ping=True,
)

# Create session factory
async_session_factory = sqlalchemy.ext.asyncio.async_sessionmaker(
    engine,
    class_=sqlalchemy.ext.asyncio.AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[sqlalchemy.ext.asyncio.AsyncSession, None]:
    """Get database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize database (create tables)."""
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(sqlalchemy.text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
