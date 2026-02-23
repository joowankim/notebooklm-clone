"""Tests for citation metrics."""

from src.evaluation.domain import metric


class TestCitationPrecision:
    def test_all_cited_are_relevant(self) -> None:
        # Arrange
        cited = ["a", "b"]
        relevant = {"a", "b", "c"}

        # Act
        result = metric.citation_precision(cited, relevant)

        # Assert
        assert result == 1.0

    def test_no_cited_are_relevant(self) -> None:
        # Arrange
        cited = ["x", "y"]
        relevant = {"a", "b"}

        # Act
        result = metric.citation_precision(cited, relevant)

        # Assert
        assert result == 0.0

    def test_half_cited_are_relevant(self) -> None:
        # Arrange
        cited = ["a", "x"]
        relevant = {"a", "b"}

        # Act
        result = metric.citation_precision(cited, relevant)

        # Assert
        assert result == 0.5

    def test_empty_cited_returns_zero(self) -> None:
        # Arrange
        cited: list[str] = []
        relevant = {"a", "b"}

        # Act
        result = metric.citation_precision(cited, relevant)

        # Assert
        assert result == 0.0


class TestCitationRecall:
    def test_all_relevant_are_cited(self) -> None:
        # Arrange
        cited = ["a", "b", "c"]
        relevant = {"a", "b"}

        # Act
        result = metric.citation_recall(cited, relevant)

        # Assert
        assert result == 1.0

    def test_no_relevant_are_cited(self) -> None:
        # Arrange
        cited = ["x", "y"]
        relevant = {"a", "b"}

        # Act
        result = metric.citation_recall(cited, relevant)

        # Assert
        assert result == 0.0

    def test_half_relevant_are_cited(self) -> None:
        # Arrange
        cited = ["a", "x"]
        relevant = {"a", "b"}

        # Act
        result = metric.citation_recall(cited, relevant)

        # Assert
        assert result == 0.5

    def test_empty_relevant_returns_zero(self) -> None:
        # Arrange
        cited = ["a", "b"]
        relevant: set[str] = set()

        # Act
        result = metric.citation_recall(cited, relevant)

        # Assert
        assert result == 0.0

    def test_empty_cited_returns_zero(self) -> None:
        # Arrange
        cited: list[str] = []
        relevant = {"a", "b"}

        # Act
        result = metric.citation_recall(cited, relevant)

        # Assert
        assert result == 0.0


class TestPhantomCitationCount:
    def test_no_phantom_citations(self) -> None:
        # Arrange
        indices = [0, 1, 2]
        chunk_count = 5

        # Act
        result = metric.phantom_citation_count(indices, chunk_count)

        # Assert
        assert result == 0

    def test_all_phantom_citations(self) -> None:
        # Arrange
        indices = [5, 6, 7]
        chunk_count = 5

        # Act
        result = metric.phantom_citation_count(indices, chunk_count)

        # Assert
        assert result == 3

    def test_mixed_phantom_citations(self) -> None:
        # Arrange
        indices = [0, 3, 5, 10]
        chunk_count = 5

        # Act
        result = metric.phantom_citation_count(indices, chunk_count)

        # Assert
        assert result == 2

    def test_empty_indices_returns_zero(self) -> None:
        # Arrange
        indices: list[int] = []
        chunk_count = 5

        # Act
        result = metric.phantom_citation_count(indices, chunk_count)

        # Assert
        assert result == 0

    def test_zero_chunk_count_all_phantom(self) -> None:
        # Arrange
        indices = [0, 1, 2]
        chunk_count = 0

        # Act
        result = metric.phantom_citation_count(indices, chunk_count)

        # Assert
        assert result == 3
