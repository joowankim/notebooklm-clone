"""Tests for evaluation response schemas."""

import datetime

import pytest

from src.evaluation.domain import model
from src.evaluation.schema import command, response


class TestTestCaseResponseDifficulty:
    """Tests for TestCaseResponse difficulty field."""

    def test_from_entity_with_difficulty_none(self) -> None:
        # Arrange
        entity = model.TestCase(
            id="tc1",
            question="What is AI?",
            ground_truth_chunk_ids=("chunk1", "chunk2"),
            source_chunk_id="chunk1",
            difficulty=None,
            created_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC),
        )

        # Act
        result = response.TestCaseResponse.from_entity(entity)

        # Assert
        expected = response.TestCaseResponse(
            id="tc1",
            question="What is AI?",
            ground_truth_chunk_ids=["chunk1", "chunk2"],
            source_chunk_id="chunk1",
            difficulty=None,
            created_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC),
        )
        assert result == expected

    @pytest.mark.parametrize(
        "difficulty,expected_string",
        [
            (model.QuestionDifficulty.FACTUAL, "factual"),
            (model.QuestionDifficulty.ANALYTICAL, "analytical"),
            (model.QuestionDifficulty.INFERENTIAL, "inferential"),
            (model.QuestionDifficulty.PARAPHRASED, "paraphrased"),
        ],
    )
    def test_from_entity_with_each_difficulty_value(
        self,
        difficulty: model.QuestionDifficulty,
        expected_string: str,
    ) -> None:
        # Arrange
        entity = model.TestCase(
            id="tc1",
            question="What is AI?",
            ground_truth_chunk_ids=("chunk1",),
            source_chunk_id="chunk1",
            difficulty=difficulty,
            created_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC),
        )

        # Act
        result = response.TestCaseResponse.from_entity(entity)

        # Assert
        assert result.difficulty == expected_string


class TestDifficultyMetrics:
    """Tests for DifficultyMetrics response model."""

    def test_validates_correctly_with_all_required_fields(self) -> None:
        # Arrange & Act
        metrics = response.DifficultyMetrics(
            difficulty="factual",
            test_case_count=10,
            precision_at_k=0.85,
            recall_at_k=0.90,
            hit_rate_at_k=0.95,
            mrr=0.88,
        )

        # Assert
        expected = response.DifficultyMetrics(
            difficulty="factual",
            test_case_count=10,
            precision_at_k=0.85,
            recall_at_k=0.90,
            hit_rate_at_k=0.95,
            mrr=0.88,
        )
        assert metrics == expected

    def test_missing_required_field_raises_validation_error(self) -> None:
        # Act & Assert
        with pytest.raises(Exception):
            response.DifficultyMetrics(
                difficulty="factual",
                test_case_count=10,
                precision_at_k=0.85,
                # missing recall_at_k, hit_rate_at_k, mrr
            )


class TestRunDetailDifficulty:
    """Tests for RunDetail metrics_by_difficulty field."""

    def test_metrics_by_difficulty_defaults_to_none(self) -> None:
        # Arrange & Act
        run_detail = response.RunDetail(
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
        assert run_detail.metrics_by_difficulty is None

    def test_accepts_list_of_difficulty_metrics(self) -> None:
        # Arrange
        difficulty_metrics = [
            response.DifficultyMetrics(
                difficulty="factual",
                test_case_count=5,
                precision_at_k=0.80,
                recall_at_k=0.90,
                hit_rate_at_k=0.95,
                mrr=0.85,
            ),
            response.DifficultyMetrics(
                difficulty="analytical",
                test_case_count=3,
                precision_at_k=0.60,
                recall_at_k=0.70,
                hit_rate_at_k=0.80,
                mrr=0.65,
            ),
        ]

        # Act
        run_detail = response.RunDetail(
            id="run1",
            dataset_id="ds1",
            status="completed",
            k=5,
            metrics=None,
            error_message=None,
            results=[],
            metrics_by_difficulty=difficulty_metrics,
            created_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC),
            updated_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC),
        )

        # Assert
        assert run_detail.metrics_by_difficulty is not None
        assert len(run_detail.metrics_by_difficulty) == 2
        assert run_detail.metrics_by_difficulty[0].difficulty == "factual"
        assert run_detail.metrics_by_difficulty[1].difficulty == "analytical"


class TestCompareRunsCommand:
    """Tests for CompareRuns command schema."""

    def test_valid_two_run_ids(self) -> None:
        # Act
        cmd = command.CompareRuns(run_ids=["run1", "run2"])

        # Assert
        assert cmd.run_ids == ["run1", "run2"]

    def test_min_two_run_ids_required(self) -> None:
        # Act & Assert
        with pytest.raises(Exception):
            command.CompareRuns(run_ids=["run1"])

    def test_max_ten_run_ids(self) -> None:
        # Act & Assert
        with pytest.raises(Exception):
            command.CompareRuns(run_ids=[f"run{i}" for i in range(11)])

    def test_ten_run_ids_accepted(self) -> None:
        # Act
        cmd = command.CompareRuns(run_ids=[f"run{i}" for i in range(10)])

        # Assert
        assert len(cmd.run_ids) == 10


class TestRunComparisonResponse:
    """Tests for comparison response schemas."""

    def test_run_comparison_metrics_with_generation(self) -> None:
        # Act
        metrics = response.RunComparisonMetrics(
            run_id="run1",
            created_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC),
            evaluation_type="full_rag",
            precision_at_k=0.8,
            recall_at_k=0.7,
            hit_rate_at_k=0.9,
            mrr=0.85,
            mean_faithfulness=0.9,
            mean_answer_relevancy=0.8,
        )

        # Assert
        assert metrics.run_id == "run1"
        assert metrics.mean_faithfulness == 0.9

    def test_run_comparison_metrics_without_generation(self) -> None:
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
        assert metrics.mean_faithfulness is None

    def test_test_case_comparison_structure(self) -> None:
        # Arrange
        entry1 = response.TestCaseComparisonEntry(
            run_id="run1",
            precision=0.8,
            recall=0.7,
            hit=True,
            reciprocal_rank=1.0,
        )
        entry2 = response.TestCaseComparisonEntry(
            run_id="run2",
            precision=0.6,
            recall=0.5,
            hit=True,
            reciprocal_rank=0.5,
            faithfulness=0.9,
            answer_relevancy=0.8,
            generated_answer="AI is...",
        )

        # Act
        comparison = response.TestCaseComparison(
            test_case_id="tc1",
            question="What is AI?",
            difficulty="factual",
            entries=[entry1, entry2],
        )

        # Assert
        assert len(comparison.entries) == 2
        assert comparison.entries[0].faithfulness is None
        assert comparison.entries[1].faithfulness == 0.9

    def test_full_comparison_response(self) -> None:
        # Arrange
        agg = response.RunComparisonMetrics(
            run_id="run1",
            created_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC),
            evaluation_type="retrieval_only",
            precision_at_k=0.8,
            recall_at_k=0.7,
            hit_rate_at_k=0.9,
            mrr=0.85,
        )
        tc_comp = response.TestCaseComparison(
            test_case_id="tc1",
            question="What is AI?",
            entries=[
                response.TestCaseComparisonEntry(
                    run_id="run1",
                    precision=0.8,
                    recall=0.7,
                    hit=True,
                    reciprocal_rank=1.0,
                ),
            ],
        )

        # Act
        resp = response.RunComparisonResponse(
            dataset_id="ds1",
            k=5,
            run_count=1,
            aggregate_metrics=[agg],
            test_case_comparisons=[tc_comp],
        )

        # Assert
        assert resp.dataset_id == "ds1"
        assert resp.run_count == 1
        assert len(resp.aggregate_metrics) == 1
        assert len(resp.test_case_comparisons) == 1
