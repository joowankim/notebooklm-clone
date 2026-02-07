"""Evaluation dependency injection container."""

from dependency_injector import containers, providers

from src import settings as settings_module
from src.evaluation.adapter import generator as generator_module
from src.evaluation.adapter import repository as evaluation_repository_module
from src.evaluation.handler import handlers


class EvaluationAdapterContainer(containers.DeclarativeContainer):
    """Container for evaluation infrastructure adapters."""

    db_session = providers.Dependency()

    dataset_repository = providers.Factory(
        evaluation_repository_module.DatasetRepository,
        session=db_session,
    )

    run_repository = providers.Factory(
        evaluation_repository_module.RunRepository,
        session=db_session,
    )

    test_generator = providers.Singleton(
        generator_module.SyntheticTestGenerator,
        eval_model=settings_module.settings.eval_model,
    )


class EvaluationHandlerContainer(containers.DeclarativeContainer):
    """Container for evaluation handlers."""

    adapter = providers.DependenciesContainer()
    notebook_adapter = providers.DependenciesContainer()
    document_adapter = providers.DependenciesContainer()
    chunk_adapter = providers.DependenciesContainer()
    query_service = providers.DependenciesContainer()

    generate_dataset_handler = providers.Factory(
        handlers.GenerateDatasetHandler,
        notebook_repository=notebook_adapter.repository,
        document_repository=document_adapter.repository,
        chunk_repository=chunk_adapter.repository,
        dataset_repository=adapter.dataset_repository,
        test_generator=adapter.test_generator,
    )

    run_evaluation_handler = providers.Factory(
        handlers.RunEvaluationHandler,
        dataset_repository=adapter.dataset_repository,
        run_repository=adapter.run_repository,
        retrieval_service=query_service.retrieval_service,
    )

    get_dataset_handler = providers.Factory(
        handlers.GetDatasetHandler,
        dataset_repository=adapter.dataset_repository,
    )

    get_run_handler = providers.Factory(
        handlers.GetRunHandler,
        run_repository=adapter.run_repository,
    )

    list_datasets_handler = providers.Factory(
        handlers.ListDatasetsHandler,
        notebook_repository=notebook_adapter.repository,
        dataset_repository=adapter.dataset_repository,
    )


class EvaluationContainer(containers.DeclarativeContainer):
    """Root evaluation container."""

    db_session = providers.Dependency()
    notebook_adapter = providers.DependenciesContainer()
    document_adapter = providers.DependenciesContainer()
    chunk_adapter = providers.DependenciesContainer()
    query_service = providers.DependenciesContainer()

    adapter = providers.Container(
        EvaluationAdapterContainer,
        db_session=db_session,
    )

    handler = providers.Container(
        EvaluationHandlerContainer,
        adapter=adapter,
        notebook_adapter=notebook_adapter,
        document_adapter=document_adapter,
        chunk_adapter=chunk_adapter,
        query_service=query_service,
    )
