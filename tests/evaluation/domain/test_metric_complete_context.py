"""Tests for complete_context_rate metric."""

from src.evaluation.domain import metric


class TestCompleteContextRate:
    def test_all_relevant_in_top_k_returns_one(self) -> None:
        # Arrange
        retrieved = ["a", "b", "c", "d"]
        relevant = {"a", "b"}

        # Act
        result = metric.complete_context_rate(retrieved, relevant, k=4)

        # Assert
        assert result == 1.0

    def test_not_all_relevant_in_top_k_returns_zero(self) -> None:
        # Arrange
        retrieved = ["a", "c", "d", "b"]
        relevant = {"a", "b"}

        # Act
        result = metric.complete_context_rate(retrieved, relevant, k=2)

        # Assert
        assert result == 0.0

    def test_empty_relevant_returns_one(self) -> None:
        # Arrange
        retrieved = ["a", "b"]
        relevant: set[str] = set()

        # Act
        result = metric.complete_context_rate(retrieved, relevant, k=2)

        # Assert
        assert result == 1.0

    def test_k_zero_with_relevant_returns_zero(self) -> None:
        # Arrange
        retrieved = ["a", "b"]
        relevant = {"a"}

        # Act
        result = metric.complete_context_rate(retrieved, relevant, k=0)

        # Assert
        assert result == 0.0

    def test_k_zero_with_empty_relevant_returns_one(self) -> None:
        # Arrange
        retrieved = ["a", "b"]
        relevant: set[str] = set()

        # Act
        result = metric.complete_context_rate(retrieved, relevant, k=0)

        # Assert
        assert result == 1.0

    def test_exact_match_at_boundary(self) -> None:
        # Arrange
        retrieved = ["a", "b", "c"]
        relevant = {"a", "b", "c"}

        # Act
        result = metric.complete_context_rate(retrieved, relevant, k=3)

        # Assert
        assert result == 1.0
