"""Tests for pearson_correlation and bucket_generation_quality metrics."""

from src.evaluation.domain import metric


class TestPearsonCorrelation:
    def test_perfect_positive_correlation(self) -> None:
        # Arrange
        xs = [1.0, 2.0, 3.0, 4.0, 5.0]
        ys = [2.0, 4.0, 6.0, 8.0, 10.0]

        # Act
        result = metric.pearson_correlation(xs, ys)

        # Assert
        assert result is not None
        assert abs(result - 1.0) < 1e-9

    def test_perfect_negative_correlation(self) -> None:
        # Arrange
        xs = [1.0, 2.0, 3.0, 4.0, 5.0]
        ys = [10.0, 8.0, 6.0, 4.0, 2.0]

        # Act
        result = metric.pearson_correlation(xs, ys)

        # Assert
        assert result is not None
        assert abs(result - (-1.0)) < 1e-9

    def test_no_correlation(self) -> None:
        # Arrange - symmetric pattern yields r = 0.0
        xs = [1.0, 2.0, 3.0, 4.0]
        ys = [2.0, 4.0, 4.0, 2.0]

        # Act
        result = metric.pearson_correlation(xs, ys)

        # Assert
        assert result is not None
        assert abs(result) < 0.1

    def test_fewer_than_three_returns_none(self) -> None:
        # Arrange & Act & Assert
        assert metric.pearson_correlation([1.0, 2.0], [3.0, 4.0]) is None
        assert metric.pearson_correlation([], []) is None

    def test_zero_variance_returns_none(self) -> None:
        # Arrange & Act & Assert
        assert metric.pearson_correlation([5.0, 5.0, 5.0], [1.0, 2.0, 3.0]) is None
        assert metric.pearson_correlation([1.0, 2.0, 3.0], [5.0, 5.0, 5.0]) is None


class TestBucketGenerationQuality:
    def test_all_three_buckets(self) -> None:
        # Arrange
        results = [
            (1.0, 0.9, 0.8),   # perfect
            (1.0, 0.7, 0.6),   # perfect
            (0.5, 0.5, 0.4),   # partial
            (0.0, 0.1, 0.2),   # missed
        ]

        # Act
        buckets = metric.bucket_generation_quality(results)

        # Assert
        assert "perfect" in buckets
        assert "partial" in buckets
        assert "missed" in buckets
        # perfect: mean_faith=(0.9+0.7)/2=0.8, mean_rel=(0.8+0.6)/2=0.7
        assert abs(buckets["perfect"][0] - 0.8) < 1e-9
        assert abs(buckets["perfect"][1] - 0.7) < 1e-9
        # partial: (0.5, 0.4)
        assert abs(buckets["partial"][0] - 0.5) < 1e-9
        assert abs(buckets["partial"][1] - 0.4) < 1e-9
        # missed: (0.1, 0.2)
        assert abs(buckets["missed"][0] - 0.1) < 1e-9
        assert abs(buckets["missed"][1] - 0.2) < 1e-9

    def test_empty_results_returns_empty_dict(self) -> None:
        # Arrange & Act & Assert
        assert metric.bucket_generation_quality([]) == {}

    def test_only_perfect_bucket(self) -> None:
        # Arrange
        results = [(1.0, 0.9, 0.8)]

        # Act
        buckets = metric.bucket_generation_quality(results)

        # Assert
        assert "perfect" in buckets
        assert "partial" not in buckets
        assert "missed" not in buckets

    def test_empty_buckets_not_included(self) -> None:
        # Arrange
        results = [(0.3, 0.5, 0.4), (0.7, 0.6, 0.5)]

        # Act
        buckets = metric.bucket_generation_quality(results)

        # Assert
        assert "partial" in buckets
        assert "perfect" not in buckets
        assert "missed" not in buckets
