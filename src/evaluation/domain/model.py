"""Evaluation domain entities."""

import datetime
import enum
import uuid
from typing import Self

import pydantic

from src import exceptions
from src.common import types as common_types


class DatasetStatus(enum.StrEnum):
    """Status of an evaluation dataset."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

    @property
    def is_generatable(self) -> bool:
        """Check if dataset can start generation."""
        return self == DatasetStatus.PENDING

    @property
    def is_runnable(self) -> bool:
        """Check if dataset can be used for evaluation runs."""
        return self == DatasetStatus.COMPLETED


class RunStatus(enum.StrEnum):
    """Status of an evaluation run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

    @property
    def is_runnable(self) -> bool:
        """Check if run can start."""
        return self == RunStatus.PENDING


class QuestionDifficulty(enum.StrEnum):
    """Question difficulty classification."""

    FACTUAL = "factual"
    ANALYTICAL = "analytical"
    INFERENTIAL = "inferential"
    PARAPHRASED = "paraphrased"


class EvaluationType(enum.StrEnum):
    """Type of evaluation to run."""

    RETRIEVAL_ONLY = "retrieval_only"
    FULL_RAG = "full_rag"


class RetrievalMetrics(pydantic.BaseModel):
    """Aggregated retrieval evaluation metrics."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    precision_at_k: float
    recall_at_k: float
    hit_rate_at_k: float
    mrr: float
    k: int


class TestCase(pydantic.BaseModel):
    """A single test case for retrieval evaluation."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    id: str
    question: str
    ground_truth_chunk_ids: tuple[str, ...]
    source_chunk_id: str
    difficulty: QuestionDifficulty | None = None
    created_at: datetime.datetime

    @classmethod
    def create(
        cls,
        question: str,
        ground_truth_chunk_ids: tuple[str, ...],
        source_chunk_id: str,
        difficulty: QuestionDifficulty | None = None,
    ) -> Self:
        """Factory method to create a new test case."""
        return cls(
            id=uuid.uuid4().hex,
            question=question,
            ground_truth_chunk_ids=ground_truth_chunk_ids,
            source_chunk_id=source_chunk_id,
            difficulty=difficulty,
            created_at=common_types.utc_now(),
        )


class CaseMetrics(pydantic.BaseModel):
    """Per-case retrieval metrics."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    precision: float
    recall: float
    hit: bool
    reciprocal_rank: float


class GenerationCaseMetrics(pydantic.BaseModel):
    """Per-case generation quality metrics."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    faithfulness: float
    answer_relevancy: float


class GenerationMetrics(pydantic.BaseModel):
    """Aggregated generation quality metrics."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    mean_faithfulness: float
    mean_answer_relevancy: float


class TestCaseResult(pydantic.BaseModel):
    """Result of evaluating a single test case."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    id: str
    test_case_id: str
    retrieved_chunk_ids: tuple[str, ...]
    retrieved_scores: tuple[float, ...]
    precision: float
    recall: float
    hit: bool
    reciprocal_rank: float
    generated_answer: str | None = None
    faithfulness: float | None = None
    answer_relevancy: float | None = None

    @classmethod
    def create(
        cls,
        test_case_id: str,
        retrieved_chunk_ids: tuple[str, ...],
        retrieved_scores: tuple[float, ...],
        metrics: CaseMetrics,
        generation_metrics: GenerationCaseMetrics | None = None,
        generated_answer: str | None = None,
    ) -> Self:
        """Factory method to create a test case result."""
        return cls(
            id=uuid.uuid4().hex,
            test_case_id=test_case_id,
            retrieved_chunk_ids=retrieved_chunk_ids,
            retrieved_scores=retrieved_scores,
            precision=metrics.precision,
            recall=metrics.recall,
            hit=metrics.hit,
            reciprocal_rank=metrics.reciprocal_rank,
            generated_answer=generated_answer,
            faithfulness=generation_metrics.faithfulness if generation_metrics else None,
            answer_relevancy=generation_metrics.answer_relevancy if generation_metrics else None,
        )


class EvaluationDataset(pydantic.BaseModel):
    """Dataset entity containing test cases for retrieval evaluation."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    id: str
    notebook_id: str
    name: str
    status: DatasetStatus
    questions_per_chunk: int
    max_chunks_sample: int
    error_message: str | None = None
    test_cases: tuple[TestCase, ...] = ()
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @classmethod
    def create(
        cls,
        notebook_id: str,
        name: str,
        questions_per_chunk: int = 2,
        max_chunks_sample: int = 50,
    ) -> Self:
        """Factory method to create a new evaluation dataset."""
        now = common_types.utc_now()
        return cls(
            id=uuid.uuid4().hex,
            notebook_id=notebook_id,
            name=name,
            status=DatasetStatus.PENDING,
            questions_per_chunk=questions_per_chunk,
            max_chunks_sample=max_chunks_sample,
            created_at=now,
            updated_at=now,
        )

    def mark_generating(self) -> Self:
        """Mark dataset as generating."""
        if not self.status.is_generatable:
            raise exceptions.InvalidStateError(
                f"Cannot generate dataset in status: {self.status}"
            )
        return self.model_copy(
            update={
                "status": DatasetStatus.GENERATING,
                "updated_at": common_types.utc_now(),
            }
        )

    def mark_completed(self, test_cases: tuple[TestCase, ...]) -> Self:
        """Mark dataset as completed with test cases."""
        if self.status != DatasetStatus.GENERATING:
            raise exceptions.InvalidStateError(
                f"Cannot complete dataset in status: {self.status}"
            )
        return self.model_copy(
            update={
                "status": DatasetStatus.COMPLETED,
                "test_cases": test_cases,
                "updated_at": common_types.utc_now(),
            }
        )

    def mark_failed(self, error_message: str) -> Self:
        """Mark dataset as failed."""
        if self.status != DatasetStatus.GENERATING:
            raise exceptions.InvalidStateError(
                f"Cannot fail dataset in status: {self.status}"
            )
        return self.model_copy(
            update={
                "status": DatasetStatus.FAILED,
                "error_message": error_message,
                "updated_at": common_types.utc_now(),
            }
        )


class EvaluationRun(pydantic.BaseModel):
    """An evaluation run against a dataset."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    id: str
    dataset_id: str
    status: RunStatus
    k: int
    evaluation_type: EvaluationType = EvaluationType.RETRIEVAL_ONLY
    precision_at_k: float | None = None
    recall_at_k: float | None = None
    hit_rate_at_k: float | None = None
    mrr: float | None = None
    mean_faithfulness: float | None = None
    mean_answer_relevancy: float | None = None
    error_message: str | None = None
    results: tuple[TestCaseResult, ...] = ()
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @classmethod
    def create(
        cls,
        dataset_id: str,
        k: int = 5,
        evaluation_type: EvaluationType = EvaluationType.RETRIEVAL_ONLY,
    ) -> Self:
        """Factory method to create a new evaluation run."""
        now = common_types.utc_now()
        return cls(
            id=uuid.uuid4().hex,
            dataset_id=dataset_id,
            status=RunStatus.PENDING,
            k=k,
            evaluation_type=evaluation_type,
            created_at=now,
            updated_at=now,
        )

    def mark_running(self) -> Self:
        """Mark run as running."""
        if not self.status.is_runnable:
            raise exceptions.InvalidStateError(
                f"Cannot run evaluation in status: {self.status}"
            )
        return self.model_copy(
            update={
                "status": RunStatus.RUNNING,
                "updated_at": common_types.utc_now(),
            }
        )

    def mark_completed(
        self,
        metrics: RetrievalMetrics,
        results: tuple[TestCaseResult, ...],
        generation_metrics: GenerationMetrics | None = None,
    ) -> Self:
        """Mark run as completed with metrics."""
        if self.status != RunStatus.RUNNING:
            raise exceptions.InvalidStateError(
                f"Cannot complete evaluation in status: {self.status}"
            )
        update: dict[str, object] = {
            "status": RunStatus.COMPLETED,
            "precision_at_k": metrics.precision_at_k,
            "recall_at_k": metrics.recall_at_k,
            "hit_rate_at_k": metrics.hit_rate_at_k,
            "mrr": metrics.mrr,
            "results": results,
            "updated_at": common_types.utc_now(),
        }
        if generation_metrics is not None:
            update["mean_faithfulness"] = generation_metrics.mean_faithfulness
            update["mean_answer_relevancy"] = generation_metrics.mean_answer_relevancy
        return self.model_copy(update=update)

    def mark_failed(self, error_message: str) -> Self:
        """Mark run as failed."""
        if self.status != RunStatus.RUNNING:
            raise exceptions.InvalidStateError(
                f"Cannot fail evaluation in status: {self.status}"
            )
        return self.model_copy(
            update={
                "status": RunStatus.FAILED,
                "error_message": error_message,
                "updated_at": common_types.utc_now(),
            }
        )
