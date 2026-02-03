"""Notebook API schemas."""

from src.notebook.schema.command import CreateNotebook, UpdateNotebook
from src.notebook.schema.query import ListNotebooks
from src.notebook.schema.response import NotebookDetail, NotebookId

__all__ = [
    "CreateNotebook",
    "UpdateNotebook",
    "ListNotebooks",
    "NotebookDetail",
    "NotebookId",
]
