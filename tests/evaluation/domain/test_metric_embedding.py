"""Tests for embedding quality metric functions."""

import math

from src.evaluation.domain import metric


class TestIntraDocumentSimilarity:
    def test_single_doc_multiple_similar_embeddings(self) -> None:
        # Arrange
        embeddings_by_doc = {
            "doc1": [[1.0, 0.0, 0.0], [0.9, 0.1, 0.0]],
        }

        # Act
        result = metric.intra_document_similarity(embeddings_by_doc)

        # Assert
        expected = metric.cosine_similarity([1.0, 0.0, 0.0], [0.9, 0.1, 0.0])
        assert math.isclose(result, expected, rel_tol=1e-9)

    def test_single_doc_single_embedding_returns_zero(self) -> None:
        # Arrange
        embeddings_by_doc = {
            "doc1": [[1.0, 0.0, 0.0]],
        }

        # Act
        result = metric.intra_document_similarity(embeddings_by_doc)

        # Assert
        assert result == 0.0

    def test_empty_dict_returns_zero(self) -> None:
        # Arrange
        embeddings_by_doc: dict[str, list[list[float]]] = {}

        # Act
        result = metric.intra_document_similarity(embeddings_by_doc)

        # Assert
        assert result == 0.0

    def test_multiple_docs(self) -> None:
        # Arrange
        embeddings_by_doc = {
            "doc1": [[1.0, 0.0, 0.0], [0.9, 0.1, 0.0]],
            "doc2": [[0.0, 1.0, 0.0], [0.0, 0.9, 0.1]],
        }

        # Act
        result = metric.intra_document_similarity(embeddings_by_doc)

        # Assert
        sim_doc1 = metric.cosine_similarity([1.0, 0.0, 0.0], [0.9, 0.1, 0.0])
        sim_doc2 = metric.cosine_similarity([0.0, 1.0, 0.0], [0.0, 0.9, 0.1])
        expected = (sim_doc1 + sim_doc2) / 2
        assert math.isclose(result, expected, rel_tol=1e-9)


class TestInterDocumentSimilarity:
    def test_two_docs_orthogonal(self) -> None:
        # Arrange
        embeddings_by_doc = {
            "doc1": [[1.0, 0.0, 0.0]],
            "doc2": [[0.0, 1.0, 0.0]],
        }

        # Act
        result = metric.inter_document_similarity(embeddings_by_doc)

        # Assert
        assert math.isclose(result, 0.0, abs_tol=1e-9)

    def test_two_docs_similar(self) -> None:
        # Arrange
        embeddings_by_doc = {
            "doc1": [[1.0, 0.0, 0.0]],
            "doc2": [[0.9, 0.1, 0.0]],
        }

        # Act
        result = metric.inter_document_similarity(embeddings_by_doc)

        # Assert
        expected = metric.cosine_similarity([1.0, 0.0, 0.0], [0.9, 0.1, 0.0])
        assert math.isclose(result, expected, rel_tol=1e-9)

    def test_single_doc_returns_zero(self) -> None:
        # Arrange
        embeddings_by_doc = {
            "doc1": [[1.0, 0.0, 0.0], [0.5, 0.5, 0.0]],
        }

        # Act
        result = metric.inter_document_similarity(embeddings_by_doc)

        # Assert
        assert result == 0.0

    def test_empty_dict_returns_zero(self) -> None:
        # Arrange
        embeddings_by_doc: dict[str, list[list[float]]] = {}

        # Act
        result = metric.inter_document_similarity(embeddings_by_doc)

        # Assert
        assert result == 0.0


class TestSeparationRatio:
    def test_good_separation(self) -> None:
        # Arrange
        intra = 0.9
        inter = 0.3

        # Act
        result = metric.separation_ratio(intra, inter)

        # Assert
        assert math.isclose(result, 3.0, rel_tol=1e-9)

    def test_zero_inter_returns_zero(self) -> None:
        # Arrange
        intra = 0.9
        inter = 0.0

        # Act
        result = metric.separation_ratio(intra, inter)

        # Assert
        assert result == 0.0

    def test_equal_returns_one(self) -> None:
        # Arrange
        intra = 0.5
        inter = 0.5

        # Act
        result = metric.separation_ratio(intra, inter)

        # Assert
        assert math.isclose(result, 1.0, rel_tol=1e-9)


class TestAdjacentChunkSimilarity:
    def test_similar_adjacent_pairs(self) -> None:
        # Arrange
        ordered_embeddings = [
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],
            [0.8, 0.2, 0.0],
        ]

        # Act
        result = metric.adjacent_chunk_similarity(ordered_embeddings)

        # Assert
        sim_01 = metric.cosine_similarity([1.0, 0.0, 0.0], [0.9, 0.1, 0.0])
        sim_12 = metric.cosine_similarity([0.9, 0.1, 0.0], [0.8, 0.2, 0.0])
        expected = (sim_01 + sim_12) / 2
        assert math.isclose(result, expected, rel_tol=1e-9)

    def test_single_embedding_returns_zero(self) -> None:
        # Arrange
        ordered_embeddings = [[1.0, 0.0, 0.0]]

        # Act
        result = metric.adjacent_chunk_similarity(ordered_embeddings)

        # Assert
        assert result == 0.0

    def test_empty_list_returns_zero(self) -> None:
        # Arrange
        ordered_embeddings: list[list[float]] = []

        # Act
        result = metric.adjacent_chunk_similarity(ordered_embeddings)

        # Assert
        assert result == 0.0
