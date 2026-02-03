"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from src import exceptions
from src.chunk.entrypoint import api as chunk_api
from src.common.rate_limit import limiter
from src.conversation.entrypoint import api as conversation_api
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

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Database session middleware
class DBSessionMiddleware(BaseHTTPMiddleware):
    """Middleware to inject database session into container."""

    async def dispatch(self, request: Request, call_next):
        async with async_session_factory() as session:
            with container.db_session.override(session):
                try:
                    response = await call_next(request)
                    await session.commit()
                    return response
                except Exception:
                    await session.rollback()
                    raise


app.add_middleware(DBSessionMiddleware)


# Wire container
container.wire(
    modules=[
        "src.notebook.entrypoint.api",
        "src.document.entrypoint.api",
        "src.chunk.entrypoint.api",
        "src.query.entrypoint.api",
        "src.conversation.entrypoint.api",
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


@app.exception_handler(exceptions.ExternalServiceError)
async def external_service_handler(
    request: Request, exc: exceptions.ExternalServiceError
) -> JSONResponse:
    """Handle external service errors."""
    return JSONResponse(
        status_code=502,
        content={"detail": exc.message},
    )


# Health check
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}


# Include routers under /api/v1 prefix
app.include_router(notebook_api.router, prefix="/api/v1")
app.include_router(document_api.router, prefix="/api/v1")
app.include_router(document_api.document_router, prefix="/api/v1")
app.include_router(chunk_api.router, prefix="/api/v1")
app.include_router(query_api.router, prefix="/api/v1")
app.include_router(conversation_api.router, prefix="/api/v1")
