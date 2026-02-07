"""Conversation query schemas."""

from src.common import pagination


class ListConversations(pagination.ListQuery):
    """Query to list conversations for a notebook."""

    notebook_id: str
