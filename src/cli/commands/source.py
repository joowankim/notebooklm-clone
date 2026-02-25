"""Source CLI commands."""

import asyncio

import rich.console
import rich.table
import typer

from src.cli import dependencies as deps
from src.cli import utils as cli_utils
from src.cli.error_handling import handle_domain_errors
from src.document.schema import command as command_module
from src.document.schema import query as query_module

console = rich.console.Console()
app = typer.Typer()


@app.command("add")
def add_source(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    url: str = typer.Argument(..., help="Source URL"),
    title: str | None = typer.Option(None, "--title", "-t", help="Source title"),
) -> None:
    """Add a source URL to a notebook."""
    asyncio.run(_add_source(notebook_id, url, title))


@handle_domain_errors
async def _add_source(notebook_id: str, url: str, title: str | None) -> None:
    async with cli_utils.get_session_context() as session:
        handler, background_service = deps.build_add_source_handler(session)
        cmd = command_module.AddSource(url=url, title=title)
        result = await handler.handle(notebook_id, cmd)
        await session.commit()

        console.print(f"[green]Added source:[/green] {result.id}")
        console.print(f"  URL: {url}")
        console.print("[dim]Ingesting document...[/dim]")

        await background_service.wait_for_all()
        console.print("[green]Ingestion completed.[/green]")


@app.command("list")
def list_sources(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(10, "--size", "-s", help="Page size"),
) -> None:
    """List sources in a notebook."""
    asyncio.run(_list_sources(notebook_id, page, size))


@handle_domain_errors
async def _list_sources(notebook_id: str, page: int, size: int) -> None:
    async with cli_utils.get_session_context() as session:
        handler = deps.build_list_sources_handler(session)
        qry = query_module.ListSources(notebook_id=notebook_id, page=page, size=size)
        result = await handler.handle(qry)

        if not result.items:
            console.print("[yellow]No sources found.[/yellow]")
            return

        table = rich.table.Table(title="Sources")
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
            }.get(doc.status, "white")

            table.add_row(
                doc.id,
                doc.title or "-",
                doc.url[:40] + "..." if len(doc.url) > 40 else doc.url,
                f"[{status_style}]{doc.status}[/{status_style}]",
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


@handle_domain_errors
async def _get_source(document_id: str) -> None:
    async with cli_utils.get_session_context() as session:
        handler = deps.build_get_document_handler(session)
        doc = await handler.handle(document_id)

        status_style = {
            "pending": "yellow",
            "processing": "blue",
            "completed": "green",
            "failed": "red",
        }.get(doc.status, "white")

        console.print(f"[bold]Document:[/bold] {doc.id}")
        console.print(f"  Notebook ID: {doc.notebook_id}")
        console.print(f"  URL: {doc.url}")
        console.print(f"  Title: {doc.title or '-'}")
        console.print(f"  Status: [{status_style}]{doc.status}[/{status_style}]")
        if doc.error_message:
            console.print(f"  Error: [red]{doc.error_message}[/red]")
        console.print(f"  Created: {doc.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
