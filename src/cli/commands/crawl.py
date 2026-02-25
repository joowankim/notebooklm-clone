"""Crawl CLI commands."""

import asyncio

import rich.console
import rich.table
import typer

from src.cli import dependencies as deps
from src.cli import utils as cli_utils
from src.cli.error_handling import handle_domain_errors
from src.crawl.schema import command as command_module
from src.crawl.schema import query as query_module

console = rich.console.Console()
app = typer.Typer()

MAX_URL_DISPLAY_LENGTH = 50


@app.command("start")
def start_crawl(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    url: str = typer.Argument(..., help="Seed URL to crawl"),
    depth: int = typer.Option(2, "--depth", "-d", help="Max crawl depth"),
    max_pages: int = typer.Option(50, "--max-pages", "-m", help="Max pages to crawl"),
    include: str | None = typer.Option(None, "--include", "-i", help="URL include pattern (regex)"),
    exclude: str | None = typer.Option(None, "--exclude", "-e", help="URL exclude pattern (regex)"),
) -> None:
    """Start crawling from a seed URL."""
    asyncio.run(_start_crawl(notebook_id, url, depth, max_pages, include, exclude))


@handle_domain_errors
async def _start_crawl(
    notebook_id: str,
    url: str,
    depth: int,
    max_pages: int,
    include: str | None,
    exclude: str | None,
) -> None:
    async with cli_utils.get_session_context() as session:
        handler, background_service = deps.build_start_crawl_handler(session)
        cmd = command_module.StartCrawl(
            url=url,
            max_depth=depth,
            max_pages=max_pages,
            url_include_pattern=include,
            url_exclude_pattern=exclude,
        )
        result = await handler.handle(notebook_id, cmd)
        await session.commit()

        console.print(f"[green]Crawl job created:[/green] {result.id}")
        console.print(f"  Seed URL: {url}")
        console.print(f"  Max Depth: {depth}")
        console.print(f"  Max Pages: {max_pages}")
        console.print("[dim]Crawling in progress...[/dim]")

        await background_service.wait_for_all()
        console.print("[green]Crawl completed.[/green]")


@app.command("status")
def crawl_status(
    crawl_job_id: str = typer.Argument(..., help="Crawl Job ID"),
) -> None:
    """Get crawl job status."""
    asyncio.run(_crawl_status(crawl_job_id))


@handle_domain_errors
async def _crawl_status(crawl_job_id: str) -> None:
    async with cli_utils.get_session_context() as session:
        handler = deps.build_get_crawl_job_handler(session)
        detail = await handler.handle(crawl_job_id)

        status_style = _get_status_style(detail.status)

        console.print(f"[bold]Crawl Job:[/bold] {detail.id}")
        console.print(f"  Seed URL: {detail.seed_url}")
        console.print(f"  Domain: {detail.domain}")
        console.print(f"  Status: [{status_style}]{detail.status}[/{status_style}]")
        console.print(f"  Discovered: {detail.total_discovered}")
        console.print(f"  Ingested: {detail.total_ingested}")
        console.print(f"  Depth: {detail.max_depth} | Max Pages: {detail.max_pages}")
        if detail.error_message:
            console.print(f"  Error: [red]{detail.error_message}[/red]")
        console.print(f"  Created: {detail.created_at.strftime('%Y-%m-%d %H:%M:%S')}")


@app.command("list")
def list_crawls(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(10, "--size", "-s", help="Page size"),
) -> None:
    """List crawl jobs for a notebook."""
    asyncio.run(_list_crawls(notebook_id, page, size))


@handle_domain_errors
async def _list_crawls(notebook_id: str, page: int, size: int) -> None:
    async with cli_utils.get_session_context() as session:
        handler = deps.build_list_crawl_jobs_handler(session)
        qry = query_module.ListCrawlJobs(notebook_id=notebook_id, page=page, size=size)
        result = await handler.handle(notebook_id, qry)

        if not result.items:
            console.print("[yellow]No crawl jobs found.[/yellow]")
            return

        table = rich.table.Table(title="Crawl Jobs")
        table.add_column("ID", style="cyan")
        table.add_column("Seed URL", max_width=40)
        table.add_column("Status", style="bold")
        table.add_column("Discovered")
        table.add_column("Ingested")
        table.add_column("Created", style="dim")

        for job in result.items:
            status_style = _get_status_style(job.status)
            seed_display = _truncate_url(job.seed_url)

            table.add_row(
                job.id,
                seed_display,
                f"[{status_style}]{job.status}[/{status_style}]",
                str(job.total_discovered),
                str(job.total_ingested),
                job.created_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)
        console.print(f"Page {result.page}/{result.pages} (Total: {result.total})")


@app.command("cancel")
def cancel_crawl(
    crawl_job_id: str = typer.Argument(..., help="Crawl Job ID"),
) -> None:
    """Cancel a crawl job."""
    asyncio.run(_cancel_crawl(crawl_job_id))


@handle_domain_errors
async def _cancel_crawl(crawl_job_id: str) -> None:
    async with cli_utils.get_session_context() as session:
        handler = deps.build_cancel_crawl_handler(session)
        await handler.handle(crawl_job_id)
        await session.commit()
        console.print(f"[green]Crawl job cancelled:[/green] {crawl_job_id}")


def _get_status_style(status: str) -> str:
    """Get Rich style for crawl status."""
    styles = {
        "pending": "yellow",
        "in_progress": "blue",
        "completed": "green",
        "failed": "red",
        "cancelled": "dim",
    }
    return styles.get(status, "white")


def _truncate_url(url: str) -> str:
    """Truncate URL for display."""
    if len(url) > MAX_URL_DISPLAY_LENGTH:
        return url[:MAX_URL_DISPLAY_LENGTH] + "..."
    return url
