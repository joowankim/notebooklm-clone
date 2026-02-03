"""Notebook dependency injection container."""

from dependency_injector import containers, providers

from src.notebook.adapter.repository import NotebookRepository
from src.notebook.handler import handlers


class NotebookAdapterContainer(containers.DeclarativeContainer):
    """Container for notebook infrastructure adapters."""

    db_session = providers.Dependency()

    repository = providers.Factory(
        NotebookRepository,
        session=db_session,
    )


class NotebookHandlerContainer(containers.DeclarativeContainer):
    """Container for notebook handlers."""

    adapter = providers.DependenciesContainer()

    create_notebook_handler = providers.Factory(
        handlers.CreateNotebookHandler,
        repository=adapter.repository,
    )

    get_notebook_handler = providers.Factory(
        handlers.GetNotebookHandler,
        repository=adapter.repository,
    )

    list_notebooks_handler = providers.Factory(
        handlers.ListNotebooksHandler,
        repository=adapter.repository,
    )

    update_notebook_handler = providers.Factory(
        handlers.UpdateNotebookHandler,
        repository=adapter.repository,
    )

    delete_notebook_handler = providers.Factory(
        handlers.DeleteNotebookHandler,
        repository=adapter.repository,
    )


class NotebookContainer(containers.DeclarativeContainer):
    """Root notebook container."""

    db_session = providers.Dependency()

    adapter = providers.Container(
        NotebookAdapterContainer,
        db_session=db_session,
    )

    handler = providers.Container(
        NotebookHandlerContainer,
        adapter=adapter,
    )
