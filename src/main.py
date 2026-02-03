"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src import exceptions
from src.chunk.entrypoint import api as chunk_api
from src.database import async_session_factory, close_db, init_db
from src.dependency.container import ApplicationContainer
from src.document.entrypoint import api as document_api
from src.notebook.entrypoint import api as notebook_api
from src.query.entrypoint import api as query_api

# Create container
container = ApplicationContainer()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


# Create FastAPI app
app = FastAPI(
    title="NotebookLM Clone",
    description="Document Research System with RAG",
    version="0.1.0",
    lifespan=lifespan,
)


# Dependency to get session and wire container
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for request."""
    async with async_session_factory() as session:
        # Wire session to container for this request
        with container.db_session.override(session):
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


# Wire container
container.wire(
    modules=[
        "src.notebook.entrypoint.api",
        "src.document.entrypoint.api",
        "src.chunk.entrypoint.api",
        "src.query.entrypoint.api",
    ]
)


# Exception handlers
@app.exception_handler(exceptions.NotFoundError)
async def not_found_handler(request: Request, exc: exceptions.NotFoundError) -> JSONResponse:
    """Handle not found errors."""
    return JSONResponse(
        status_code=404,
        content={"detail": exc.message},
    )


@app.exception_handler(exceptions.ValidationError)
async def validation_handler(request: Request, exc: exceptions.ValidationError) -> JSONResponse:
    """Handle validation errors."""
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message},
    )


@app.exception_handler(exceptions.InvalidStateError)
async def invalid_state_handler(
    request: Request, exc: exceptions.InvalidStateError
) -> JSONResponse:
    """Handle invalid state transition errors."""
    return JSONResponse(
        status_code=409,
        content={"detail": exc.message},
    )


# Health check
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}


# API router
api_router = FastAPI(title="API v1")


# Include domain routers with session dependency
@api_router.middleware("http")
async def db_session_middleware(request: Request, call_next):
    """Middleware to inject database session."""
    async with async_session_factory() as session:
        with container.db_session.override(session):
            try:
                response = await call_next(request)
                await session.commit()
                return response
            except Exception:
                await session.rollback()
                raise


api_router.include_router(notebook_api.router)
api_router.include_router(document_api.router)
api_router.include_router(document_api.document_router)
api_router.include_router(chunk_api.router)
api_router.include_router(query_api.router)

# Mount API router
app.mount("/api/v1", api_router)
