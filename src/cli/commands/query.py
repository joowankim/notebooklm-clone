"""Query CLI commands."""

import asyncio

import rich.console
import rich.markdown
import rich.panel
import typer

from src.cli import dependencies as deps
from src.cli import utils as cli_utils
from src.cli.error_handling import handle_domain_errors
from src.query.schema import command as command_module

console = rich.console.Console()
app = typer.Typer()


@app.command("ask")
def ask_query(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    question: str = typer.Argument(..., help="Question to ask"),
    max_sources: int = typer.Option(5, "--max-sources", "-m", help="Maximum sources to use"),
) -> None:
    """Query a notebook with RAG and get an answer with citations."""
    asyncio.run(_ask_query(notebook_id, question, max_sources))


@handle_domain_errors
async def _ask_query(notebook_id: str, question: str, max_sources: int) -> None:
    async with cli_utils.get_session_context() as session:
        handler = deps.build_query_notebook_handler(session)
        cmd = command_module.QueryNotebook(question=question, max_sources=max_sources)

        console.print("[dim]Querying notebook...[/dim]\n")

        answer = await handler.handle(notebook_id, cmd)

        console.print(rich.panel.Panel(
            rich.markdown.Markdown(answer.answer), title="Answer", border_style="green"
        ))

        if answer.citations:
            console.print("\n[bold]Citations:[/bold]")
            for citation in answer.citations:
                console.print(
                    f"  [{citation.citation_index}] "
                    f"[cyan]{citation.document_title or 'Untitled'}[/cyan]"
                )
                console.print(f"      URL: {citation.document_url}")
                console.print(f"      Position: chars {citation.char_start}-{citation.char_end}")
                console.print(f"      [dim]{citation.snippet[:100]}...[/dim]")
                console.print()

        console.print(f"[dim]Sources used: {answer.sources_used}[/dim]")
