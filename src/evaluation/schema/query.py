"""Evaluation query schemas."""

import pydantic


class ListDatasets(pydantic.BaseModel):
    """Query to list evaluation datasets for a notebook."""

    model_config = pydantic.ConfigDict(extra="forbid")

    notebook_id: str
