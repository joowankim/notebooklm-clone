"""Query CLI commands."""

import asyncio

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from src.cli.utils import get_session_context

console = Console()
app = typer.Typer()


@app.command("ask")
def ask_query(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    question: str = typer.Argument(..., help="Question to ask"),
    max_sources: int = typer.Option(5, "--max-sources", "-m", help="Maximum sources to use"),
):
    """Query a notebook with RAG and get an answer with citations."""
    asyncio.run(_ask_query(notebook_id, question, max_sources))


async def _ask_query(notebook_id: str, question: str, max_sources: int):
    from src.chunk.adapter.embedding.openai_embedding import OpenAIEmbeddingProvider
    from src.chunk.adapter.repository import ChunkRepository
    from src.document.adapter.repository import DocumentRepository
    from src.notebook.adapter.repository import NotebookRepository
    from src.query.adapter.pydantic_ai.agent import RAGAgent
    from src.query.service.retrieval import RetrievalService

    async with get_session_context() as session:
        # Verify notebook exists
        notebook_repo = NotebookRepository(session)
        notebook = await notebook_repo.find_by_id(notebook_id)
        if notebook is None:
            console.print(f"[red]Notebook not found:[/red] {notebook_id}")
            raise typer.Exit(1)

        console.print(f"[dim]Querying notebook '{notebook.name}'...[/dim]\n")

        # Set up services
        chunk_repo = ChunkRepository(session)
        doc_repo = DocumentRepository(session)
        embedding_provider = OpenAIEmbeddingProvider()
        retrieval_service = RetrievalService(
            chunk_repository=chunk_repo,
            document_repository=doc_repo,
            embedding_provider=embedding_provider,
        )
        rag_agent = RAGAgent()

        # Retrieve relevant chunks
        retrieved = await retrieval_service.retrieve(
            notebook_id=notebook_id,
            query=question,
            max_chunks=max_sources,
        )

        if not retrieved:
            console.print(
                "[yellow]No relevant sources found. "
                "Make sure documents have been ingested.[/yellow]"
            )
            raise typer.Exit(1)

        # Generate answer
        answer = await rag_agent.answer(
            question=question,
            retrieved_chunks=retrieved,
        )

        # Display answer
        console.print(Panel(Markdown(answer.answer), title="Answer", border_style="green"))

        # Display citations
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
