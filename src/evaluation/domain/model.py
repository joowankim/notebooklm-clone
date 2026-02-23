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
    MULTI_HOP = "multi_hop"


class EvaluationType(enum.StrEnum):
    """Type of evaluation to run."""

    RETRIEVAL_ONLY = "retrieval_only"
    FULL_RAG = "full_rag"


class ClaimVerdict(enum.StrEnum):
    """Verdict for a single claim in hallucination analysis."""

    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    CONTRADICTED = "contradicted"
    FABRICATED = "fabricated"
    UNVERIFIABLE = "unverifiable"


class CitationMetrics(pydantic.BaseModel):
    """Citation quality metrics for a generated answer."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    citation_precision: float
    citation_recall: float
    phantom_citation_count: int
    total_citations: int


class ClaimAnalysis(pydantic.BaseModel):
    """Analysis of a single claim against source chunks."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    claim_text: str
    verdict: ClaimVerdict
    supporting_chunk_indices: tuple[int, ...]
    reasoning: str


class HallucinationAnalysis(pydantic.BaseModel):
    """Aggregated hallucination analysis for a generated answer."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    claims: tuple[ClaimAnalysis, ...]
    total_claims: int
    supported_count: int
    partially_supported_count: int
    contradicted_count: int
    fabricated_count: int
    unverifiable_count: int
    hallucination_rate: float
    faithfulness_score: float


class ScoreDistributionMetrics(pydantic.BaseModel):
    """Score distribution metrics for retrieval results."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    mean_score_gap: float | None
    high_confidence_rate: float
    mean_relevant_score: float
    mean_irrelevant_score: float


class ChunkQualityMetrics(pydantic.BaseModel):
    """Quality metrics for a single chunk."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    chunk_id: str
    boundary_coherence: float
    self_containment: float
    information_density: float


class ChunkQualityReport(pydantic.BaseModel):
    """Quality report for all chunks in a notebook."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    notebook_id: str
    total_chunks_analyzed: int
    mean_boundary_coherence: float
    mean_self_containment: float
    mean_information_density: float
    low_quality_chunk_ids: tuple[str, ...]
    created_at: datetime.datetime


class EmbeddingQualityMetrics(pydantic.BaseModel):
    """Quality metrics for embedding space analysis."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    intra_document_similarity: float
    inter_document_similarity: float
    separation_ratio: float
    adjacent_chunk_similarity: float
    total_documents: int
    total_chunks: int


class RetrievalBucketMetrics(pydantic.BaseModel):
    """Metrics for a retrieval quality bucket."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    bucket: str
    test_case_count: int
    mean_faithfulness: float
    mean_relevancy: float


class ErrorPropagationAnalysis(pydantic.BaseModel):
    """Analysis of error propagation from retrieval to generation."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    recall_faithfulness_correlation: float | None
    recall_relevancy_correlation: float | None
    bucket_metrics: tuple[RetrievalBucketMetrics, ...]


class RunCostMetrics(pydantic.BaseModel):
    """Cost and latency metrics for an evaluation run."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    mean_latency_ms: float | None = None


class RetrievalMetrics(pydantic.BaseModel):
    """Aggregated retrieval evaluation metrics."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    precision_at_k: float
    recall_at_k: float
    hit_rate_at_k: float
    mrr: float
    k: int
    ndcg_at_k: float = 0.0
    map_at_k: float = 0.0


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
    ndcg: float = 0.0
    map_score: float = 0.0


class GenerationCaseMetrics(pydantic.BaseModel):
    """Per-case generation quality metrics."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    faithfulness: float
    answer_relevancy: float
    answer_completeness: float | None = None


class GenerationMetrics(pydantic.BaseModel):
    """Aggregated generation quality metrics."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    mean_faithfulness: float
    mean_answer_relevancy: float
    mean_citation_precision: float | None = None
    mean_citation_recall: float | None = None
    mean_phantom_citation_count: float | None = None
    mean_hallucination_rate: float | None = None
    total_contradictions: int | None = None
    total_fabrications: int | None = None
    mean_answer_completeness: float | None = None


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
    ndcg: float = 0.0
    map_score: float = 0.0
    generated_answer: str | None = None
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    citation_precision: float | None = None
    citation_recall: float | None = None
    phantom_citation_count: int | None = None
    citation_support_score: float | None = None
    hallucination_rate: float | None = None
    contradiction_count: int | None = None
    fabrication_count: int | None = None
    total_claims: int | None = None
    claim_analyses_json: str | None = None
    answer_completeness: float | None = None

    @classmethod
    def create(
        cls,
        test_case_id: str,
        retrieved_chunk_ids: tuple[str, ...],
        retrieved_scores: tuple[float, ...],
        metrics: CaseMetrics,
        generation_metrics: GenerationCaseMetrics | None = None,
        generated_answer: str | None = None,
        citation_metrics: CitationMetrics | None = None,
        hallucination_rate: float | None = None,
        contradiction_count: int | None = None,
        fabrication_count: int | None = None,
        total_claims: int | None = None,
        claim_analyses_json: str | None = None,
        answer_completeness: float | None = None,
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
            ndcg=metrics.ndcg,
            map_score=metrics.map_score,
            generated_answer=generated_answer,
            faithfulness=generation_metrics.faithfulness if generation_metrics else None,
            answer_relevancy=generation_metrics.answer_relevancy if generation_metrics else None,
            citation_precision=citation_metrics.citation_precision if citation_metrics else None,
            citation_recall=citation_metrics.citation_recall if citation_metrics else None,
            phantom_citation_count=citation_metrics.phantom_citation_count if citation_metrics else None,
            hallucination_rate=hallucination_rate,
            contradiction_count=contradiction_count,
            fabrication_count=fabrication_count,
            total_claims=total_claims,
            claim_analyses_json=claim_analyses_json,
            answer_completeness=answer_completeness,
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
    expand_ground_truth: bool = False
    similarity_threshold: float | None = 0.85
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
    ndcg_at_k: float | None = None
    map_at_k: float | None = None
    mean_faithfulness: float | None = None
    mean_answer_relevancy: float | None = None
    mean_citation_precision: float | None = None
    mean_citation_recall: float | None = None
    mean_phantom_citation_count: float | None = None
    mean_hallucination_rate: float | None = None
    total_contradictions: int | None = None
    total_fabrications: int | None = None
    mean_answer_completeness: float | None = None
    total_input_tokens: int | None = None
    total_output_tokens: int | None = None
    estimated_cost_usd: float | None = None
    generation_model: str | None = None
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
        generation_model: str | None = None,
        total_input_tokens: int | None = None,
        total_output_tokens: int | None = None,
        estimated_cost_usd: float | None = None,
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
            "ndcg_at_k": metrics.ndcg_at_k,
            "map_at_k": metrics.map_at_k,
            "results": results,
            "updated_at": common_types.utc_now(),
        }
        if generation_metrics is not None:
            update["mean_faithfulness"] = generation_metrics.mean_faithfulness
            update["mean_answer_relevancy"] = generation_metrics.mean_answer_relevancy
            update["mean_citation_precision"] = generation_metrics.mean_citation_precision
            update["mean_citation_recall"] = generation_metrics.mean_citation_recall
            update["mean_phantom_citation_count"] = generation_metrics.mean_phantom_citation_count
            update["mean_hallucination_rate"] = generation_metrics.mean_hallucination_rate
            update["total_contradictions"] = generation_metrics.total_contradictions
            update["total_fabrications"] = generation_metrics.total_fabrications
            update["mean_answer_completeness"] = generation_metrics.mean_answer_completeness
        if generation_model is not None:
            update["generation_model"] = generation_model
        if total_input_tokens is not None:
            update["total_input_tokens"] = total_input_tokens
        if total_output_tokens is not None:
            update["total_output_tokens"] = total_output_tokens
        if estimated_cost_usd is not None:
            update["estimated_cost_usd"] = estimated_cost_usd
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
