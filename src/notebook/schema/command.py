"""Notebook command schemas (input DTOs)."""

import pydantic


class CreateNotebook(pydantic.BaseModel):
    """Command to create a new notebook."""

    model_config = pydantic.ConfigDict(extra="forbid")

    name: str = pydantic.Field(..., min_length=1, max_length=255)
    description: str | None = pydantic.Field(default=None, max_length=2000)


class UpdateNotebook(pydantic.BaseModel):
    """Command to update an existing notebook."""

    model_config = pydantic.ConfigDict(extra="forbid")

    name: str | None = pydantic.Field(default=None, min_length=1, max_length=255)
    description: str | None = pydantic.Field(default=None, max_length=2000)
