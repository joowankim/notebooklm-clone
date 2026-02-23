"""Tests for cosine_similarity metric."""

from src.evaluation.domain import metric


class TestCosineSimilarity:
    def test_identical_vectors_returns_one(self) -> None:
        # Arrange
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [1.0, 0.0, 0.0]

        # Act
        result = metric.cosine_similarity(vec_a, vec_b)

        # Assert
        assert result == 1.0

    def test_orthogonal_vectors_returns_zero(self) -> None:
        # Arrange
        vec_a = [1.0, 0.0]
        vec_b = [0.0, 1.0]

        # Act
        result = metric.cosine_similarity(vec_a, vec_b)

        # Assert
        assert abs(result - 0.0) < 1e-9

    def test_zero_vector_a_returns_zero(self) -> None:
        # Arrange
        vec_a = [0.0, 0.0, 0.0]
        vec_b = [1.0, 2.0, 3.0]

        # Act
        result = metric.cosine_similarity(vec_a, vec_b)

        # Assert
        assert result == 0.0

    def test_zero_vector_b_returns_zero(self) -> None:
        # Arrange
        vec_a = [1.0, 2.0, 3.0]
        vec_b = [0.0, 0.0, 0.0]

        # Act
        result = metric.cosine_similarity(vec_a, vec_b)

        # Assert
        assert result == 0.0

    def test_anti_parallel_vectors_returns_negative_one(self) -> None:
        # Arrange
        vec_a = [1.0, 0.0]
        vec_b = [-1.0, 0.0]

        # Act
        result = metric.cosine_similarity(vec_a, vec_b)

        # Assert
        assert abs(result - (-1.0)) < 1e-9

    def test_similar_vectors_returns_high_similarity(self) -> None:
        # Arrange
        vec_a = [1.0, 2.0, 3.0]
        vec_b = [2.0, 4.0, 6.0]

        # Act
        result = metric.cosine_similarity(vec_a, vec_b)

        # Assert
        assert abs(result - 1.0) < 1e-9

    def test_both_zero_vectors_returns_zero(self) -> None:
        # Arrange
        vec_a = [0.0, 0.0]
        vec_b = [0.0, 0.0]

        # Act
        result = metric.cosine_similarity(vec_a, vec_b)

        # Assert
        assert result == 0.0

    def test_empty_vectors_returns_zero(self) -> None:
        # Arrange
        vec_a: list[float] = []
        vec_b: list[float] = []

        # Act
        result = metric.cosine_similarity(vec_a, vec_b)

        # Assert
        assert result == 0.0
