"""Document API schemas."""

from src.document.schema.command import AddSource
from src.document.schema.query import ListSources
from src.document.schema.response import DocumentDetail, DocumentId

__all__ = [
    "AddSource",
    "ListSources",
    "DocumentDetail",
    "DocumentId",
]
