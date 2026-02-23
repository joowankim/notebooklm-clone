"""Tests for SyntheticTestGenerator difficulty classification."""

import json
from unittest import mock

import pytest

from src.chunk.domain import model as chunk_model
from src.evaluation.adapter import generator
from src.evaluation.domain import model


def _make_chunk(content: str = "Some passage text about AI.") -> chunk_model.Chunk:
    """Create a chunk for testing."""
    return chunk_model.Chunk.create(
        document_id="doc1",
        content=content,
        char_start=0,
        char_end=len(content),
        chunk_index=0,
        token_count=10,
    )


def _make_generator() -> generator.SyntheticTestGenerator:
    """Create a generator with a test model to avoid OpenAI key requirement."""
    return generator.SyntheticTestGenerator(eval_model="test")


class TestParseQuestionsWithDifficulty:
    """Tests for _parse_questions with difficulty classification."""

    def test_valid_json_with_difficulty_returns_tuples(self) -> None:
        # Arrange
        gen = _make_generator()
        raw = json.dumps({
            "questions": [
                {"text": "What is AI?", "difficulty": "factual"},
                {"text": "How does AI compare to ML?", "difficulty": "analytical"},
            ]
        })

        # Act
        result = gen._parse_questions(raw, expected_count=2)

        # Assert
        assert result == [
            ("What is AI?", model.QuestionDifficulty.FACTUAL),
            ("How does AI compare to ML?", model.QuestionDifficulty.ANALYTICAL),
        ]

    def test_all_difficulty_levels_parsed_correctly(self) -> None:
        # Arrange
        gen = _make_generator()
        raw = json.dumps({
            "questions": [
                {"text": "q1", "difficulty": "factual"},
                {"text": "q2", "difficulty": "analytical"},
                {"text": "q3", "difficulty": "inferential"},
                {"text": "q4", "difficulty": "paraphrased"},
            ]
        })

        # Act
        result = gen._parse_questions(raw, expected_count=4)

        # Assert
        assert result == [
            ("q1", model.QuestionDifficulty.FACTUAL),
            ("q2", model.QuestionDifficulty.ANALYTICAL),
            ("q3", model.QuestionDifficulty.INFERENTIAL),
            ("q4", model.QuestionDifficulty.PARAPHRASED),
        ]

    def test_missing_difficulty_returns_none(self) -> None:
        # Arrange
        gen = _make_generator()
        raw = json.dumps({
            "questions": [
                {"text": "What is AI?"},
                {"text": "How does AI work?"},
            ]
        })

        # Act
        result = gen._parse_questions(raw, expected_count=2)

        # Assert
        assert result == [
            ("What is AI?", None),
            ("How does AI work?", None),
        ]

    def test_invalid_difficulty_value_returns_none_with_warning(self) -> None:
        # Arrange
        gen = _make_generator()
        raw = json.dumps({
            "questions": [
                {"text": "What is AI?", "difficulty": "impossible"},
            ]
        })

        # Act
        with mock.patch.object(generator.logger, "warning") as mock_warn:
            result = gen._parse_questions(raw, expected_count=1)

        # Assert
        assert result == [("What is AI?", None)]
        mock_warn.assert_called_once()

    def test_backward_compatible_with_plain_string_list(self) -> None:
        # Arrange
        gen = _make_generator()
        raw = json.dumps({
            "questions": ["What is AI?", "How does AI work?"]
        })

        # Act
        result = gen._parse_questions(raw, expected_count=2)

        # Assert
        assert result == [
            ("What is AI?", None),
            ("How does AI work?", None),
        ]

    def test_mixed_format_questions_handled(self) -> None:
        # Arrange
        gen = _make_generator()
        raw = json.dumps({
            "questions": [
                {"text": "What is AI?", "difficulty": "factual"},
                "How does AI work?",
            ]
        })

        # Act
        result = gen._parse_questions(raw, expected_count=2)

        # Assert
        assert result == [
            ("What is AI?", model.QuestionDifficulty.FACTUAL),
            ("How does AI work?", None),
        ]

    def test_uppercase_difficulty_parsed_correctly(self) -> None:
        # Arrange
        gen = _make_generator()
        raw = json.dumps({
            "questions": [
                {"text": "What is AI?", "difficulty": "FACTUAL"},
            ]
        })

        # Act
        result = gen._parse_questions(raw, expected_count=1)

        # Assert
        assert result == [("What is AI?", model.QuestionDifficulty.FACTUAL)]

    def test_markdown_code_block_with_difficulty(self) -> None:
        # Arrange
        gen = _make_generator()
        raw = '```json\n' + json.dumps({
            "questions": [
                {"text": "What is AI?", "difficulty": "analytical"},
            ]
        }) + '\n```'

        # Act
        result = gen._parse_questions(raw, expected_count=1)

        # Assert
        assert result == [
            ("What is AI?", model.QuestionDifficulty.ANALYTICAL),
        ]

    def test_empty_text_questions_filtered_out(self) -> None:
        # Arrange
        gen = _make_generator()
        raw = json.dumps({
            "questions": [
                {"text": "", "difficulty": "factual"},
                {"text": "Valid?", "difficulty": "factual"},
            ]
        })

        # Act
        result = gen._parse_questions(raw, expected_count=2)

        # Assert
        assert result == [("Valid?", model.QuestionDifficulty.FACTUAL)]

    def test_invalid_json_returns_empty_list(self) -> None:
        # Arrange
        gen = _make_generator()

        # Act
        result = gen._parse_questions("not json at all", expected_count=2)

        # Assert
        assert result == []


class TestGenerateTestCasesWithDifficulty:
    """Tests for generate_test_cases producing TestCase entities with difficulty."""

    @pytest.mark.asyncio
    async def test_generate_test_cases_with_difficulty(self) -> None:
        # Arrange
        gen = _make_generator()
        chunk = _make_chunk("AI is a broad field of computer science.")

        llm_response = json.dumps({
            "questions": [
                {"text": "What is AI?", "difficulty": "factual"},
                {"text": "How might AI evolve?", "difficulty": "inferential"},
            ]
        })

        mock_result = mock.MagicMock()
        mock_result.output = llm_response

        with mock.patch.object(gen._agent, "run", return_value=mock_result):
            # Act
            test_cases = await gen.generate_test_cases(
                chunks=[chunk],
                questions_per_chunk=2,
            )

        # Assert
        assert len(test_cases) == 2

        assert test_cases[0].question == "What is AI?"
        assert test_cases[0].difficulty == model.QuestionDifficulty.FACTUAL
        assert test_cases[0].source_chunk_id == chunk.id
        assert test_cases[0].ground_truth_chunk_ids == (chunk.id,)

        assert test_cases[1].question == "How might AI evolve?"
        assert test_cases[1].difficulty == model.QuestionDifficulty.INFERENTIAL
        assert test_cases[1].source_chunk_id == chunk.id

    @pytest.mark.asyncio
    async def test_generate_test_cases_without_difficulty(self) -> None:
        # Arrange
        gen = _make_generator()
        chunk = _make_chunk("AI is a broad field.")

        llm_response = json.dumps({
            "questions": ["What is AI?", "Define AI."]
        })

        mock_result = mock.MagicMock()
        mock_result.output = llm_response

        with mock.patch.object(gen._agent, "run", return_value=mock_result):
            # Act
            test_cases = await gen.generate_test_cases(
                chunks=[chunk],
                questions_per_chunk=2,
            )

        # Assert
        assert len(test_cases) == 2
        assert test_cases[0].question == "What is AI?"
        assert test_cases[0].difficulty is None
        assert test_cases[1].question == "Define AI."
        assert test_cases[1].difficulty is None

    @pytest.mark.asyncio
    async def test_generate_test_cases_multiple_chunks(self) -> None:
        # Arrange
        gen = _make_generator()
        chunk_a = _make_chunk("AI is about intelligence.")
        chunk_b = _make_chunk("ML is a subset of AI.")

        llm_response_a = json.dumps({
            "questions": [
                {"text": "What is AI?", "difficulty": "factual"},
            ]
        })
        llm_response_b = json.dumps({
            "questions": [
                {"text": "How does ML relate to AI?", "difficulty": "analytical"},
            ]
        })

        mock_result_a = mock.MagicMock()
        mock_result_a.output = llm_response_a
        mock_result_b = mock.MagicMock()
        mock_result_b.output = llm_response_b

        with mock.patch.object(
            gen._agent,
            "run",
            side_effect=[mock_result_a, mock_result_b],
        ):
            # Act
            test_cases = await gen.generate_test_cases(
                chunks=[chunk_a, chunk_b],
                questions_per_chunk=1,
            )

        # Assert
        assert len(test_cases) == 2
        assert test_cases[0].difficulty == model.QuestionDifficulty.FACTUAL
        assert test_cases[0].source_chunk_id == chunk_a.id
        assert test_cases[1].difficulty == model.QuestionDifficulty.ANALYTICAL
        assert test_cases[1].source_chunk_id == chunk_b.id
