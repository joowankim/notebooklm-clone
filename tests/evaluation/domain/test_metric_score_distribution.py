"""Tests for score distribution metrics."""

from src.evaluation.domain import metric


class TestScoreGap:
    def test_clear_separation_returns_positive(self) -> None:
        # Arrange
        ids = ["a", "b", "c", "d"]
        scores = [0.9, 0.8, 0.3, 0.2]
        relevant = {"a", "b"}

        # Act
        result = metric.score_gap(ids, scores, relevant)

        # Assert
        assert result is not None
        expected = (0.9 + 0.8) / 2 - (0.3 + 0.2) / 2  # 0.85 - 0.25 = 0.6
        assert abs(result - expected) < 1e-9

    def test_no_relevant_returns_none(self) -> None:
        # Arrange
        ids = ["a", "b"]
        scores = [0.9, 0.8]
        relevant: set[str] = set()

        # Act
        result = metric.score_gap(ids, scores, relevant)

        # Assert
        assert result is None

    def test_all_relevant_returns_none(self) -> None:
        # Arrange
        ids = ["a", "b"]
        scores = [0.9, 0.8]
        relevant = {"a", "b"}

        # Act
        result = metric.score_gap(ids, scores, relevant)

        # Assert
        assert result is None

    def test_empty_retrieved_returns_none(self) -> None:
        # Arrange
        ids: list[str] = []
        scores: list[float] = []
        relevant = {"a"}

        # Act
        result = metric.score_gap(ids, scores, relevant)

        # Assert
        assert result is None

    def test_single_relevant_single_irrelevant(self) -> None:
        # Arrange
        ids = ["a", "b"]
        scores = [0.9, 0.4]
        relevant = {"a"}

        # Act
        result = metric.score_gap(ids, scores, relevant)

        # Assert
        assert result is not None
        assert abs(result - 0.5) < 1e-9


class TestHighConfidenceRate:
    def test_all_high_confidence(self) -> None:
        # Arrange
        ids = ["a", "b", "c"]
        scores = [0.9, 0.8, 0.1]
        relevant = {"a", "b"}

        # Act
        result = metric.high_confidence_rate(ids, scores, relevant)

        # Assert
        assert result == 1.0

    def test_no_high_confidence(self) -> None:
        # Arrange
        ids = ["a", "b", "c"]
        scores = [0.5, 0.5, 0.5]
        relevant = {"a"}

        # Act
        result = metric.high_confidence_rate(ids, scores, relevant)

        # Assert
        assert result == 0.0

    def test_custom_margin(self) -> None:
        # Arrange
        ids = ["a", "b"]
        scores = [0.6, 0.5]
        relevant = {"a"}

        # Act
        result_tight = metric.high_confidence_rate(ids, scores, relevant, margin=0.05)
        result_wide = metric.high_confidence_rate(ids, scores, relevant, margin=0.2)

        # Assert
        assert result_tight == 1.0
        assert result_wide == 0.0

    def test_no_relevant_returns_zero(self) -> None:
        # Arrange
        ids = ["a", "b"]
        scores = [0.9, 0.8]
        relevant: set[str] = set()

        # Act
        result = metric.high_confidence_rate(ids, scores, relevant)

        # Assert
        assert result == 0.0

    def test_all_relevant_returns_zero(self) -> None:
        # Arrange
        ids = ["a", "b"]
        scores = [0.9, 0.8]
        relevant = {"a", "b"}

        # Act
        result = metric.high_confidence_rate(ids, scores, relevant)

        # Assert
        assert result == 0.0


class TestMeanRelevantScore:
    def test_mixed_scores(self) -> None:
        # Arrange
        ids = ["a", "b", "c", "d"]
        scores = [0.9, 0.8, 0.3, 0.2]
        relevant = {"a", "b"}

        # Act
        result = metric.mean_relevant_score(ids, scores, relevant)

        # Assert
        assert abs(result - 0.85) < 1e-9

    def test_no_relevant_returns_zero(self) -> None:
        # Arrange
        ids = ["a", "b"]
        scores = [0.9, 0.8]
        relevant: set[str] = set()

        # Act
        result = metric.mean_relevant_score(ids, scores, relevant)

        # Assert
        assert result == 0.0

    def test_no_relevant_in_retrieved_returns_zero(self) -> None:
        # Arrange
        ids = ["x", "y"]
        scores = [0.9, 0.8]
        relevant = {"a", "b"}

        # Act
        result = metric.mean_relevant_score(ids, scores, relevant)

        # Assert
        assert result == 0.0


class TestMeanIrrelevantScore:
    def test_mixed_scores(self) -> None:
        # Arrange
        ids = ["a", "b", "c", "d"]
        scores = [0.9, 0.8, 0.3, 0.2]
        relevant = {"a", "b"}

        # Act
        result = metric.mean_irrelevant_score(ids, scores, relevant)

        # Assert
        assert abs(result - 0.25) < 1e-9

    def test_all_relevant_returns_zero(self) -> None:
        # Arrange
        ids = ["a", "b"]
        scores = [0.9, 0.8]
        relevant = {"a", "b"}

        # Act
        result = metric.mean_irrelevant_score(ids, scores, relevant)

        # Assert
        assert result == 0.0

    def test_no_relevant_returns_mean_of_all(self) -> None:
        # Arrange
        ids = ["a", "b"]
        scores = [0.6, 0.4]
        relevant: set[str] = set()

        # Act
        result = metric.mean_irrelevant_score(ids, scores, relevant)

        # Assert
        assert abs(result - 0.5) < 1e-9
