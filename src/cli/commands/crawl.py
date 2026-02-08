"""Crawl CLI commands."""

import asyncio

import rich.console
import rich.table
import typer

from src.cli import utils as cli_utils
from src.common import pagination
from src.crawl.adapter import repository as crawl_repo_module
from src.crawl.domain import model as crawl_model
from src.notebook.adapter import repository as notebook_repo_module

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


async def _start_crawl(
    notebook_id: str,
    url: str,
    depth: int,
    max_pages: int,
    include: str | None,
    exclude: str | None,
) -> None:
    async with cli_utils.get_session_context() as session:
        notebook_repo = notebook_repo_module.NotebookRepository(session)
        notebook = await notebook_repo.find_by_id(notebook_id)
        if notebook is None:
            console.print(f"[red]Notebook not found:[/red] {notebook_id}")
            raise typer.Exit(1)

        crawl_repo = crawl_repo_module.CrawlJobRepository(session)
        job = crawl_model.CrawlJob.create(
            notebook_id=notebook_id,
            seed_url=url,
            max_depth=depth,
            max_pages=max_pages,
            url_include_pattern=include,
            url_exclude_pattern=exclude,
        )
        saved = await crawl_repo.save(job)
        await session.commit()

        console.print(f"[green]Crawl job created:[/green] {saved.id}")
        console.print(f"  Seed URL: {saved.seed_url}")
        console.print(f"  Domain: {saved.domain}")
        console.print(f"  Max Depth: {saved.max_depth}")
        console.print(f"  Max Pages: {saved.max_pages}")
        console.print("[dim]Note: Background crawling runs via the API server.[/dim]")


@app.command("status")
def crawl_status(
    crawl_job_id: str = typer.Argument(..., help="Crawl Job ID"),
) -> None:
    """Get crawl job status."""
    asyncio.run(_crawl_status(crawl_job_id))


async def _crawl_status(crawl_job_id: str) -> None:
    async with cli_utils.get_session_context() as session:
        repo = crawl_repo_module.CrawlJobRepository(session)
        job = await repo.find_by_id(crawl_job_id)

        if job is None:
            console.print(f"[red]Crawl job not found:[/red] {crawl_job_id}")
            raise typer.Exit(1)

        status_style = _get_status_style(job.status.value)

        console.print(f"[bold]Crawl Job:[/bold] {job.id}")
        console.print(f"  Seed URL: {job.seed_url}")
        console.print(f"  Domain: {job.domain}")
        console.print(f"  Status: [{status_style}]{job.status.value}[/{status_style}]")
        console.print(f"  Discovered: {job.total_discovered}")
        console.print(f"  Ingested: {job.total_ingested}")
        console.print(f"  Depth: {job.max_depth} | Max Pages: {job.max_pages}")
        if job.error_message:
            console.print(f"  Error: [red]{job.error_message}[/red]")
        console.print(f"  Created: {job.created_at.strftime('%Y-%m-%d %H:%M:%S')}")


@app.command("list")
def list_crawls(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(10, "--size", "-s", help="Page size"),
) -> None:
    """List crawl jobs for a notebook."""
    asyncio.run(_list_crawls(notebook_id, page, size))


async def _list_crawls(notebook_id: str, page: int, size: int) -> None:
    async with cli_utils.get_session_context() as session:
        notebook_repo = notebook_repo_module.NotebookRepository(session)
        notebook = await notebook_repo.find_by_id(notebook_id)
        if notebook is None:
            console.print(f"[red]Notebook not found:[/red] {notebook_id}")
            raise typer.Exit(1)

        crawl_repo = crawl_repo_module.CrawlJobRepository(session)
        result = await crawl_repo.list_by_notebook(
            notebook_id, pagination.ListQuery(page=page, size=size)
        )

        if not result.items:
            console.print("[yellow]No crawl jobs found.[/yellow]")
            return

        table = rich.table.Table(title=f"Crawl Jobs for '{notebook.name}'")
        table.add_column("ID", style="cyan")
        table.add_column("Seed URL", max_width=40)
        table.add_column("Status", style="bold")
        table.add_column("Discovered")
        table.add_column("Ingested")
        table.add_column("Created", style="dim")

        for job in result.items:
            status_style = _get_status_style(job.status.value)
            seed_display = _truncate_url(job.seed_url)

            table.add_row(
                job.id,
                seed_display,
                f"[{status_style}]{job.status.value}[/{status_style}]",
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


async def _cancel_crawl(crawl_job_id: str) -> None:
    async with cli_utils.get_session_context() as session:
        repo = crawl_repo_module.CrawlJobRepository(session)
        job = await repo.find_by_id(crawl_job_id)

        if job is None:
            console.print(f"[red]Crawl job not found:[/red] {crawl_job_id}")
            raise typer.Exit(1)

        if not job.status.can_cancel:
            console.print(
                f"[red]Cannot cancel crawl job in status:[/red] {job.status.value}"
            )
            raise typer.Exit(1)

        cancelled = job.mark_cancelled()
        await repo.save(cancelled)
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
