"""Source CLI commands."""

import asyncio
from typing import Optional

import rich.console
import rich.table
import typer

from src.cli import utils as cli_utils
from src.common import pagination
from src.document.adapter import repository as document_repository_module
from src.document.domain import model as document_model
from src.notebook.adapter import repository as notebook_repository_module

console = rich.console.Console()
app = typer.Typer()


@app.command("add")
def add_source(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    url: str = typer.Argument(..., help="Source URL"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Source title"),
) -> None:
    """Add a source URL to a notebook."""
    asyncio.run(_add_source(notebook_id, url, title))


async def _add_source(notebook_id: str, url: str, title: Optional[str]) -> None:
    async with cli_utils.get_session_context() as session:
        # Verify notebook exists
        notebook_repo = notebook_repository_module.NotebookRepository(session)
        notebook = await notebook_repo.find_by_id(notebook_id)
        if notebook is None:
            console.print(f"[red]Notebook not found:[/red] {notebook_id}")
            raise typer.Exit(1)

        # Check for duplicate
        doc_repo = document_repository_module.DocumentRepository(session)
        existing = await doc_repo.find_by_notebook_and_url(notebook_id, url)
        if existing is not None:
            console.print(f"[yellow]Source URL already exists:[/yellow] {url}")
            console.print(f"  Document ID: {existing.id}")
            raise typer.Exit(1)

        # Create document
        document = document_model.Document.create(notebook_id=notebook_id, url=url, title=title)
        saved = await doc_repo.save(document)
        await session.commit()

        console.print(f"[green]Added source:[/green] {saved.id}")
        console.print(f"  URL: {saved.url}")
        console.print(f"  Status: {saved.status}")
        console.print("[dim]Note: Ingestion runs in the background when using the API.[/dim]")


@app.command("list")
def list_sources(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(10, "--size", "-s", help="Page size"),
) -> None:
    """List sources in a notebook."""
    asyncio.run(_list_sources(notebook_id, page, size))


async def _list_sources(notebook_id: str, page: int, size: int) -> None:
    async with cli_utils.get_session_context() as session:
        # Verify notebook exists
        notebook_repo = notebook_repository_module.NotebookRepository(session)
        notebook = await notebook_repo.find_by_id(notebook_id)
        if notebook is None:
            console.print(f"[red]Notebook not found:[/red] {notebook_id}")
            raise typer.Exit(1)

        doc_repo = document_repository_module.DocumentRepository(session)
        result = await doc_repo.list_by_notebook(
            notebook_id, pagination.ListQuery(page=page, size=size)
        )

        if not result.items:
            console.print("[yellow]No sources found.[/yellow]")
            return

        table = rich.table.Table(title=f"Sources in '{notebook.name}'")
        table.add_column("ID", style="cyan")
        table.add_column("Title")
        table.add_column("URL", max_width=40)
        table.add_column("Status", style="bold")
        table.add_column("Created", style="dim")

        for doc in result.items:
            status_style = {
                "pending": "yellow",
                "processing": "blue",
                "completed": "green",
                "failed": "red",
            }.get(doc.status.value, "white")

            table.add_row(
                doc.id,
                doc.title or "-",
                doc.url[:40] + "..." if len(doc.url) > 40 else doc.url,
                f"[{status_style}]{doc.status.value}[/{status_style}]",
                doc.created_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)
        console.print(f"Page {result.page}/{result.pages} (Total: {result.total})")


@app.command("get")
def get_source(
    document_id: str = typer.Argument(..., help="Document ID"),
) -> None:
    """Get source details."""
    asyncio.run(_get_source(document_id))


async def _get_source(document_id: str) -> None:
    async with cli_utils.get_session_context() as session:
        repo = document_repository_module.DocumentRepository(session)
        doc = await repo.find_by_id(document_id)

        if doc is None:
            console.print(f"[red]Document not found:[/red] {document_id}")
            raise typer.Exit(1)

        status_style = {
            "pending": "yellow",
            "processing": "blue",
            "completed": "green",
            "failed": "red",
        }.get(doc.status.value, "white")

        console.print(f"[bold]Document:[/bold] {doc.id}")
        console.print(f"  Notebook ID: {doc.notebook_id}")
        console.print(f"  URL: {doc.url}")
        console.print(f"  Title: {doc.title or '-'}")
        console.print(f"  Status: [{status_style}]{doc.status.value}[/{status_style}]")
        if doc.error_message:
            console.print(f"  Error: [red]{doc.error_message}[/red]")
        console.print(f"  Created: {doc.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
