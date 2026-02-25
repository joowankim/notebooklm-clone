"""Conversation CLI commands."""

import asyncio

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.cli import dependencies as deps
from src.cli.error_handling import handle_domain_errors
from src.cli.utils import get_session_context
from src.conversation.schema import command as command_module
from src.conversation.schema import query as query_module

console = Console()
app = typer.Typer()


@app.command("create")
def create_conversation(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    title: str = typer.Option(None, "--title", "-t", help="Conversation title"),
):
    """Create a new conversation in a notebook."""
    asyncio.run(_create_conversation(notebook_id, title))


@handle_domain_errors
async def _create_conversation(notebook_id: str, title: str | None):
    async with get_session_context() as session:
        handler = deps.build_create_conversation_handler(session)
        cmd = command_module.CreateConversation(title=title)
        result = await handler.handle(notebook_id, cmd)
        await session.commit()

        console.print(f"[green]Conversation created:[/green] {result.id}")
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


@handle_domain_errors
async def _list_conversations(notebook_id: str, page: int, size: int):
    async with get_session_context() as session:
        handler = deps.build_list_conversations_handler(session)
        qry = query_module.ListConversations(notebook_id=notebook_id, page=page, size=size)
        result = await handler.handle(qry)

        if not result.items:
            console.print("[dim]No conversations found.[/dim]")
            return

        table = Table(title="Conversations")
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


@handle_domain_errors
async def _chat_in_conversation(conversation_id: str, message: str):
    async with get_session_context() as session:
        handler = deps.build_send_message_handler(session)
        cmd = command_module.SendMessage(content=message)

        console.print(f"[blue]You:[/blue] {message}\n")
        console.print("[dim]Generating response...[/dim]\n")

        result = await handler.handle(conversation_id, cmd)
        await session.commit()

        console.print(Panel(
            Markdown(result.assistant_message.content),
            title="Assistant",
            border_style="green",
        ))

        if result.assistant_message.citations:
            console.print("\n[bold]Citations:[/bold]")
            for citation in result.assistant_message.citations:
                console.print(
                    f"  [{citation.get('citation_index', '?')}] "
                    f"[cyan]{citation.get('document_title', 'Untitled')}[/cyan]"
                )


@app.command("show")
def show_conversation(
    conversation_id: str = typer.Argument(..., help="Conversation ID"),
):
    """Show a conversation with all messages."""
    asyncio.run(_show_conversation(conversation_id))


@handle_domain_errors
async def _show_conversation(conversation_id: str):
    async with get_session_context() as session:
        handler = deps.build_get_conversation_handler(session)
        detail = await handler.handle(conversation_id)

        console.print(Panel(
            f"[bold]{detail.title or 'Untitled Conversation'}[/bold]\n"
            f"ID: {detail.id}\n"
            f"Created: {detail.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"Messages: {len(detail.messages)}",
            title="Conversation",
            border_style="blue",
        ))

        for msg in detail.messages:
            if msg.role == "user":
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
    if not force:
        confirm = typer.confirm(f"Delete conversation {conversation_id}?")
        if not confirm:
            raise typer.Abort()

    asyncio.run(_delete_conversation(conversation_id))


@handle_domain_errors
async def _delete_conversation(conversation_id: str):
    async with get_session_context() as session:
        handler = deps.build_delete_conversation_handler(session)
        await handler.handle(conversation_id)
        await session.commit()

        console.print(f"[green]Conversation deleted:[/green] {conversation_id}")
