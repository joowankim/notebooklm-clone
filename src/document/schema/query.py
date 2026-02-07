"""Document query schemas."""

from src.common import pagination


class ListSources(pagination.ListQuery):
    """Query to list sources in a notebook with pagination."""

    notebook_id: str
