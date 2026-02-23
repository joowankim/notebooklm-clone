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
    difficulty: str | None = None
    created_at: datetime.datetime

    @classmethod
    def from_entity(cls, entity: model.TestCase) -> Self:
        """Create response from domain entity."""
        return cls(
            id=entity.id,
            question=entity.question,
            ground_truth_chunk_ids=list(entity.ground_truth_chunk_ids),
            source_chunk_id=entity.source_chunk_id,
            difficulty=entity.difficulty.value if entity.difficulty else None,
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
    answer_completeness: float | None = None

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
            ndcg=entity.ndcg,
            map_score=entity.map_score,
            generated_answer=entity.generated_answer,
            faithfulness=entity.faithfulness,
            answer_relevancy=entity.answer_relevancy,
            citation_precision=entity.citation_precision,
            citation_recall=entity.citation_recall,
            phantom_citation_count=entity.phantom_citation_count,
            citation_support_score=entity.citation_support_score,
            hallucination_rate=entity.hallucination_rate,
            contradiction_count=entity.contradiction_count,
            fabrication_count=entity.fabrication_count,
            total_claims=entity.total_claims,
            answer_completeness=entity.answer_completeness,
        )


class MetricsResponse(pydantic.BaseModel):
    """Aggregated metrics response."""

    precision_at_k: float
    recall_at_k: float
    hit_rate_at_k: float
    mrr: float
    k: int
    ndcg_at_k: float = 0.0
    map_at_k: float = 0.0


class DifficultyMetrics(pydantic.BaseModel):
    """Per-difficulty aggregated metrics response."""

    difficulty: str
    test_case_count: int
    precision_at_k: float
    recall_at_k: float
    hit_rate_at_k: float
    mrr: float
    ndcg_at_k: float = 0.0
    map_at_k: float = 0.0
    complete_context_rate: float | None = None


class ScoreDistributionResponse(pydantic.BaseModel):
    """Score distribution analysis response."""

    mean_score_gap: float | None
    high_confidence_rate: float
    mean_relevant_score: float
    mean_irrelevant_score: float


class ChunkQualityMetricsResponse(pydantic.BaseModel):
    """Single chunk quality metrics response."""

    chunk_id: str
    boundary_coherence: float
    self_containment: float
    information_density: float


class ChunkQualityReportResponse(pydantic.BaseModel):
    """Chunk quality report response."""

    notebook_id: str
    total_chunks_analyzed: int
    mean_boundary_coherence: float
    mean_self_containment: float
    mean_information_density: float
    low_quality_chunks: list[ChunkQualityMetricsResponse]


class EmbeddingQualityResponse(pydantic.BaseModel):
    """Embedding quality analysis response."""

    intra_document_similarity: float
    inter_document_similarity: float
    separation_ratio: float
    adjacent_chunk_similarity: float
    total_documents: int
    total_chunks: int


class ClaimAnalysisResponse(pydantic.BaseModel):
    """Claim-level hallucination analysis response."""

    claim_text: str
    verdict: str
    supporting_chunk_indices: list[int]
    reasoning: str


class RetrievalBucketMetricsResponse(pydantic.BaseModel):
    """Retrieval quality bucket metrics response."""

    bucket: str
    test_case_count: int
    mean_faithfulness: float
    mean_relevancy: float


class ErrorPropagationResponse(pydantic.BaseModel):
    """Error propagation analysis response."""

    recall_faithfulness_correlation: float | None
    recall_relevancy_correlation: float | None
    bucket_metrics: list[RetrievalBucketMetricsResponse]


class RunCostMetricsResponse(pydantic.BaseModel):
    """Run cost metrics response."""

    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    mean_latency_ms: float | None = None


class RunDetail(pydantic.BaseModel):
    """Evaluation run detail response."""

    id: str
    dataset_id: str
    status: str
    k: int
    evaluation_type: str = "retrieval_only"
    metrics: MetricsResponse | None
    metrics_by_difficulty: list[DifficultyMetrics] | None = None
    mean_faithfulness: float | None = None
    mean_answer_relevancy: float | None = None
    generation_model: str | None = None
    mean_citation_precision: float | None = None
    mean_citation_recall: float | None = None
    mean_hallucination_rate: float | None = None
    mean_answer_completeness: float | None = None
    score_distribution: ScoreDistributionResponse | None = None
    error_propagation: ErrorPropagationResponse | None = None
    cost_metrics: RunCostMetricsResponse | None = None
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
                ndcg_at_k=entity.ndcg_at_k or 0.0,
                map_at_k=entity.map_at_k or 0.0,
            )

        return cls(
            id=entity.id,
            dataset_id=entity.dataset_id,
            status=entity.status.value,
            k=entity.k,
            evaluation_type=entity.evaluation_type.value,
            metrics=metrics,
            mean_faithfulness=entity.mean_faithfulness,
            mean_answer_relevancy=entity.mean_answer_relevancy,
            generation_model=entity.generation_model,
            mean_citation_precision=entity.mean_citation_precision,
            mean_citation_recall=entity.mean_citation_recall,
            mean_hallucination_rate=entity.mean_hallucination_rate,
            mean_answer_completeness=entity.mean_answer_completeness,
            error_message=entity.error_message,
            results=[TestCaseResultResponse.from_entity(r) for r in entity.results],
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class RunComparisonMetrics(pydantic.BaseModel):
    """Per-run aggregate metrics for comparison."""

    run_id: str
    created_at: datetime.datetime
    evaluation_type: str
    precision_at_k: float
    recall_at_k: float
    hit_rate_at_k: float
    mrr: float
    ndcg_at_k: float = 0.0
    map_at_k: float = 0.0
    mean_faithfulness: float | None = None
    mean_answer_relevancy: float | None = None
    generation_model: str | None = None
    estimated_cost_usd: float | None = None


class TestCaseComparisonEntry(pydantic.BaseModel):
    """Per-run metrics for a single test case."""

    run_id: str
    precision: float
    recall: float
    hit: bool
    reciprocal_rank: float
    ndcg: float = 0.0
    map_score: float = 0.0
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    generated_answer: str | None = None


class TestCaseComparison(pydantic.BaseModel):
    """Comparison of a test case across multiple runs."""

    test_case_id: str
    question: str
    difficulty: str | None = None
    entries: list[TestCaseComparisonEntry]
    answer_consistency: float | None = None


class RunComparisonResponse(pydantic.BaseModel):
    """Complete run comparison response."""

    dataset_id: str
    k: int
    run_count: int
    aggregate_metrics: list[RunComparisonMetrics]
    test_case_comparisons: list[TestCaseComparison]
    mean_answer_consistency: float | None = None


class DatasetId(pydantic.BaseModel):
    """Response containing dataset ID."""

    id: str


class RunId(pydantic.BaseModel):
    """Response containing run ID."""

    id: str
