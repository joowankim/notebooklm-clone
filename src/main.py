"""FastAPI application entry point."""

import contextlib
import http
from typing import AsyncGenerator

import fastapi
import fastapi.responses
import slowapi
import slowapi.errors
import starlette.middleware.base

from src import exceptions
from src.chunk.entrypoint import api as chunk_api
from src.common import rate_limit
from src.conversation.entrypoint import api as conversation_api
from src import database as database_module
from src.dependency import container as container_module
from src.document.entrypoint import api as document_api
from src.notebook.entrypoint import api as notebook_api
from src.query.entrypoint import api as query_api

# Create container
container = container_module.ApplicationContainer()


@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    await database_module.init_db()
    yield
    # Shutdown
    await database_module.close_db()


# Create FastAPI app
app = fastapi.FastAPI(
    title="NotebookLM Clone",
    description="Document Research System with RAG",
    version="0.1.0",
    lifespan=lifespan,
)

# Add rate limiter
app.state.limiter = rate_limit.limiter
app.add_exception_handler(
    slowapi.errors.RateLimitExceeded,
    slowapi._rate_limit_exceeded_handler,
)


# Database session middleware
class DBSessionMiddleware(starlette.middleware.base.BaseHTTPMiddleware):
    """Middleware to inject database session into container."""

    async def dispatch(
        self, request: fastapi.Request, call_next: starlette.middleware.base.RequestResponseEndpoint
    ) -> fastapi.responses.Response:
        async with database_module.async_session_factory() as session:
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
async def not_found_handler(
    request: fastapi.Request, exc: exceptions.NotFoundError
) -> fastapi.responses.JSONResponse:
    """Handle not found errors."""
    return fastapi.responses.JSONResponse(
        status_code=http.HTTPStatus.NOT_FOUND,
        content={"detail": exc.message},
    )


@app.exception_handler(exceptions.ValidationError)
async def validation_handler(
    request: fastapi.Request, exc: exceptions.ValidationError
) -> fastapi.responses.JSONResponse:
    """Handle validation errors."""
    return fastapi.responses.JSONResponse(
        status_code=http.HTTPStatus.BAD_REQUEST,
        content={"detail": exc.message},
    )


@app.exception_handler(exceptions.InvalidStateError)
async def invalid_state_handler(
    request: fastapi.Request, exc: exceptions.InvalidStateError
) -> fastapi.responses.JSONResponse:
    """Handle invalid state transition errors."""
    return fastapi.responses.JSONResponse(
        status_code=http.HTTPStatus.CONFLICT,
        content={"detail": exc.message},
    )


@app.exception_handler(exceptions.ExternalServiceError)
async def external_service_handler(
    request: fastapi.Request, exc: exceptions.ExternalServiceError
) -> fastapi.responses.JSONResponse:
    """Handle external service errors."""
    return fastapi.responses.JSONResponse(
        status_code=http.HTTPStatus.BAD_GATEWAY,
        content={"detail": exc.message},
    )


# Health check
@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


# Include routers under /api/v1 prefix
app.include_router(notebook_api.router, prefix="/api/v1")
app.include_router(document_api.router, prefix="/api/v1")
app.include_router(document_api.document_router, prefix="/api/v1")
app.include_router(chunk_api.router, prefix="/api/v1")
app.include_router(query_api.router, prefix="/api/v1")
app.include_router(conversation_api.router, prefix="/api/v1")
