"""Crawl REST API router."""

import http

import fastapi
from dependency_injector.wiring import Provide, inject

from src.common import pagination
from src.crawl.handler import handlers
from src.crawl.schema import command, query, response
from src.dependency import container as container_module

router = fastapi.APIRouter(
    prefix="/notebooks/{notebook_id}/crawl", tags=["crawl"]
)


@router.post(
    "",
    response_model=response.CrawlJobId,
    status_code=http.HTTPStatus.CREATED,
    summary="Start a crawl job",
    description="Start crawling from a seed URL to discover and ingest nested pages.",
    responses={
        http.HTTPStatus.CREATED: {"description": "Crawl job created successfully"},
        http.HTTPStatus.NOT_FOUND: {"description": "Notebook not found"},
    },
)
@inject
async def start_crawl(
    notebook_id: str,
    cmd: command.StartCrawl,
    handler: handlers.StartCrawlHandler = fastapi.Depends(
        Provide[container_module.ApplicationContainer.crawl.handler.start_crawl_handler]
    ),
) -> response.CrawlJobId:
    """Start a new crawl job for a notebook."""
    return await handler.handle(notebook_id, cmd)


@router.get(
    "",
    response_model=pagination.PaginationSchema[response.CrawlJobDetail],
    summary="List crawl jobs",
    description="List all crawl jobs for a notebook with pagination.",
    responses={
        http.HTTPStatus.OK: {"description": "Crawl jobs retrieved successfully"},
        http.HTTPStatus.NOT_FOUND: {"description": "Notebook not found"},
    },
)
@inject
async def list_crawl_jobs(
    notebook_id: str,
    page: int = fastapi.Query(1, ge=1),
    size: int = fastapi.Query(10, ge=1, le=100),
    handler: handlers.ListCrawlJobsHandler = fastapi.Depends(
        Provide[container_module.ApplicationContainer.crawl.handler.list_crawl_jobs_handler]
    ),
) -> pagination.PaginationSchema[response.CrawlJobDetail]:
    """List crawl jobs for a notebook."""
    qry = query.ListCrawlJobs(notebook_id=notebook_id, page=page, size=size)
    return await handler.handle(notebook_id, qry)


# Crawl job detail endpoints (under different prefix)
crawl_router = fastapi.APIRouter(prefix="/crawl", tags=["crawl"])


@crawl_router.get(
    "/{crawl_job_id}",
    response_model=response.CrawlJobDetail,
    summary="Get crawl job details",
    description="Retrieve detailed information about a crawl job.",
    responses={
        http.HTTPStatus.OK: {"description": "Crawl job details retrieved"},
        http.HTTPStatus.NOT_FOUND: {"description": "Crawl job not found"},
    },
)
@inject
async def get_crawl_job(
    crawl_job_id: str,
    include_urls: bool = fastapi.Query(False, description="Include discovered URLs"),
    handler: handlers.GetCrawlJobHandler = fastapi.Depends(
        Provide[container_module.ApplicationContainer.crawl.handler.get_crawl_job_handler]
    ),
) -> response.CrawlJobDetail:
    """Get crawl job details."""
    return await handler.handle(crawl_job_id, include_urls=include_urls)


@crawl_router.post(
    "/{crawl_job_id}/cancel",
    status_code=http.HTTPStatus.NO_CONTENT,
    summary="Cancel a crawl job",
    description="Cancel a pending or in-progress crawl job.",
    responses={
        http.HTTPStatus.NO_CONTENT: {"description": "Crawl job cancelled"},
        http.HTTPStatus.NOT_FOUND: {"description": "Crawl job not found"},
        http.HTTPStatus.CONFLICT: {"description": "Crawl job cannot be cancelled"},
    },
)
@inject
async def cancel_crawl(
    crawl_job_id: str,
    handler: handlers.CancelCrawlHandler = fastapi.Depends(
        Provide[container_module.ApplicationContainer.crawl.handler.cancel_crawl_handler]
    ),
) -> None:
    """Cancel a crawl job."""
    await handler.handle(crawl_job_id)
