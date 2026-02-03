"""Pagination utilities."""

from typing import Generic, TypeVar

import pydantic

T = TypeVar("T")


class ListQuery(pydantic.BaseModel):
    """Base query for paginated list operations."""

    model_config = pydantic.ConfigDict(extra="forbid")

    page: int = pydantic.Field(default=1, ge=1)
    size: int = pydantic.Field(default=10, ge=1, le=100)

    @property
    def offset(self) -> int:
        """Calculate offset for pagination."""
        return (self.page - 1) * self.size


class PaginationSchema(pydantic.BaseModel, Generic[T]):
    """Generic pagination response schema."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: list[T], total: int, page: int, size: int) -> "PaginationSchema[T]":
        """Create pagination response."""
        pages = (total + size - 1) // size if size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )
