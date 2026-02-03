"""Document command schemas (input DTOs)."""

import pydantic


class AddSource(pydantic.BaseModel):
    """Command to add a source URL to a notebook."""

    model_config = pydantic.ConfigDict(extra="forbid")

    url: pydantic.HttpUrl
    title: str | None = pydantic.Field(default=None, max_length=500)
