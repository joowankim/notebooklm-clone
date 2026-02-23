"""Tests for NDCG@k and Average Precision@k metrics."""

from src.evaluation.domain import metric


class TestNdcgAtK:
    def test_perfect_ranking_returns_one(self) -> None:
        # Arrange
        retrieved = ["a", "b", "c", "d"]
        relevant = {"a", "b"}

        # Act
        result = metric.ndcg_at_k(retrieved, relevant, k=4)

        # Assert
        assert abs(result - 1.0) < 1e-9

    def test_worst_ranking_returns_low_score(self) -> None:
        # Arrange
        retrieved = ["c", "d", "a", "b"]
        relevant = {"a", "b"}

        # Act
        result = metric.ndcg_at_k(retrieved, relevant, k=4)

        # Assert
        assert result < 1.0
        assert result > 0.0

    def test_empty_retrieved_returns_zero(self) -> None:
        # Arrange
        retrieved: list[str] = []
        relevant = {"a", "b"}

        # Act
        result = metric.ndcg_at_k(retrieved, relevant, k=3)

        # Assert
        assert result == 0.0

    def test_empty_relevant_returns_zero(self) -> None:
        # Arrange
        retrieved = ["a", "b", "c"]
        relevant: set[str] = set()

        # Act
        result = metric.ndcg_at_k(retrieved, relevant, k=3)

        # Assert
        assert result == 0.0

    def test_k_zero_returns_zero(self) -> None:
        # Arrange
        retrieved = ["a", "b"]
        relevant = {"a"}

        # Act
        result = metric.ndcg_at_k(retrieved, relevant, k=0)

        # Assert
        assert result == 0.0

    def test_single_relevant_at_top(self) -> None:
        # Arrange
        retrieved = ["a", "b", "c"]
        relevant = {"a"}

        # Act
        result = metric.ndcg_at_k(retrieved, relevant, k=3)

        # Assert
        assert abs(result - 1.0) < 1e-9

    def test_no_relevant_in_retrieved_returns_zero(self) -> None:
        # Arrange
        retrieved = ["x", "y", "z"]
        relevant = {"a", "b"}

        # Act
        result = metric.ndcg_at_k(retrieved, relevant, k=3)

        # Assert
        assert result == 0.0


class TestAveragePrecisionAtK:
    def test_perfect_ranking_returns_one(self) -> None:
        # Arrange
        retrieved = ["a", "b", "c", "d"]
        relevant = {"a", "b"}

        # Act
        result = metric.average_precision_at_k(retrieved, relevant, k=4)

        # Assert
        assert abs(result - 1.0) < 1e-9

    def test_worst_ranking_returns_low_score(self) -> None:
        # Arrange
        retrieved = ["c", "d", "a", "b"]
        relevant = {"a", "b"}

        # Act
        result = metric.average_precision_at_k(retrieved, relevant, k=4)

        # Assert
        assert result < 1.0
        assert result > 0.0

    def test_empty_retrieved_returns_zero(self) -> None:
        # Arrange
        retrieved: list[str] = []
        relevant = {"a", "b"}

        # Act
        result = metric.average_precision_at_k(retrieved, relevant, k=3)

        # Assert
        assert result == 0.0

    def test_empty_relevant_returns_zero(self) -> None:
        # Arrange
        retrieved = ["a", "b", "c"]
        relevant: set[str] = set()

        # Act
        result = metric.average_precision_at_k(retrieved, relevant, k=3)

        # Assert
        assert result == 0.0

    def test_k_zero_returns_zero(self) -> None:
        # Arrange
        retrieved = ["a", "b"]
        relevant = {"a"}

        # Act
        result = metric.average_precision_at_k(retrieved, relevant, k=0)

        # Assert
        assert result == 0.0

    def test_single_relevant_at_position_one(self) -> None:
        # Arrange
        retrieved = ["a", "b", "c"]
        relevant = {"a"}

        # Act
        result = metric.average_precision_at_k(retrieved, relevant, k=3)

        # Assert
        assert abs(result - 1.0) < 1e-9

    def test_single_relevant_at_position_three(self) -> None:
        # Arrange
        retrieved = ["x", "y", "a"]
        relevant = {"a"}

        # Act
        result = metric.average_precision_at_k(retrieved, relevant, k=3)

        # Assert
        expected = (1.0 / 3.0) / 1.0  # precision@3 * 1 / |relevant|
        assert abs(result - expected) < 1e-9

    def test_no_relevant_in_retrieved_returns_zero(self) -> None:
        # Arrange
        retrieved = ["x", "y", "z"]
        relevant = {"a", "b"}

        # Act
        result = metric.average_precision_at_k(retrieved, relevant, k=3)

        # Assert
        assert result == 0.0
