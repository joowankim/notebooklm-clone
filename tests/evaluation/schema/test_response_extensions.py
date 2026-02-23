"""Tests for evaluation response schema extensions."""

import datetime

from src.evaluation.domain import model
from src.evaluation.schema import response


class TestTestCaseResultResponseExtensions:
    """Tests for TestCaseResultResponse new fields."""

    def test_new_fields_default_values(self) -> None:
        # Act
        result = response.TestCaseResultResponse(
            id="r1",
            test_case_id="tc1",
            retrieved_chunk_ids=["c1"],
            precision=0.8,
            recall=0.7,
            hit=True,
            reciprocal_rank=1.0,
        )

        # Assert
        assert result.ndcg == 0.0
        assert result.map_score == 0.0
        assert result.citation_precision is None
        assert result.citation_recall is None
        assert result.phantom_citation_count is None
        assert result.citation_support_score is None
        assert result.hallucination_rate is None
        assert result.contradiction_count is None
        assert result.fabrication_count is None
        assert result.total_claims is None
        assert result.answer_completeness is None

    def test_new_fields_accept_values(self) -> None:
        # Act
        result = response.TestCaseResultResponse(
            id="r1",
            test_case_id="tc1",
            retrieved_chunk_ids=["c1"],
            precision=0.8,
            recall=0.7,
            hit=True,
            reciprocal_rank=1.0,
            ndcg=0.85,
            map_score=0.75,
            citation_precision=0.9,
            citation_recall=0.8,
            phantom_citation_count=2,
            citation_support_score=0.7,
            hallucination_rate=0.1,
            contradiction_count=1,
            fabrication_count=0,
            total_claims=10,
            answer_completeness=0.95,
        )

        # Assert
        assert result.ndcg == 0.85
        assert result.map_score == 0.75
        assert result.citation_precision == 0.9
        assert result.citation_recall == 0.8
        assert result.phantom_citation_count == 2
        assert result.citation_support_score == 0.7
        assert result.hallucination_rate == 0.1
        assert result.contradiction_count == 1
        assert result.fabrication_count == 0
        assert result.total_claims == 10
        assert result.answer_completeness == 0.95


class TestMetricsResponseExtensions:
    """Tests for MetricsResponse new fields."""

    def test_new_fields_default_values(self) -> None:
        # Act
        metrics = response.MetricsResponse(
            precision_at_k=0.8,
            recall_at_k=0.7,
            hit_rate_at_k=0.9,
            mrr=0.85,
            k=5,
        )

        # Assert
        assert metrics.ndcg_at_k == 0.0
        assert metrics.map_at_k == 0.0

    def test_new_fields_accept_values(self) -> None:
        # Act
        metrics = response.MetricsResponse(
            precision_at_k=0.8,
            recall_at_k=0.7,
            hit_rate_at_k=0.9,
            mrr=0.85,
            k=5,
            ndcg_at_k=0.88,
            map_at_k=0.76,
        )

        # Assert
        assert metrics.ndcg_at_k == 0.88
        assert metrics.map_at_k == 0.76


class TestDifficultyMetricsExtensions:
    """Tests for DifficultyMetrics new fields."""

    def test_new_fields_default_values(self) -> None:
        # Act
        metrics = response.DifficultyMetrics(
            difficulty="factual",
            test_case_count=10,
            precision_at_k=0.8,
            recall_at_k=0.7,
            hit_rate_at_k=0.9,
            mrr=0.85,
        )

        # Assert
        assert metrics.ndcg_at_k == 0.0
        assert metrics.map_at_k == 0.0
        assert metrics.complete_context_rate is None

    def test_new_fields_accept_values(self) -> None:
        # Act
        metrics = response.DifficultyMetrics(
            difficulty="factual",
            test_case_count=10,
            precision_at_k=0.8,
            recall_at_k=0.7,
            hit_rate_at_k=0.9,
            mrr=0.85,
            ndcg_at_k=0.88,
            map_at_k=0.76,
            complete_context_rate=0.95,
        )

        # Assert
        assert metrics.ndcg_at_k == 0.88
        assert metrics.map_at_k == 0.76
        assert metrics.complete_context_rate == 0.95


class TestRunDetailExtensions:
    """Tests for RunDetail new fields."""

    def test_new_fields_default_values(self) -> None:
        # Act
        run = response.RunDetail(
            id="run1",
            dataset_id="ds1",
            status="completed",
            k=5,
            metrics=None,
            error_message=None,
            results=[],
            created_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC),
            updated_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC),
        )

        # Assert
        assert run.generation_model is None
        assert run.mean_citation_precision is None
        assert run.mean_citation_recall is None
        assert run.mean_hallucination_rate is None
        assert run.mean_answer_completeness is None
        assert run.score_distribution is None
        assert run.error_propagation is None
        assert run.cost_metrics is None

    def test_new_fields_accept_values(self) -> None:
        # Arrange
        score_dist = response.ScoreDistributionResponse(
            mean_score_gap=0.3,
            high_confidence_rate=0.8,
            mean_relevant_score=0.9,
            mean_irrelevant_score=0.2,
        )

        # Act
        run = response.RunDetail(
            id="run1",
            dataset_id="ds1",
            status="completed",
            k=5,
            metrics=None,
            error_message=None,
            results=[],
            created_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC),
            updated_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC),
            generation_model="openai:gpt-4o",
            mean_citation_precision=0.85,
            mean_citation_recall=0.9,
            mean_hallucination_rate=0.05,
            mean_answer_completeness=0.92,
            score_distribution=score_dist,
        )

        # Assert
        assert run.generation_model == "openai:gpt-4o"
        assert run.mean_citation_precision == 0.85
        assert run.mean_citation_recall == 0.9
        assert run.mean_hallucination_rate == 0.05
        assert run.mean_answer_completeness == 0.92
        assert run.score_distribution is not None
        assert run.score_distribution.mean_score_gap == 0.3


class TestRunComparisonMetricsExtensions:
    """Tests for RunComparisonMetrics new fields."""

    def test_new_fields_default_values(self) -> None:
        # Act
        metrics = response.RunComparisonMetrics(
            run_id="run1",
            created_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC),
            evaluation_type="retrieval_only",
            precision_at_k=0.8,
            recall_at_k=0.7,
            hit_rate_at_k=0.9,
            mrr=0.85,
        )

        # Assert
        assert metrics.ndcg_at_k == 0.0
        assert metrics.map_at_k == 0.0
        assert metrics.generation_model is None
        assert metrics.estimated_cost_usd is None

    def test_new_fields_accept_values(self) -> None:
        # Act
        metrics = response.RunComparisonMetrics(
            run_id="run1",
            created_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC),
            evaluation_type="full_rag",
            precision_at_k=0.8,
            recall_at_k=0.7,
            hit_rate_at_k=0.9,
            mrr=0.85,
            ndcg_at_k=0.88,
            map_at_k=0.76,
            generation_model="openai:gpt-4o",
            estimated_cost_usd=1.25,
        )

        # Assert
        assert metrics.ndcg_at_k == 0.88
        assert metrics.map_at_k == 0.76
        assert metrics.generation_model == "openai:gpt-4o"
        assert metrics.estimated_cost_usd == 1.25


class TestTestCaseComparisonEntryExtensions:
    """Tests for TestCaseComparisonEntry new fields."""

    def test_new_fields_default_values(self) -> None:
        # Act
        entry = response.TestCaseComparisonEntry(
            run_id="run1",
            precision=0.8,
            recall=0.7,
            hit=True,
            reciprocal_rank=1.0,
        )

        # Assert
        assert entry.ndcg == 0.0
        assert entry.map_score == 0.0

    def test_new_fields_accept_values(self) -> None:
        # Act
        entry = response.TestCaseComparisonEntry(
            run_id="run1",
            precision=0.8,
            recall=0.7,
            hit=True,
            reciprocal_rank=1.0,
            ndcg=0.85,
            map_score=0.75,
        )

        # Assert
        assert entry.ndcg == 0.85
        assert entry.map_score == 0.75


class TestTestCaseComparisonExtensions:
    """Tests for TestCaseComparison new fields."""

    def test_answer_consistency_defaults_to_none(self) -> None:
        # Act
        comparison = response.TestCaseComparison(
            test_case_id="tc1",
            question="What is AI?",
            entries=[],
        )

        # Assert
        assert comparison.answer_consistency is None

    def test_answer_consistency_accepts_value(self) -> None:
        # Act
        comparison = response.TestCaseComparison(
            test_case_id="tc1",
            question="What is AI?",
            entries=[],
            answer_consistency=0.92,
        )

        # Assert
        assert comparison.answer_consistency == 0.92


class TestRunComparisonResponseExtensions:
    """Tests for RunComparisonResponse new fields."""

    def test_mean_answer_consistency_defaults_to_none(self) -> None:
        # Act
        resp = response.RunComparisonResponse(
            dataset_id="ds1",
            k=5,
            run_count=2,
            aggregate_metrics=[],
            test_case_comparisons=[],
        )

        # Assert
        assert resp.mean_answer_consistency is None

    def test_mean_answer_consistency_accepts_value(self) -> None:
        # Act
        resp = response.RunComparisonResponse(
            dataset_id="ds1",
            k=5,
            run_count=2,
            aggregate_metrics=[],
            test_case_comparisons=[],
            mean_answer_consistency=0.88,
        )

        # Assert
        assert resp.mean_answer_consistency == 0.88


class TestScoreDistributionResponse:
    """Tests for ScoreDistributionResponse model."""

    def test_creation_with_all_fields(self) -> None:
        # Act
        dist = response.ScoreDistributionResponse(
            mean_score_gap=0.4,
            high_confidence_rate=0.75,
            mean_relevant_score=0.9,
            mean_irrelevant_score=0.1,
        )

        # Assert
        expected = response.ScoreDistributionResponse(
            mean_score_gap=0.4,
            high_confidence_rate=0.75,
            mean_relevant_score=0.9,
            mean_irrelevant_score=0.1,
        )
        assert dist == expected

    def test_mean_score_gap_nullable(self) -> None:
        # Act
        dist = response.ScoreDistributionResponse(
            mean_score_gap=None,
            high_confidence_rate=0.75,
            mean_relevant_score=0.9,
            mean_irrelevant_score=0.1,
        )

        # Assert
        assert dist.mean_score_gap is None


class TestChunkQualityMetricsResponse:
    """Tests for ChunkQualityMetricsResponse model."""

    def test_creation(self) -> None:
        # Act
        metrics = response.ChunkQualityMetricsResponse(
            chunk_id="chunk1",
            boundary_coherence=0.85,
            self_containment=0.9,
            information_density=0.7,
        )

        # Assert
        expected = response.ChunkQualityMetricsResponse(
            chunk_id="chunk1",
            boundary_coherence=0.85,
            self_containment=0.9,
            information_density=0.7,
        )
        assert metrics == expected


class TestChunkQualityReportResponse:
    """Tests for ChunkQualityReportResponse model."""

    def test_creation(self) -> None:
        # Arrange
        low_quality_chunk = response.ChunkQualityMetricsResponse(
            chunk_id="chunk1",
            boundary_coherence=0.3,
            self_containment=0.4,
            information_density=0.2,
        )

        # Act
        report = response.ChunkQualityReportResponse(
            notebook_id="nb1",
            total_chunks_analyzed=100,
            mean_boundary_coherence=0.8,
            mean_self_containment=0.85,
            mean_information_density=0.75,
            low_quality_chunks=[low_quality_chunk],
        )

        # Assert
        assert report.notebook_id == "nb1"
        assert report.total_chunks_analyzed == 100
        assert len(report.low_quality_chunks) == 1
        assert report.low_quality_chunks[0].chunk_id == "chunk1"


class TestEmbeddingQualityResponse:
    """Tests for EmbeddingQualityResponse model."""

    def test_creation(self) -> None:
        # Act
        quality = response.EmbeddingQualityResponse(
            intra_document_similarity=0.8,
            inter_document_similarity=0.3,
            separation_ratio=2.67,
            adjacent_chunk_similarity=0.75,
            total_documents=10,
            total_chunks=100,
        )

        # Assert
        expected = response.EmbeddingQualityResponse(
            intra_document_similarity=0.8,
            inter_document_similarity=0.3,
            separation_ratio=2.67,
            adjacent_chunk_similarity=0.75,
            total_documents=10,
            total_chunks=100,
        )
        assert quality == expected


class TestClaimAnalysisResponse:
    """Tests for ClaimAnalysisResponse model."""

    def test_creation(self) -> None:
        # Act
        claim = response.ClaimAnalysisResponse(
            claim_text="AI is a branch of CS.",
            verdict="supported",
            supporting_chunk_indices=[0, 1],
            reasoning="Directly stated in context.",
        )

        # Assert
        expected = response.ClaimAnalysisResponse(
            claim_text="AI is a branch of CS.",
            verdict="supported",
            supporting_chunk_indices=[0, 1],
            reasoning="Directly stated in context.",
        )
        assert claim == expected


class TestRetrievalBucketMetricsResponse:
    """Tests for RetrievalBucketMetricsResponse model."""

    def test_creation(self) -> None:
        # Act
        bucket = response.RetrievalBucketMetricsResponse(
            bucket="high",
            test_case_count=25,
            mean_faithfulness=0.9,
            mean_relevancy=0.85,
        )

        # Assert
        expected = response.RetrievalBucketMetricsResponse(
            bucket="high",
            test_case_count=25,
            mean_faithfulness=0.9,
            mean_relevancy=0.85,
        )
        assert bucket == expected


class TestErrorPropagationResponse:
    """Tests for ErrorPropagationResponse model."""

    def test_creation(self) -> None:
        # Arrange
        bucket = response.RetrievalBucketMetricsResponse(
            bucket="high",
            test_case_count=25,
            mean_faithfulness=0.9,
            mean_relevancy=0.85,
        )

        # Act
        error_prop = response.ErrorPropagationResponse(
            recall_faithfulness_correlation=0.72,
            recall_relevancy_correlation=0.68,
            bucket_metrics=[bucket],
        )

        # Assert
        assert error_prop.recall_faithfulness_correlation == 0.72
        assert error_prop.recall_relevancy_correlation == 0.68
        assert len(error_prop.bucket_metrics) == 1

    def test_nullable_correlations(self) -> None:
        # Act
        error_prop = response.ErrorPropagationResponse(
            recall_faithfulness_correlation=None,
            recall_relevancy_correlation=None,
            bucket_metrics=[],
        )

        # Assert
        assert error_prop.recall_faithfulness_correlation is None
        assert error_prop.recall_relevancy_correlation is None


class TestRunCostMetricsResponse:
    """Tests for RunCostMetricsResponse model."""

    def test_creation(self) -> None:
        # Act
        cost = response.RunCostMetricsResponse(
            total_input_tokens=50000,
            total_output_tokens=10000,
            total_tokens=60000,
            estimated_cost_usd=0.45,
            mean_latency_ms=250.0,
        )

        # Assert
        expected = response.RunCostMetricsResponse(
            total_input_tokens=50000,
            total_output_tokens=10000,
            total_tokens=60000,
            estimated_cost_usd=0.45,
            mean_latency_ms=250.0,
        )
        assert cost == expected

    def test_mean_latency_defaults_to_none(self) -> None:
        # Act
        cost = response.RunCostMetricsResponse(
            total_input_tokens=50000,
            total_output_tokens=10000,
            total_tokens=60000,
            estimated_cost_usd=0.45,
        )

        # Assert
        assert cost.mean_latency_ms is None
