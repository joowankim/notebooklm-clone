"""CLI application entry point."""

import rich.console
import typer

from src.cli.commands import conversation, crawl, evaluation, notebook, query, source

console = rich.console.Console()

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
app.add_typer(evaluation.app, name="evaluation", help="Evaluate retrieval quality")
app.add_typer(crawl.app, name="crawl", help="Manage URL crawling")


@app.callback()
def main() -> None:
    """NotebookLM Clone CLI."""
    pass


if __name__ == "__main__":
    app()
