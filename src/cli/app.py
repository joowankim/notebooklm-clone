"""CLI application entry point."""

import typer
from rich.console import Console

from src.cli.commands import conversation, notebook, query, source

console = Console()

app = typer.Typer(
    name="ntlm",
    help="NotebookLM Clone - Document Research System with RAG",
    add_completion=False,
)

# Add subcommands
app.add_typer(notebook.app, name="notebook", help="Manage notebooks")
app.add_typer(source.app, name="source", help="Manage sources")
app.add_typer(query.app, name="query", help="Query notebooks")
app.add_typer(conversation.app, name="conversation", help="Manage conversations")


@app.callback()
def main():
    """NotebookLM Clone CLI."""
    pass


if __name__ == "__main__":
    app()
