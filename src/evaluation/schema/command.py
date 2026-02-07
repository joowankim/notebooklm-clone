"""Evaluation command schemas (input DTOs)."""

import pydantic


class GenerateDataset(pydantic.BaseModel):
    """Command to generate an evaluation dataset."""

    model_config = pydantic.ConfigDict(extra="forbid")

    name: str = pydantic.Field(..., min_length=1, max_length=255)
    questions_per_chunk: int = pydantic.Field(default=2, ge=1, le=10)
    max_chunks_sample: int = pydantic.Field(default=50, ge=1, le=500)


class RunEvaluation(pydantic.BaseModel):
    """Command to run an evaluation against a dataset."""

    model_config = pydantic.ConfigDict(extra="forbid")

    k: int = pydantic.Field(default=5, ge=1, le=50)
