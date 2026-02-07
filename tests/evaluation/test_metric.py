"""Tests for retrieval evaluation metric functions."""

from src.evaluation.domain.metric import (
    aggregate_metrics,
    hit_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


class TestPrecisionAtK:
    """Tests for precision_at_k function."""

    def test_all_relevant(self):
        """All top-k items are relevant."""
        result = precision_at_k(["a", "b", "c"], {"a", "b", "c"}, k=3)
        assert result == 1.0

    def test_none_relevant(self):
        """No top-k items are relevant."""
        result = precision_at_k(["x", "y", "z"], {"a", "b"}, k=3)
        assert result == 0.0

    def test_partial_relevant(self):
        """Some top-k items are relevant."""
        result = precision_at_k(["a", "x", "b"], {"a", "b"}, k=3)
        assert abs(result - 2.0 / 3) < 1e-9

    def test_k_smaller_than_retrieved(self):
        """k is smaller than total retrieved items."""
        result = precision_at_k(["a", "x", "y", "b"], {"a", "b"}, k=2)
        assert result == 0.5

    def test_k_larger_than_retrieved(self):
        """k is larger than total retrieved items."""
        result = precision_at_k(["a", "b"], {"a", "b"}, k=5)
        assert result == 1.0

    def test_empty_retrieved(self):
        result = precision_at_k([], {"a", "b"}, k=3)
        assert result == 0.0

    def test_empty_relevant(self):
        result = precision_at_k(["a", "b"], set(), k=3)
        assert result == 0.0

    def test_k_zero(self):
        result = precision_at_k(["a", "b"], {"a"}, k=0)
        assert result == 0.0


class TestRecallAtK:
    """Tests for recall_at_k function."""

    def test_all_relevant_found(self):
        """All relevant items are in top-k."""
        result = recall_at_k(["a", "b", "c"], {"a", "b"}, k=3)
        assert result == 1.0

    def test_none_relevant_found(self):
        """No relevant items in top-k."""
        result = recall_at_k(["x", "y", "z"], {"a", "b"}, k=3)
        assert result == 0.0

    def test_partial_relevant_found(self):
        """Some relevant items are in top-k."""
        result = recall_at_k(["a", "x", "y"], {"a", "b"}, k=3)
        assert result == 0.5

    def test_single_relevant_found(self):
        result = recall_at_k(["a"], {"a"}, k=1)
        assert result == 1.0

    def test_empty_relevant(self):
        result = recall_at_k(["a", "b"], set(), k=3)
        assert result == 0.0

    def test_k_zero(self):
        result = recall_at_k(["a"], {"a"}, k=0)
        assert result == 0.0


class TestHitAtK:
    """Tests for hit_at_k function."""

    def test_hit(self):
        """At least one relevant item in top-k."""
        result = hit_at_k(["x", "a", "y"], {"a"}, k=3)
        assert result is True

    def test_miss(self):
        """No relevant items in top-k."""
        result = hit_at_k(["x", "y", "z"], {"a"}, k=3)
        assert result is False

    def test_hit_at_first(self):
        result = hit_at_k(["a", "x", "y"], {"a"}, k=1)
        assert result is True

    def test_miss_due_to_k(self):
        """Relevant item exists but beyond k."""
        result = hit_at_k(["x", "y", "a"], {"a"}, k=2)
        assert result is False

    def test_empty_relevant(self):
        result = hit_at_k(["a", "b"], set(), k=3)
        assert result is False

    def test_empty_retrieved(self):
        result = hit_at_k([], {"a"}, k=3)
        assert result is False

    def test_k_zero(self):
        result = hit_at_k(["a"], {"a"}, k=0)
        assert result is False


class TestReciprocalRank:
    """Tests for reciprocal_rank function."""

    def test_first_position(self):
        """First relevant item at position 1."""
        result = reciprocal_rank(["a", "x", "y"], {"a"}, k=3)
        assert result == 1.0

    def test_second_position(self):
        """First relevant item at position 2."""
        result = reciprocal_rank(["x", "a", "y"], {"a"}, k=3)
        assert result == 0.5

    def test_third_position(self):
        """First relevant item at position 3."""
        result = reciprocal_rank(["x", "y", "a"], {"a"}, k=3)
        assert abs(result - 1.0 / 3) < 1e-9

    def test_no_relevant(self):
        """No relevant items in top-k."""
        result = reciprocal_rank(["x", "y", "z"], {"a"}, k=3)
        assert result == 0.0

    def test_relevant_beyond_k(self):
        """Relevant item exists but beyond k."""
        result = reciprocal_rank(["x", "y", "a"], {"a"}, k=2)
        assert result == 0.0

    def test_multiple_relevant(self):
        """Multiple relevant items - returns rank of first."""
        result = reciprocal_rank(["x", "a", "b"], {"a", "b"}, k=3)
        assert result == 0.5

    def test_empty_relevant(self):
        result = reciprocal_rank(["a", "b"], set(), k=3)
        assert result == 0.0

    def test_k_zero(self):
        result = reciprocal_rank(["a"], {"a"}, k=0)
        assert result == 0.0


class TestAggregateMetrics:
    """Tests for aggregate_metrics function."""

    def test_aggregate(self):
        precisions = [0.2, 0.4, 0.6]
        recalls = [0.5, 0.5, 1.0]
        hits = [True, False, True]
        rrs = [1.0, 0.0, 0.5]

        mean_p, mean_r, hit_rate, mrr = aggregate_metrics(
            precisions, recalls, hits, rrs
        )

        assert abs(mean_p - 0.4) < 1e-9
        assert abs(mean_r - 2.0 / 3) < 1e-9
        assert abs(hit_rate - 2.0 / 3) < 1e-9
        assert abs(mrr - 0.5) < 1e-9

    def test_all_perfect(self):
        precisions = [1.0, 1.0]
        recalls = [1.0, 1.0]
        hits = [True, True]
        rrs = [1.0, 1.0]

        mean_p, mean_r, hit_rate, mrr = aggregate_metrics(
            precisions, recalls, hits, rrs
        )

        assert mean_p == 1.0
        assert mean_r == 1.0
        assert hit_rate == 1.0
        assert mrr == 1.0

    def test_all_zero(self):
        precisions = [0.0, 0.0]
        recalls = [0.0, 0.0]
        hits = [False, False]
        rrs = [0.0, 0.0]

        mean_p, mean_r, hit_rate, mrr = aggregate_metrics(
            precisions, recalls, hits, rrs
        )

        assert mean_p == 0.0
        assert mean_r == 0.0
        assert hit_rate == 0.0
        assert mrr == 0.0

    def test_empty_input(self):
        mean_p, mean_r, hit_rate, mrr = aggregate_metrics([], [], [], [])

        assert mean_p == 0.0
        assert mean_r == 0.0
        assert hit_rate == 0.0
        assert mrr == 0.0

    def test_single_case(self):
        mean_p, mean_r, hit_rate, mrr = aggregate_metrics(
            [0.4], [0.8], [True], [0.5]
        )

        assert mean_p == 0.4
        assert mean_r == 0.8
        assert hit_rate == 1.0
        assert mrr == 0.5
