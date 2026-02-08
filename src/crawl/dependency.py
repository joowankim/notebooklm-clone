"""Crawl dependency injection container."""

from dependency_injector import containers, providers

from src.crawl.adapter import repository as crawl_repository_module
from src.crawl.handler import handlers
from src.crawl.service import crawl_service as crawl_service_module
from src.crawl.service import link_discovery as link_discovery_module


class CrawlAdapterContainer(containers.DeclarativeContainer):
    """Container for crawl infrastructure adapters."""

    db_session = providers.Dependency()

    repository = providers.Factory(
        crawl_repository_module.CrawlJobRepository,
        session=db_session,
    )


class CrawlServiceContainer(containers.DeclarativeContainer):
    """Container for crawl services."""

    adapter = providers.DependenciesContainer()
    document_adapter = providers.DependenciesContainer()
    document_service = providers.DependenciesContainer()

    link_discovery = providers.Singleton(
        link_discovery_module.LinkDiscoveryService,
    )

    crawl_service = providers.Singleton(
        crawl_service_module.CrawlService,
        crawl_repository=adapter.repository,
        document_repository=document_adapter.repository,
        link_discovery=link_discovery,
        background_ingestion=document_service.background_ingestion,
    )

    background_crawl = providers.Singleton(
        crawl_service_module.BackgroundCrawlService,
        crawl_service=crawl_service,
    )


class CrawlHandlerContainer(containers.DeclarativeContainer):
    """Container for crawl handlers."""

    adapter = providers.DependenciesContainer()
    notebook_adapter = providers.DependenciesContainer()
    service = providers.DependenciesContainer()

    start_crawl_handler = providers.Factory(
        handlers.StartCrawlHandler,
        notebook_repository=notebook_adapter.repository,
        crawl_repository=adapter.repository,
        background_crawl_service=service.background_crawl,
    )

    get_crawl_job_handler = providers.Factory(
        handlers.GetCrawlJobHandler,
        crawl_repository=adapter.repository,
    )

    list_crawl_jobs_handler = providers.Factory(
        handlers.ListCrawlJobsHandler,
        notebook_repository=notebook_adapter.repository,
        crawl_repository=adapter.repository,
    )

    cancel_crawl_handler = providers.Factory(
        handlers.CancelCrawlHandler,
        crawl_repository=adapter.repository,
    )


class CrawlContainer(containers.DeclarativeContainer):
    """Root crawl container."""

    db_session = providers.Dependency()
    notebook_adapter = providers.DependenciesContainer()
    document_adapter = providers.DependenciesContainer()
    document_service = providers.DependenciesContainer()

    adapter = providers.Container(
        CrawlAdapterContainer,
        db_session=db_session,
    )

    service = providers.Container(
        CrawlServiceContainer,
        adapter=adapter,
        document_adapter=document_adapter,
        document_service=document_service,
    )

    handler = providers.Container(
        CrawlHandlerContainer,
        adapter=adapter,
        notebook_adapter=notebook_adapter,
        service=service,
    )
