"""Evaluation command schemas (input DTOs)."""

import pydantic

from src.evaluation.domain import model


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
    evaluation_type: model.EvaluationType = model.EvaluationType.RETRIEVAL_ONLY


class CompareRuns(pydantic.BaseModel):
    """Command to compare multiple evaluation runs."""

    model_config = pydantic.ConfigDict(extra="forbid")

    run_ids: list[str] = pydantic.Field(..., min_length=2, max_length=10)
