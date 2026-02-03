"""Notebook CLI commands."""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from src.cli.utils import get_session_context

console = Console()
app = typer.Typer()


@app.command("create")
def create_notebook(
    name: str = typer.Argument(..., help="Name of the notebook"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Description"),
):
    """Create a new notebook."""
    asyncio.run(_create_notebook(name, description))


async def _create_notebook(name: str, description: Optional[str]):
    from src.notebook.domain.model import Notebook
    from src.notebook.adapter.repository import NotebookRepository

    async with get_session_context() as session:
        repository = NotebookRepository(session)
        notebook = Notebook.create(name=name, description=description)
        saved = await repository.save(notebook)
        await session.commit()

        console.print(f"[green]Created notebook:[/green] {saved.id}")
        console.print(f"  Name: {saved.name}")
        if saved.description:
            console.print(f"  Description: {saved.description}")


@app.command("list")
def list_notebooks(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(10, "--size", "-s", help="Page size"),
):
    """List all notebooks."""
    asyncio.run(_list_notebooks(page, size))


async def _list_notebooks(page: int, size: int):
    from src.common import ListQuery
    from src.notebook.adapter.repository import NotebookRepository

    async with get_session_context() as session:
        repository = NotebookRepository(session)
        result = await repository.list(ListQuery(page=page, size=size))

        if not result.items:
            console.print("[yellow]No notebooks found.[/yellow]")
            return

        table = Table(title="Notebooks")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Description")
        table.add_column("Created", style="dim")

        for notebook in result.items:
            table.add_row(
                notebook.id,
                notebook.name,
                notebook.description or "-",
                notebook.created_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)
        console.print(f"Page {result.page}/{result.pages} (Total: {result.total})")


@app.command("get")
def get_notebook(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
):
    """Get notebook details."""
    asyncio.run(_get_notebook(notebook_id))


async def _get_notebook(notebook_id: str):
    from src.notebook.adapter.repository import NotebookRepository

    async with get_session_context() as session:
        repository = NotebookRepository(session)
        notebook = await repository.find_by_id(notebook_id)

        if notebook is None:
            console.print(f"[red]Notebook not found:[/red] {notebook_id}")
            raise typer.Exit(1)

        console.print(f"[bold]Notebook:[/bold] {notebook.id}")
        console.print(f"  Name: {notebook.name}")
        console.print(f"  Description: {notebook.description or '-'}")
        console.print(f"  Created: {notebook.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        console.print(f"  Updated: {notebook.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")


@app.command("delete")
def delete_notebook(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a notebook."""
    if not force:
        confirm = typer.confirm(f"Delete notebook {notebook_id}?")
        if not confirm:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit()

    asyncio.run(_delete_notebook(notebook_id))


async def _delete_notebook(notebook_id: str):
    from src.notebook.adapter.repository import NotebookRepository

    async with get_session_context() as session:
        repository = NotebookRepository(session)
        deleted = await repository.delete(notebook_id)
        await session.commit()

        if deleted:
            console.print(f"[green]Deleted notebook:[/green] {notebook_id}")
        else:
            console.print(f"[red]Notebook not found:[/red] {notebook_id}")
            raise typer.Exit(1)
