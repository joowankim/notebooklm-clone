"""CLI utility functions."""

import contextlib
from collections.abc import AsyncGenerator

import sqlalchemy.ext.asyncio

from src import database as database_module


@contextlib.asynccontextmanager
async def get_session_context() -> AsyncGenerator[sqlalchemy.ext.asyncio.AsyncSession, None]:
    """Get a database session for CLI commands."""
    async with database_module.async_session_factory() as session:
        yield session
