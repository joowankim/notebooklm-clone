"""CLI utility functions."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session_factory


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session for CLI commands."""
    async with async_session_factory() as session:
        yield session
