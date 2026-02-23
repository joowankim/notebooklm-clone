"""Tests for evaluation command schema extensions."""

import pytest

from src.evaluation.schema import command


class TestGenerateDatasetExtensions:
    """Tests for GenerateDataset new fields."""

    def test_defaults_for_new_fields(self) -> None:
        # Arrange & Act
        cmd = command.GenerateDataset(name="test-dataset")

        # Assert
        assert cmd.expand_ground_truth is False
        assert cmd.similarity_threshold == 0.85
        assert cmd.multi_hop_ratio == 0.0
        assert cmd.multi_hop_max_cases == 10

    def test_expand_ground_truth_accepts_true(self) -> None:
        # Act
        cmd = command.GenerateDataset(
            name="test-dataset",
            expand_ground_truth=True,
        )

        # Assert
        assert cmd.expand_ground_truth is True

    def test_similarity_threshold_minimum_boundary(self) -> None:
        # Act
        cmd = command.GenerateDataset(
            name="test-dataset",
            similarity_threshold=0.5,
        )

        # Assert
        assert cmd.similarity_threshold == 0.5

    def test_similarity_threshold_maximum_boundary(self) -> None:
        # Act
        cmd = command.GenerateDataset(
            name="test-dataset",
            similarity_threshold=1.0,
        )

        # Assert
        assert cmd.similarity_threshold == 1.0

    def test_similarity_threshold_below_minimum_raises(self) -> None:
        # Act & Assert
        with pytest.raises(Exception):
            command.GenerateDataset(
                name="test-dataset",
                similarity_threshold=0.49,
            )

    def test_similarity_threshold_above_maximum_raises(self) -> None:
        # Act & Assert
        with pytest.raises(Exception):
            command.GenerateDataset(
                name="test-dataset",
                similarity_threshold=1.01,
            )

    def test_multi_hop_ratio_minimum_boundary(self) -> None:
        # Act
        cmd = command.GenerateDataset(
            name="test-dataset",
            multi_hop_ratio=0.0,
        )

        # Assert
        assert cmd.multi_hop_ratio == 0.0

    def test_multi_hop_ratio_maximum_boundary(self) -> None:
        # Act
        cmd = command.GenerateDataset(
            name="test-dataset",
            multi_hop_ratio=1.0,
        )

        # Assert
        assert cmd.multi_hop_ratio == 1.0

    def test_multi_hop_ratio_out_of_range_raises(self) -> None:
        # Act & Assert
        with pytest.raises(Exception):
            command.GenerateDataset(
                name="test-dataset",
                multi_hop_ratio=1.1,
            )

    def test_multi_hop_max_cases_minimum_boundary(self) -> None:
        # Act
        cmd = command.GenerateDataset(
            name="test-dataset",
            multi_hop_max_cases=1,
        )

        # Assert
        assert cmd.multi_hop_max_cases == 1

    def test_multi_hop_max_cases_maximum_boundary(self) -> None:
        # Act
        cmd = command.GenerateDataset(
            name="test-dataset",
            multi_hop_max_cases=50,
        )

        # Assert
        assert cmd.multi_hop_max_cases == 50

    def test_multi_hop_max_cases_out_of_range_raises(self) -> None:
        # Act & Assert
        with pytest.raises(Exception):
            command.GenerateDataset(
                name="test-dataset",
                multi_hop_max_cases=51,
            )

    def test_multi_hop_max_cases_below_minimum_raises(self) -> None:
        # Act & Assert
        with pytest.raises(Exception):
            command.GenerateDataset(
                name="test-dataset",
                multi_hop_max_cases=0,
            )


class TestRunEvaluationExtensions:
    """Tests for RunEvaluation generation_model field."""

    def test_generation_model_defaults_to_none(self) -> None:
        # Act
        cmd = command.RunEvaluation()

        # Assert
        assert cmd.generation_model is None

    def test_generation_model_accepts_string(self) -> None:
        # Act
        cmd = command.RunEvaluation(generation_model="openai:gpt-4o")

        # Assert
        assert cmd.generation_model == "openai:gpt-4o"


class TestEvaluateChunkQuality:
    """Tests for EvaluateChunkQuality command."""

    def test_defaults(self) -> None:
        # Act
        cmd = command.EvaluateChunkQuality()

        # Assert
        assert cmd.sample_size == 30
        assert cmd.low_quality_threshold == 0.5

    def test_sample_size_minimum_boundary(self) -> None:
        # Act
        cmd = command.EvaluateChunkQuality(sample_size=5)

        # Assert
        assert cmd.sample_size == 5

    def test_sample_size_maximum_boundary(self) -> None:
        # Act
        cmd = command.EvaluateChunkQuality(sample_size=200)

        # Assert
        assert cmd.sample_size == 200

    def test_sample_size_below_minimum_raises(self) -> None:
        # Act & Assert
        with pytest.raises(Exception):
            command.EvaluateChunkQuality(sample_size=4)

    def test_sample_size_above_maximum_raises(self) -> None:
        # Act & Assert
        with pytest.raises(Exception):
            command.EvaluateChunkQuality(sample_size=201)

    def test_low_quality_threshold_minimum_boundary(self) -> None:
        # Act
        cmd = command.EvaluateChunkQuality(low_quality_threshold=0.0)

        # Assert
        assert cmd.low_quality_threshold == 0.0

    def test_low_quality_threshold_maximum_boundary(self) -> None:
        # Act
        cmd = command.EvaluateChunkQuality(low_quality_threshold=1.0)

        # Assert
        assert cmd.low_quality_threshold == 1.0

    def test_low_quality_threshold_out_of_range_raises(self) -> None:
        # Act & Assert
        with pytest.raises(Exception):
            command.EvaluateChunkQuality(low_quality_threshold=1.1)

    def test_extra_fields_forbidden(self) -> None:
        # Act & Assert
        with pytest.raises(Exception):
            command.EvaluateChunkQuality(unknown_field="value")
