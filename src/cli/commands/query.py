"""Query CLI commands."""

import asyncio

import rich.console
import rich.markdown
import rich.panel
import typer

from src.cli import utils as cli_utils
from src.chunk.adapter.embedding import openai_embedding
from src.chunk.adapter import repository as chunk_repository_module
from src.document.adapter import repository as document_repository_module
from src.notebook.adapter import repository as notebook_repository_module
from src.query.adapter.pydantic_ai import agent as rag_agent_module
from src.query.service import retrieval

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


async def _ask_query(notebook_id: str, question: str, max_sources: int) -> None:
    async with cli_utils.get_session_context() as session:
        notebook = await _verify_notebook(session, notebook_id)

        console.print(f"[dim]Querying notebook '{notebook.name}'...[/dim]\n")

        # Set up services and retrieve
        retrieved = await _retrieve_chunks(session, notebook_id, question, max_sources)

        if not retrieved:
            console.print(
                "[yellow]No relevant sources found. "
                "Make sure documents have been ingested.[/yellow]"
            )
            raise typer.Exit(1)

        # Generate answer
        rag_agent = rag_agent_module.RAGAgent()
        answer = await rag_agent.answer(
            question=question,
            retrieved_chunks=retrieved,
        )

        # Display results
        _display_answer(answer)


async def _verify_notebook(
    session: object, notebook_id: str
) -> object:
    """Verify notebook exists and return it."""
    notebook_repo = notebook_repository_module.NotebookRepository(session)
    notebook = await notebook_repo.find_by_id(notebook_id)
    if notebook is None:
        console.print(f"[red]Notebook not found:[/red] {notebook_id}")
        raise typer.Exit(1)
    return notebook


async def _retrieve_chunks(
    session: object,
    notebook_id: str,
    question: str,
    max_sources: int,
) -> list[retrieval.RetrievedChunk]:
    """Set up services and retrieve relevant chunks."""
    chunk_repo = chunk_repository_module.ChunkRepository(session)
    doc_repo = document_repository_module.DocumentRepository(session)
    embedding_provider = openai_embedding.OpenAIEmbeddingProvider()
    retrieval_service = retrieval.RetrievalService(
        chunk_repository=chunk_repo,
        document_repository=doc_repo,
        embedding_provider=embedding_provider,
    )

    return await retrieval_service.retrieve(
        notebook_id=notebook_id,
        query=question,
        max_chunks=max_sources,
    )


def _display_answer(answer: object) -> None:
    """Display answer and citations."""
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
