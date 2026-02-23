"""Tests for answer_consistency and aggregate metrics."""

from src.evaluation.domain import metric


class TestAnswerConsistency:
    def test_identical_embeddings_returns_one(self) -> None:
        # Arrange
        embeddings = [
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ]

        # Act
        result = metric.answer_consistency(embeddings)

        # Assert
        assert abs(result - 1.0) < 1e-9

    def test_orthogonal_embeddings_returns_zero(self) -> None:
        # Arrange
        embeddings = [
            [1.0, 0.0],
            [0.0, 1.0],
        ]

        # Act
        result = metric.answer_consistency(embeddings)

        # Assert
        assert abs(result - 0.0) < 1e-9

    def test_single_embedding_returns_zero(self) -> None:
        # Arrange
        embeddings = [[1.0, 2.0, 3.0]]

        # Act
        result = metric.answer_consistency(embeddings)

        # Assert
        assert result == 0.0

    def test_empty_list_returns_zero(self) -> None:
        # Arrange
        embeddings: list[list[float]] = []

        # Act
        result = metric.answer_consistency(embeddings)

        # Assert
        assert result == 0.0

    def test_two_similar_embeddings(self) -> None:
        # Arrange
        embeddings = [
            [1.0, 2.0, 3.0],
            [2.0, 4.0, 6.0],
        ]

        # Act
        result = metric.answer_consistency(embeddings)

        # Assert
        assert abs(result - 1.0) < 1e-9

    def test_three_similar_embeddings(self) -> None:
        # Arrange - all same vectors => all pairs have similarity 1.0
        embeddings = [[1.0, 0.0], [1.0, 0.0], [1.0, 0.0]]

        # Act
        result = metric.answer_consistency(embeddings)

        # Assert
        assert abs(result - 1.0) < 1e-9

    def test_mixed_similarities(self) -> None:
        # Arrange - 3 vectors with varying pairwise similarity
        embeddings = [[1.0, 0.0], [0.7071, 0.7071], [0.0, 1.0]]

        # Act
        result = metric.answer_consistency(embeddings)

        # Assert
        # pair(0,1) ~ 0.7071, pair(0,2) = 0.0, pair(1,2) ~ 0.7071
        # mean ~ (0.7071 + 0.0 + 0.7071) / 3 ~ 0.4714
        assert 0.45 < result < 0.50


class TestAggregateNdcgMap:
    def test_basic_aggregation(self) -> None:
        # Arrange
        ndcgs = [1.0, 0.5, 0.8]
        map_scores = [0.9, 0.6, 0.7]

        # Act
        mean_ndcg, mean_map = metric.aggregate_ndcg_map(ndcgs, map_scores)

        # Assert
        expected_ndcg = (1.0 + 0.5 + 0.8) / 3
        expected_map = (0.9 + 0.6 + 0.7) / 3
        assert abs(mean_ndcg - expected_ndcg) < 1e-9
        assert abs(mean_map - expected_map) < 1e-9

    def test_empty_lists_returns_zeros(self) -> None:
        # Arrange
        ndcgs: list[float] = []
        map_scores: list[float] = []

        # Act
        mean_ndcg, mean_map = metric.aggregate_ndcg_map(ndcgs, map_scores)

        # Assert
        assert mean_ndcg == 0.0
        assert mean_map == 0.0


class TestAggregateCitationMetrics:
    def test_basic_aggregation(self) -> None:
        # Arrange
        precisions = [1.0, 0.5, 0.8]
        recalls = [0.9, 0.6, 0.7]
        phantom_counts = [0, 2, 1]

        # Act
        mean_p, mean_r, mean_ph = metric.aggregate_citation_metrics(
            precisions, recalls, phantom_counts
        )

        # Assert
        expected_p = (1.0 + 0.5 + 0.8) / 3
        expected_r = (0.9 + 0.6 + 0.7) / 3
        expected_ph = (0 + 2 + 1) / 3
        assert abs(mean_p - expected_p) < 1e-9
        assert abs(mean_r - expected_r) < 1e-9
        assert abs(mean_ph - expected_ph) < 1e-9

    def test_empty_lists_returns_zeros(self) -> None:
        # Arrange
        precisions: list[float] = []
        recalls: list[float] = []
        phantom_counts: list[int] = []

        # Act
        mean_p, mean_r, mean_ph = metric.aggregate_citation_metrics(
            precisions, recalls, phantom_counts
        )

        # Assert
        assert mean_p == 0.0
        assert mean_r == 0.0
        assert mean_ph == 0.0
