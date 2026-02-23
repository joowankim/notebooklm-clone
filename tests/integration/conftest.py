"""Integration test fixtures using testcontainers."""

from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
import sqlalchemy
import sqlalchemy.ext.asyncio
import testcontainers.postgres

from src.database import Base


@pytest.fixture(scope="session")
def postgres_container() -> Generator[testcontainers.postgres.PostgresContainer, None, None]:
    """Start PostgreSQL container with pgvector for the test session."""
    container = testcontainers.postgres.PostgresContainer(
        image="pgvector/pgvector:pg16",
        username="test",
        password="test",
        dbname="test_db",
    )
    with container:
        yield container


@pytest.fixture(scope="session")
def database_url(postgres_container: testcontainers.postgres.PostgresContainer) -> str:
    """Get async database URL from the container."""
    sync_url = postgres_container.get_connection_url()
    return sync_url.replace("psycopg2", "asyncpg")


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def integration_engine(
    database_url: str,
) -> AsyncGenerator[sqlalchemy.ext.asyncio.AsyncEngine, None]:
    """Create async engine for integration tests."""
    engine = sqlalchemy.ext.asyncio.create_async_engine(
        database_url,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.execute(sqlalchemy.text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function", loop_scope="session")
async def integration_session(
    integration_engine: sqlalchemy.ext.asyncio.AsyncEngine,
) -> AsyncGenerator[sqlalchemy.ext.asyncio.AsyncSession, None]:
    """Create isolated async session with transaction rollback."""
    session_factory = sqlalchemy.ext.asyncio.async_sessionmaker(
        integration_engine,
        class_=sqlalchemy.ext.asyncio.AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        async with session.begin():
            yield session
            await session.rollback()
