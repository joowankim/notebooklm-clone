"""Tests for domain model field extensions."""

import datetime

import pydantic
import pytest

from src.evaluation.domain import model


class TestQuestionDifficultyExtension:
    """Tests for MULTI_HOP addition to QuestionDifficulty."""

    def test_multi_hop_value(self) -> None:
        assert model.QuestionDifficulty.MULTI_HOP == "multi_hop"

    def test_all_members_count(self) -> None:
        assert len(model.QuestionDifficulty) == 5


class TestCitationMetrics:
    """Tests for CitationMetrics value object."""

    def test_create_citation_metrics(self) -> None:
        metrics = model.CitationMetrics(
            citation_precision=0.8,
            citation_recall=0.9,
            phantom_citation_count=1,
            total_citations=10,
        )
        expected = model.CitationMetrics(
            citation_precision=0.8,
            citation_recall=0.9,
            phantom_citation_count=1,
            total_citations=10,
        )
        assert metrics == expected

    def test_frozen(self) -> None:
        metrics = model.CitationMetrics(
            citation_precision=0.8,
            citation_recall=0.9,
            phantom_citation_count=1,
            total_citations=10,
        )
        with pytest.raises(pydantic.ValidationError):
            metrics.citation_precision = 0.5  # type: ignore[misc]

    def test_forbids_extra_fields(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            model.CitationMetrics(
                citation_precision=0.8,
                citation_recall=0.9,
                phantom_citation_count=1,
                total_citations=10,
                extra="nope",  # type: ignore[call-arg]
            )


class TestScoreDistributionMetrics:
    """Tests for ScoreDistributionMetrics value object."""

    def test_create_with_mean_score_gap(self) -> None:
        metrics = model.ScoreDistributionMetrics(
            mean_score_gap=0.3,
            high_confidence_rate=0.75,
            mean_relevant_score=0.85,
            mean_irrelevant_score=0.15,
        )
        expected = model.ScoreDistributionMetrics(
            mean_score_gap=0.3,
            high_confidence_rate=0.75,
            mean_relevant_score=0.85,
            mean_irrelevant_score=0.15,
        )
        assert metrics == expected

    def test_mean_score_gap_none(self) -> None:
        metrics = model.ScoreDistributionMetrics(
            mean_score_gap=None,
            high_confidence_rate=0.5,
            mean_relevant_score=0.7,
            mean_irrelevant_score=0.2,
        )
        assert metrics.mean_score_gap is None

    def test_frozen(self) -> None:
        metrics = model.ScoreDistributionMetrics(
            mean_score_gap=0.3,
            high_confidence_rate=0.75,
            mean_relevant_score=0.85,
            mean_irrelevant_score=0.15,
        )
        with pytest.raises(pydantic.ValidationError):
            metrics.high_confidence_rate = 1.0  # type: ignore[misc]


class TestChunkQualityMetrics:
    """Tests for ChunkQualityMetrics value object."""

    def test_create_chunk_quality_metrics(self) -> None:
        metrics = model.ChunkQualityMetrics(
            chunk_id="chunk_001",
            boundary_coherence=0.9,
            self_containment=0.85,
            information_density=0.7,
        )
        expected = model.ChunkQualityMetrics(
            chunk_id="chunk_001",
            boundary_coherence=0.9,
            self_containment=0.85,
            information_density=0.7,
        )
        assert metrics == expected

    def test_frozen(self) -> None:
        metrics = model.ChunkQualityMetrics(
            chunk_id="chunk_001",
            boundary_coherence=0.9,
            self_containment=0.85,
            information_density=0.7,
        )
        with pytest.raises(pydantic.ValidationError):
            metrics.chunk_id = "other"  # type: ignore[misc]


class TestChunkQualityReport:
    """Tests for ChunkQualityReport value object."""

    def test_create_chunk_quality_report(self) -> None:
        now = datetime.datetime.now(datetime.UTC)
        report = model.ChunkQualityReport(
            notebook_id="nb_001",
            total_chunks_analyzed=100,
            mean_boundary_coherence=0.88,
            mean_self_containment=0.82,
            mean_information_density=0.75,
            low_quality_chunk_ids=("chunk_3", "chunk_7"),
            created_at=now,
        )
        expected = model.ChunkQualityReport(
            notebook_id="nb_001",
            total_chunks_analyzed=100,
            mean_boundary_coherence=0.88,
            mean_self_containment=0.82,
            mean_information_density=0.75,
            low_quality_chunk_ids=("chunk_3", "chunk_7"),
            created_at=now,
        )
        assert report == expected

    def test_frozen(self) -> None:
        now = datetime.datetime.now(datetime.UTC)
        report = model.ChunkQualityReport(
            notebook_id="nb_001",
            total_chunks_analyzed=50,
            mean_boundary_coherence=0.8,
            mean_self_containment=0.8,
            mean_information_density=0.8,
            low_quality_chunk_ids=(),
            created_at=now,
        )
        with pytest.raises(pydantic.ValidationError):
            report.notebook_id = "other"  # type: ignore[misc]


class TestEmbeddingQualityMetrics:
    """Tests for EmbeddingQualityMetrics value object."""

    def test_create_embedding_quality_metrics(self) -> None:
        metrics = model.EmbeddingQualityMetrics(
            intra_document_similarity=0.85,
            inter_document_similarity=0.3,
            separation_ratio=2.83,
            adjacent_chunk_similarity=0.9,
            total_documents=10,
            total_chunks=100,
        )
        expected = model.EmbeddingQualityMetrics(
            intra_document_similarity=0.85,
            inter_document_similarity=0.3,
            separation_ratio=2.83,
            adjacent_chunk_similarity=0.9,
            total_documents=10,
            total_chunks=100,
        )
        assert metrics == expected

    def test_frozen(self) -> None:
        metrics = model.EmbeddingQualityMetrics(
            intra_document_similarity=0.85,
            inter_document_similarity=0.3,
            separation_ratio=2.83,
            adjacent_chunk_similarity=0.9,
            total_documents=10,
            total_chunks=100,
        )
        with pytest.raises(pydantic.ValidationError):
            metrics.total_documents = 20  # type: ignore[misc]


class TestRetrievalBucketMetrics:
    """Tests for RetrievalBucketMetrics value object."""

    def test_create_retrieval_bucket_metrics(self) -> None:
        metrics = model.RetrievalBucketMetrics(
            bucket="perfect",
            test_case_count=25,
            mean_faithfulness=0.95,
            mean_relevancy=0.92,
        )
        expected = model.RetrievalBucketMetrics(
            bucket="perfect",
            test_case_count=25,
            mean_faithfulness=0.95,
            mean_relevancy=0.92,
        )
        assert metrics == expected

    def test_frozen(self) -> None:
        metrics = model.RetrievalBucketMetrics(
            bucket="missed",
            test_case_count=5,
            mean_faithfulness=0.3,
            mean_relevancy=0.2,
        )
        with pytest.raises(pydantic.ValidationError):
            metrics.bucket = "partial"  # type: ignore[misc]


class TestErrorPropagationAnalysis:
    """Tests for ErrorPropagationAnalysis value object."""

    def test_create_error_propagation_analysis(self) -> None:
        bucket = model.RetrievalBucketMetrics(
            bucket="perfect",
            test_case_count=10,
            mean_faithfulness=0.9,
            mean_relevancy=0.85,
        )
        analysis = model.ErrorPropagationAnalysis(
            recall_faithfulness_correlation=0.72,
            recall_relevancy_correlation=0.68,
            bucket_metrics=(bucket,),
        )
        expected = model.ErrorPropagationAnalysis(
            recall_faithfulness_correlation=0.72,
            recall_relevancy_correlation=0.68,
            bucket_metrics=(bucket,),
        )
        assert analysis == expected

    def test_none_correlations(self) -> None:
        analysis = model.ErrorPropagationAnalysis(
            recall_faithfulness_correlation=None,
            recall_relevancy_correlation=None,
            bucket_metrics=(),
        )
        assert analysis.recall_faithfulness_correlation is None
        assert analysis.recall_relevancy_correlation is None

    def test_frozen(self) -> None:
        analysis = model.ErrorPropagationAnalysis(
            recall_faithfulness_correlation=0.5,
            recall_relevancy_correlation=0.5,
            bucket_metrics=(),
        )
        with pytest.raises(pydantic.ValidationError):
            analysis.recall_faithfulness_correlation = 0.9  # type: ignore[misc]


class TestRunCostMetrics:
    """Tests for RunCostMetrics value object."""

    def test_create_run_cost_metrics(self) -> None:
        metrics = model.RunCostMetrics(
            total_input_tokens=5000,
            total_output_tokens=1000,
            total_tokens=6000,
            estimated_cost_usd=0.05,
            mean_latency_ms=120.5,
        )
        expected = model.RunCostMetrics(
            total_input_tokens=5000,
            total_output_tokens=1000,
            total_tokens=6000,
            estimated_cost_usd=0.05,
            mean_latency_ms=120.5,
        )
        assert metrics == expected

    def test_mean_latency_defaults_to_none(self) -> None:
        metrics = model.RunCostMetrics(
            total_input_tokens=100,
            total_output_tokens=50,
            total_tokens=150,
            estimated_cost_usd=0.001,
        )
        assert metrics.mean_latency_ms is None

    def test_frozen(self) -> None:
        metrics = model.RunCostMetrics(
            total_input_tokens=100,
            total_output_tokens=50,
            total_tokens=150,
            estimated_cost_usd=0.001,
        )
        with pytest.raises(pydantic.ValidationError):
            metrics.total_tokens = 999  # type: ignore[misc]


class TestCaseMetricsExtension:
    """Tests for CaseMetrics field extensions."""

    def test_ndcg_field(self) -> None:
        metrics = model.CaseMetrics(
            precision=0.8,
            recall=0.9,
            hit=True,
            reciprocal_rank=1.0,
            ndcg=0.85,
            map_score=0.78,
        )
        assert metrics.ndcg == 0.85

    def test_map_score_field(self) -> None:
        metrics = model.CaseMetrics(
            precision=0.8,
            recall=0.9,
            hit=True,
            reciprocal_rank=1.0,
            ndcg=0.85,
            map_score=0.78,
        )
        assert metrics.map_score == 0.78

    def test_frozen(self) -> None:
        metrics = model.CaseMetrics(
            precision=0.8,
            recall=0.9,
            hit=True,
            reciprocal_rank=1.0,
            ndcg=0.85,
            map_score=0.78,
        )
        with pytest.raises(pydantic.ValidationError):
            metrics.ndcg = 0.5  # type: ignore[misc]


class TestGenerationCaseMetricsExtension:
    """Tests for GenerationCaseMetrics field extensions."""

    def test_answer_completeness_optional(self) -> None:
        metrics = model.GenerationCaseMetrics(
            faithfulness=0.9,
            answer_relevancy=0.85,
        )
        assert metrics.answer_completeness is None

    def test_answer_completeness_set(self) -> None:
        metrics = model.GenerationCaseMetrics(
            faithfulness=0.9,
            answer_relevancy=0.85,
            answer_completeness=0.75,
        )
        assert metrics.answer_completeness == 0.75


class TestRetrievalMetricsExtension:
    """Tests for RetrievalMetrics field extensions."""

    def test_ndcg_at_k_field(self) -> None:
        metrics = model.RetrievalMetrics(
            precision_at_k=0.8,
            recall_at_k=0.9,
            hit_rate_at_k=0.95,
            mrr=0.88,
            k=5,
            ndcg_at_k=0.82,
            map_at_k=0.79,
        )
        assert metrics.ndcg_at_k == 0.82

    def test_map_at_k_field(self) -> None:
        metrics = model.RetrievalMetrics(
            precision_at_k=0.8,
            recall_at_k=0.9,
            hit_rate_at_k=0.95,
            mrr=0.88,
            k=5,
            ndcg_at_k=0.82,
            map_at_k=0.79,
        )
        assert metrics.map_at_k == 0.79


class TestGenerationMetricsExtension:
    """Tests for GenerationMetrics field extensions."""

    def test_new_optional_fields_default_to_none(self) -> None:
        metrics = model.GenerationMetrics(
            mean_faithfulness=0.9,
            mean_answer_relevancy=0.85,
        )
        assert metrics.mean_citation_precision is None
        assert metrics.mean_citation_recall is None
        assert metrics.mean_phantom_citation_count is None
        assert metrics.mean_hallucination_rate is None
        assert metrics.total_contradictions is None
        assert metrics.total_fabrications is None
        assert metrics.mean_answer_completeness is None

    def test_all_new_fields_set(self) -> None:
        metrics = model.GenerationMetrics(
            mean_faithfulness=0.9,
            mean_answer_relevancy=0.85,
            mean_citation_precision=0.8,
            mean_citation_recall=0.75,
            mean_phantom_citation_count=0.5,
            mean_hallucination_rate=0.1,
            total_contradictions=2,
            total_fabrications=1,
            mean_answer_completeness=0.88,
        )
        assert metrics.mean_citation_precision == 0.8
        assert metrics.mean_citation_recall == 0.75
        assert metrics.mean_phantom_citation_count == 0.5
        assert metrics.mean_hallucination_rate == 0.1
        assert metrics.total_contradictions == 2
        assert metrics.total_fabrications == 1
        assert metrics.mean_answer_completeness == 0.88


class TestTestCaseResultExtension:
    """Tests for TestCaseResult field extensions."""

    def test_new_fields_defaults(self) -> None:
        result = model.TestCaseResult(
            id="r1",
            test_case_id="tc1",
            retrieved_chunk_ids=("c1",),
            retrieved_scores=(0.9,),
            precision=0.8,
            recall=0.9,
            hit=True,
            reciprocal_rank=1.0,
            ndcg=0.0,
            map_score=0.0,
        )
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
        assert result.claim_analyses_json is None
        assert result.answer_completeness is None

    def test_create_factory_with_new_metrics(self) -> None:
        case_metrics = model.CaseMetrics(
            precision=0.8,
            recall=0.9,
            hit=True,
            reciprocal_rank=1.0,
            ndcg=0.85,
            map_score=0.78,
        )
        citation_metrics = model.CitationMetrics(
            citation_precision=0.7,
            citation_recall=0.6,
            phantom_citation_count=2,
            total_citations=8,
        )
        gen_metrics = model.GenerationCaseMetrics(
            faithfulness=0.9,
            answer_relevancy=0.85,
            answer_completeness=0.75,
        )
        result = model.TestCaseResult.create(
            test_case_id="tc1",
            retrieved_chunk_ids=("c1", "c2"),
            retrieved_scores=(0.9, 0.8),
            metrics=case_metrics,
            generation_metrics=gen_metrics,
            generated_answer="Test answer",
            citation_metrics=citation_metrics,
            hallucination_rate=0.1,
            contradiction_count=1,
            fabrication_count=0,
            total_claims=10,
            claim_analyses_json='[{"claim": "test"}]',
            answer_completeness=0.75,
        )
        assert result.precision == 0.8
        assert result.recall == 0.9
        assert result.ndcg == 0.85
        assert result.map_score == 0.78
        assert result.citation_precision == 0.7
        assert result.citation_recall == 0.6
        assert result.phantom_citation_count == 2
        assert result.hallucination_rate == 0.1
        assert result.contradiction_count == 1
        assert result.fabrication_count == 0
        assert result.total_claims == 10
        assert result.claim_analyses_json == '[{"claim": "test"}]'
        assert result.answer_completeness == 0.75
        assert result.faithfulness == 0.9
        assert result.answer_relevancy == 0.85

    def test_create_factory_without_new_metrics(self) -> None:
        case_metrics = model.CaseMetrics(
            precision=0.8,
            recall=0.9,
            hit=True,
            reciprocal_rank=1.0,
            ndcg=0.85,
            map_score=0.78,
        )
        result = model.TestCaseResult.create(
            test_case_id="tc1",
            retrieved_chunk_ids=("c1",),
            retrieved_scores=(0.9,),
            metrics=case_metrics,
        )
        assert result.ndcg == 0.85
        assert result.map_score == 0.78
        assert result.citation_precision is None
        assert result.citation_recall is None
        assert result.hallucination_rate is None
        assert result.answer_completeness is None


class TestEvaluationDatasetExtension:
    """Tests for EvaluationDataset field extensions."""

    def test_expand_ground_truth_defaults_false(self) -> None:
        dataset = model.EvaluationDataset.create(
            notebook_id="nb1",
            name="Test Dataset",
        )
        assert dataset.expand_ground_truth is False

    def test_expand_ground_truth_set_true(self) -> None:
        dataset = model.EvaluationDataset(
            id="ds1",
            notebook_id="nb1",
            name="Test",
            status=model.DatasetStatus.PENDING,
            questions_per_chunk=2,
            max_chunks_sample=50,
            expand_ground_truth=True,
            created_at=datetime.datetime.now(datetime.UTC),
            updated_at=datetime.datetime.now(datetime.UTC),
        )
        assert dataset.expand_ground_truth is True


class TestEvaluationRunExtension:
    """Tests for EvaluationRun field extensions."""

    def test_new_fields_default_to_none(self) -> None:
        run = model.EvaluationRun.create(dataset_id="ds1")
        assert run.ndcg_at_k is None
        assert run.map_at_k is None
        assert run.mean_citation_precision is None
        assert run.mean_citation_recall is None
        assert run.mean_phantom_citation_count is None
        assert run.mean_hallucination_rate is None
        assert run.total_contradictions is None
        assert run.total_fabrications is None
        assert run.mean_answer_completeness is None
        assert run.total_input_tokens is None
        assert run.total_output_tokens is None
        assert run.estimated_cost_usd is None
        assert run.generation_model is None

    def test_mark_completed_with_extended_metrics(self) -> None:
        run = model.EvaluationRun.create(
            dataset_id="ds1",
            evaluation_type=model.EvaluationType.FULL_RAG,
        )
        running = run.mark_running()
        retrieval_metrics = model.RetrievalMetrics(
            precision_at_k=0.8,
            recall_at_k=0.9,
            hit_rate_at_k=0.95,
            mrr=0.88,
            k=5,
            ndcg_at_k=0.82,
            map_at_k=0.79,
        )
        generation_metrics = model.GenerationMetrics(
            mean_faithfulness=0.9,
            mean_answer_relevancy=0.85,
            mean_citation_precision=0.8,
            mean_citation_recall=0.75,
            mean_phantom_citation_count=0.5,
            mean_hallucination_rate=0.1,
            total_contradictions=2,
            total_fabrications=1,
            mean_answer_completeness=0.88,
        )
        completed = running.mark_completed(
            metrics=retrieval_metrics,
            results=(),
            generation_metrics=generation_metrics,
            generation_model="gpt-4o",
            total_input_tokens=5000,
            total_output_tokens=1000,
            estimated_cost_usd=0.05,
        )
        assert completed.ndcg_at_k == 0.82
        assert completed.map_at_k == 0.79
        assert completed.mean_citation_precision == 0.8
        assert completed.mean_citation_recall == 0.75
        assert completed.mean_phantom_citation_count == 0.5
        assert completed.mean_hallucination_rate == 0.1
        assert completed.total_contradictions == 2
        assert completed.total_fabrications == 1
        assert completed.mean_answer_completeness == 0.88
        assert completed.generation_model == "gpt-4o"
        assert completed.total_input_tokens == 5000
        assert completed.total_output_tokens == 1000
        assert completed.estimated_cost_usd == 0.05

    def test_mark_completed_without_extended_metrics(self) -> None:
        run = model.EvaluationRun.create(dataset_id="ds1")
        running = run.mark_running()
        retrieval_metrics = model.RetrievalMetrics(
            precision_at_k=0.8,
            recall_at_k=0.9,
            hit_rate_at_k=0.95,
            mrr=0.88,
            k=5,
            ndcg_at_k=0.82,
            map_at_k=0.79,
        )
        completed = running.mark_completed(
            metrics=retrieval_metrics,
            results=(),
        )
        assert completed.ndcg_at_k == 0.82
        assert completed.map_at_k == 0.79
        assert completed.mean_citation_precision is None
        assert completed.generation_model is None
        assert completed.total_input_tokens is None
