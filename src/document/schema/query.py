"""Document query schemas."""

from src.common import ListQuery


class ListSources(ListQuery):
    """Query to list sources in a notebook with pagination."""

    notebook_id: str
