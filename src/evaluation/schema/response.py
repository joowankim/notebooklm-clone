"""Evaluation response schemas (output DTOs)."""

import datetime
from typing import Self

import pydantic

from src.evaluation.domain import model


class TestCaseResponse(pydantic.BaseModel):
    """Test case response."""

    id: str
    question: str
    ground_truth_chunk_ids: list[str]
    source_chunk_id: str
    created_at: datetime.datetime

    @classmethod
    def from_entity(cls, entity: model.TestCase) -> Self:
        """Create response from domain entity."""
        return cls(
            id=entity.id,
            question=entity.question,
            ground_truth_chunk_ids=list(entity.ground_truth_chunk_ids),
            source_chunk_id=entity.source_chunk_id,
            created_at=entity.created_at,
        )


class DatasetSummary(pydantic.BaseModel):
    """Evaluation dataset summary response."""

    id: str
    notebook_id: str
    name: str
    status: str
    questions_per_chunk: int
    max_chunks_sample: int
    test_case_count: int
    error_message: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @classmethod
    def from_entity(cls, entity: model.EvaluationDataset) -> Self:
        """Create response from domain entity."""
        return cls(
            id=entity.id,
            notebook_id=entity.notebook_id,
            name=entity.name,
            status=entity.status.value,
            questions_per_chunk=entity.questions_per_chunk,
            max_chunks_sample=entity.max_chunks_sample,
            test_case_count=len(entity.test_cases),
            error_message=entity.error_message,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class DatasetDetail(pydantic.BaseModel):
    """Evaluation dataset detail response with test cases."""

    id: str
    notebook_id: str
    name: str
    status: str
    questions_per_chunk: int
    max_chunks_sample: int
    test_cases: list[TestCaseResponse]
    error_message: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @classmethod
    def from_entity(cls, entity: model.EvaluationDataset) -> Self:
        """Create response from domain entity."""
        return cls(
            id=entity.id,
            notebook_id=entity.notebook_id,
            name=entity.name,
            status=entity.status.value,
            questions_per_chunk=entity.questions_per_chunk,
            max_chunks_sample=entity.max_chunks_sample,
            test_cases=[TestCaseResponse.from_entity(tc) for tc in entity.test_cases],
            error_message=entity.error_message,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class TestCaseResultResponse(pydantic.BaseModel):
    """Test case result response."""

    id: str
    test_case_id: str
    retrieved_chunk_ids: list[str]
    precision: float
    recall: float
    hit: bool
    reciprocal_rank: float

    @classmethod
    def from_entity(cls, entity: model.TestCaseResult) -> Self:
        """Create response from domain entity."""
        return cls(
            id=entity.id,
            test_case_id=entity.test_case_id,
            retrieved_chunk_ids=list(entity.retrieved_chunk_ids),
            precision=entity.precision,
            recall=entity.recall,
            hit=entity.hit,
            reciprocal_rank=entity.reciprocal_rank,
        )


class MetricsResponse(pydantic.BaseModel):
    """Aggregated metrics response."""

    precision_at_k: float
    recall_at_k: float
    hit_rate_at_k: float
    mrr: float
    k: int


class RunDetail(pydantic.BaseModel):
    """Evaluation run detail response."""

    id: str
    dataset_id: str
    status: str
    k: int
    metrics: MetricsResponse | None
    error_message: str | None
    results: list[TestCaseResultResponse]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @classmethod
    def from_entity(cls, entity: model.EvaluationRun) -> Self:
        """Create response from domain entity."""
        metrics = None
        if entity.precision_at_k is not None:
            metrics = MetricsResponse(
                precision_at_k=entity.precision_at_k,
                recall_at_k=entity.recall_at_k or 0.0,
                hit_rate_at_k=entity.hit_rate_at_k or 0.0,
                mrr=entity.mrr or 0.0,
                k=entity.k,
            )

        return cls(
            id=entity.id,
            dataset_id=entity.dataset_id,
            status=entity.status.value,
            k=entity.k,
            metrics=metrics,
            error_message=entity.error_message,
            results=[TestCaseResultResponse.from_entity(r) for r in entity.results],
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class DatasetId(pydantic.BaseModel):
    """Response containing dataset ID."""

    id: str


class RunId(pydantic.BaseModel):
    """Response containing run ID."""

    id: str
