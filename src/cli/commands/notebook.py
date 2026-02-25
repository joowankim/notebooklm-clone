"""Notebook CLI commands."""

import asyncio

import rich.console
import rich.table
import typer

from src.cli import dependencies as deps
from src.cli import utils as cli_utils
from src.cli.error_handling import handle_domain_errors
from src.notebook.schema import command as command_module
from src.notebook.schema import query as query_module

console = rich.console.Console()
app = typer.Typer()


@app.command("create")
def create_notebook(
    name: str = typer.Argument(..., help="Name of the notebook"),
    description: str | None = typer.Option(None, "--description", "-d", help="Description"),
) -> None:
    """Create a new notebook."""
    asyncio.run(_create_notebook(name, description))


@handle_domain_errors
async def _create_notebook(name: str, description: str | None) -> None:
    async with cli_utils.get_session_context() as session:
        handler = deps.build_create_notebook_handler(session)
        cmd = command_module.CreateNotebook(name=name, description=description)
        result = await handler.handle(cmd)
        await session.commit()

        console.print(f"[green]Created notebook:[/green] {result.id}")
        console.print(f"  Name: {name}")
        if description:
            console.print(f"  Description: {description}")


@app.command("list")
def list_notebooks(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(10, "--size", "-s", help="Page size"),
) -> None:
    """List all notebooks."""
    asyncio.run(_list_notebooks(page, size))


@handle_domain_errors
async def _list_notebooks(page: int, size: int) -> None:
    async with cli_utils.get_session_context() as session:
        handler = deps.build_list_notebooks_handler(session)
        qry = query_module.ListNotebooks(page=page, size=size)
        result = await handler.handle(qry)

        if not result.items:
            console.print("[yellow]No notebooks found.[/yellow]")
            return

        table = rich.table.Table(title="Notebooks")
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
) -> None:
    """Get notebook details."""
    asyncio.run(_get_notebook(notebook_id))


@handle_domain_errors
async def _get_notebook(notebook_id: str) -> None:
    async with cli_utils.get_session_context() as session:
        handler = deps.build_get_notebook_handler(session)
        detail = await handler.handle(notebook_id)

        console.print(f"[bold]Notebook:[/bold] {detail.id}")
        console.print(f"  Name: {detail.name}")
        console.print(f"  Description: {detail.description or '-'}")
        console.print(f"  Created: {detail.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        console.print(f"  Updated: {detail.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")


@app.command("delete")
def delete_notebook(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a notebook."""
    if not force:
        confirm = typer.confirm(f"Delete notebook {notebook_id}?")
        if not confirm:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit()

    asyncio.run(_delete_notebook(notebook_id))


@handle_domain_errors
async def _delete_notebook(notebook_id: str) -> None:
    async with cli_utils.get_session_context() as session:
        handler = deps.build_delete_notebook_handler(session)
        await handler.handle(notebook_id)
        await session.commit()

        console.print(f"[green]Deleted notebook:[/green] {notebook_id}")
