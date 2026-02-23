"""Evaluation command schemas (input DTOs)."""

import pydantic

from src.evaluation.domain import model


class GenerateDataset(pydantic.BaseModel):
    """Command to generate an evaluation dataset."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    name: str = pydantic.Field(..., min_length=1, max_length=255)
    questions_per_chunk: int = pydantic.Field(default=2, ge=1, le=10)
    max_chunks_sample: int = pydantic.Field(default=50, ge=1, le=500)
    expand_ground_truth: bool = pydantic.Field(default=False)
    similarity_threshold: float = pydantic.Field(default=0.85, ge=0.5, le=1.0)
    multi_hop_ratio: float = pydantic.Field(default=0.0, ge=0.0, le=1.0)
    multi_hop_max_cases: int = pydantic.Field(default=10, ge=1, le=50)


class RunEvaluation(pydantic.BaseModel):
    """Command to run an evaluation against a dataset."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    k: int = pydantic.Field(default=5, ge=1, le=50)
    evaluation_type: model.EvaluationType = model.EvaluationType.RETRIEVAL_ONLY
    generation_model: str | None = pydantic.Field(default=None)


class CompareRuns(pydantic.BaseModel):
    """Command to compare multiple evaluation runs."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    run_ids: list[str] = pydantic.Field(..., min_length=2, max_length=10)


class EvaluateChunkQuality(pydantic.BaseModel):
    """Command to evaluate chunk quality for a notebook."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    sample_size: int = pydantic.Field(default=30, ge=5, le=200)
    low_quality_threshold: float = pydantic.Field(default=0.5, ge=0.0, le=1.0)
