"""Conversation CLI commands."""

import asyncio

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.cli.utils import get_session_context

console = Console()
app = typer.Typer()


@app.command("create")
def create_conversation(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    title: str = typer.Option(None, "--title", "-t", help="Conversation title"),
):
    """Create a new conversation in a notebook."""
    asyncio.run(_create_conversation(notebook_id, title))


async def _create_conversation(notebook_id: str, title: str | None):
    from src.conversation.adapter.repository import ConversationRepository
    from src.conversation.domain.model import Conversation
    from src.notebook.adapter.repository import NotebookRepository
    import datetime
    import uuid

    async with get_session_context() as session:
        # Verify notebook exists
        notebook_repo = NotebookRepository(session)
        notebook = await notebook_repo.find_by_id(notebook_id)
        if notebook is None:
            console.print(f"[red]Notebook not found:[/red] {notebook_id}")
            raise typer.Exit(1)

        # Create conversation
        now = datetime.datetime.now(datetime.timezone.utc)
        conversation = Conversation(
            id=uuid.uuid4().hex,
            notebook_id=notebook_id,
            title=title,
            messages=(),
            created_at=now,
            updated_at=now,
        )

        conversation_repo = ConversationRepository(session)
        await conversation_repo.save(conversation)
        await session.commit()

        console.print(f"[green]Conversation created:[/green] {conversation.id}")
        if title:
            console.print(f"  Title: {title}")


@app.command("list")
def list_conversations(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(10, "--size", "-s", help="Page size"),
):
    """List conversations in a notebook."""
    asyncio.run(_list_conversations(notebook_id, page, size))


async def _list_conversations(notebook_id: str, page: int, size: int):
    from src.common import ListQuery
    from src.conversation.adapter.repository import ConversationRepository
    from src.notebook.adapter.repository import NotebookRepository

    async with get_session_context() as session:
        # Verify notebook exists
        notebook_repo = NotebookRepository(session)
        notebook = await notebook_repo.find_by_id(notebook_id)
        if notebook is None:
            console.print(f"[red]Notebook not found:[/red] {notebook_id}")
            raise typer.Exit(1)

        # List conversations
        conversation_repo = ConversationRepository(session)
        result = await conversation_repo.list_by_notebook(
            notebook_id=notebook_id,
            query=ListQuery(page=page, size=size),
        )

        if not result.items:
            console.print("[dim]No conversations found.[/dim]")
            return

        table = Table(title=f"Conversations for '{notebook.name}'")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="green")
        table.add_column("Messages", justify="right")
        table.add_column("Updated", style="dim")

        for conv in result.items:
            table.add_row(
                conv.id[:12] + "...",
                conv.title or "[dim]Untitled[/dim]",
                str(len(conv.messages)),
                conv.updated_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)
        console.print(f"\n[dim]Page {result.page}/{result.pages} (Total: {result.total})[/dim]")


@app.command("chat")
def chat_in_conversation(
    conversation_id: str = typer.Argument(..., help="Conversation ID"),
    message: str = typer.Argument(..., help="Message to send"),
):
    """Send a message in a conversation and get AI response."""
    asyncio.run(_chat_in_conversation(conversation_id, message))


async def _chat_in_conversation(conversation_id: str, message: str):
    import datetime
    import uuid

    from src.chunk.adapter.embedding.openai_embedding import OpenAIEmbeddingProvider
    from src.chunk.adapter.repository import ChunkRepository
    from src.conversation.adapter.repository import ConversationRepository
    from src.conversation.domain.model import Message, MessageRole
    from src.document.adapter.repository import DocumentRepository
    from src.query.adapter.pydantic_ai.agent import RAGAgent
    from src.query.service.retrieval import RetrievalService

    async with get_session_context() as session:
        # Get conversation
        conversation_repo = ConversationRepository(session)
        conversation = await conversation_repo.find_by_id(conversation_id)
        if conversation is None:
            console.print(f"[red]Conversation not found:[/red] {conversation_id}")
            raise typer.Exit(1)

        now = datetime.datetime.now(datetime.timezone.utc)

        # Create user message
        user_message = Message(
            id=uuid.uuid4().hex,
            role=MessageRole.USER,
            content=message,
            citations=None,
            created_at=now,
        )

        # Add user message to conversation
        conversation = conversation.add_message(user_message)
        await conversation_repo.add_message(conversation_id, user_message)

        # Update conversation title if needed
        if len(conversation.messages) == 1:
            await conversation_repo.save(conversation)

        console.print(f"[blue]You:[/blue] {message}\n")
        console.print("[dim]Generating response...[/dim]\n")

        # Get conversation context for RAG
        conversation_context = conversation.get_context_for_rag(max_turns=5)

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
            notebook_id=conversation.notebook_id,
            query=message,
            max_chunks=10,
        )

        # Generate answer with conversation context
        answer = await rag_agent.answer(
            question=message,
            retrieved_chunks=retrieved,
            conversation_history=conversation_context[:-1],
        )

        # Create assistant message
        assistant_message = Message(
            id=uuid.uuid4().hex,
            role=MessageRole.ASSISTANT,
            content=answer.answer,
            citations=[c.model_dump() for c in answer.citations] if answer.citations else None,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )

        # Add assistant message
        await conversation_repo.add_message(conversation_id, assistant_message)
        await session.commit()

        # Display answer
        console.print(Panel(Markdown(answer.answer), title="Assistant", border_style="green"))

        # Display citations
        if answer.citations:
            console.print("\n[bold]Citations:[/bold]")
            for citation in answer.citations:
                console.print(
                    f"  [{citation.citation_index}] "
                    f"[cyan]{citation.document_title or 'Untitled'}[/cyan]"
                )


@app.command("show")
def show_conversation(
    conversation_id: str = typer.Argument(..., help="Conversation ID"),
):
    """Show a conversation with all messages."""
    asyncio.run(_show_conversation(conversation_id))


async def _show_conversation(conversation_id: str):
    from src.conversation.adapter.repository import ConversationRepository

    async with get_session_context() as session:
        conversation_repo = ConversationRepository(session)
        conversation = await conversation_repo.find_by_id(conversation_id)
        if conversation is None:
            console.print(f"[red]Conversation not found:[/red] {conversation_id}")
            raise typer.Exit(1)

        console.print(Panel(
            f"[bold]{conversation.title or 'Untitled Conversation'}[/bold]\n"
            f"ID: {conversation.id}\n"
            f"Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"Messages: {len(conversation.messages)}",
            title="Conversation",
            border_style="blue",
        ))

        for msg in conversation.messages:
            if msg.role.value == "user":
                console.print(f"\n[blue]You:[/blue] {msg.content}")
            else:
                console.print(Panel(
                    Markdown(msg.content),
                    title="Assistant",
                    border_style="green",
                ))


@app.command("delete")
def delete_conversation(
    conversation_id: str = typer.Argument(..., help="Conversation ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a conversation."""
    asyncio.run(_delete_conversation(conversation_id, force))


async def _delete_conversation(conversation_id: str, force: bool):
    from src.conversation.adapter.repository import ConversationRepository

    async with get_session_context() as session:
        conversation_repo = ConversationRepository(session)
        conversation = await conversation_repo.find_by_id(conversation_id)
        if conversation is None:
            console.print(f"[red]Conversation not found:[/red] {conversation_id}")
            raise typer.Exit(1)

        if not force:
            confirm = typer.confirm(
                f"Delete conversation '{conversation.title or 'Untitled'}'?"
            )
            if not confirm:
                raise typer.Abort()

        await conversation_repo.delete(conversation_id)
        await session.commit()

        console.print(f"[green]Conversation deleted:[/green] {conversation_id}")
