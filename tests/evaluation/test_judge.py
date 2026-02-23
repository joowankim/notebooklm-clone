"""Tests for LLMJudge adapter."""

import json
from unittest import mock

import pytest

from src.evaluation.adapter import judge


def _make_judge() -> judge.LLMJudge:
    """Create a judge with a test model to avoid OpenAI key requirement."""
    return judge.LLMJudge(eval_model="test")


class TestParseScore:
    """Tests for LLMJudge._parse_score."""

    def test_valid_json_returns_score(self) -> None:
        # Arrange
        j = _make_judge()
        output = json.dumps({"score": 0.85, "reasoning": "Well grounded."})

        # Act
        result = j._parse_score(output)

        # Assert
        assert result == 0.85

    def test_markdown_wrapped_json_returns_score(self) -> None:
        # Arrange
        j = _make_judge()
        output = "```json\n" + json.dumps({"score": 0.7, "reasoning": "ok"}) + "\n```"

        # Act
        result = j._parse_score(output)

        # Assert
        assert result == 0.7

    def test_invalid_json_returns_zero(self) -> None:
        # Arrange
        j = _make_judge()

        # Act
        result = j._parse_score("not valid json")

        # Assert
        assert result == 0.0

    def test_missing_score_key_returns_zero(self) -> None:
        # Arrange
        j = _make_judge()
        output = json.dumps({"reasoning": "no score here"})

        # Act
        result = j._parse_score(output)

        # Assert
        assert result == 0.0

    def test_score_above_one_clamped(self) -> None:
        # Arrange
        j = _make_judge()
        output = json.dumps({"score": 1.5, "reasoning": "too high"})

        # Act
        result = j._parse_score(output)

        # Assert
        assert result == 1.0

    def test_score_below_zero_clamped(self) -> None:
        # Arrange
        j = _make_judge()
        output = json.dumps({"score": -0.3, "reasoning": "too low"})

        # Act
        result = j._parse_score(output)

        # Assert
        assert result == 0.0

    def test_integer_score_converted_to_float(self) -> None:
        # Arrange
        j = _make_judge()
        output = json.dumps({"score": 1, "reasoning": "perfect"})

        # Act
        result = j._parse_score(output)

        # Assert
        assert result == 1.0
        assert isinstance(result, float)

    def test_score_string_value_returns_zero(self) -> None:
        # Arrange
        j = _make_judge()
        output = json.dumps({"score": "high", "reasoning": "not a number"})

        # Act
        result = j._parse_score(output)

        # Assert
        assert result == 0.0


class TestScoreFaithfulness:
    """Tests for LLMJudge.score_faithfulness with mocked agent."""

    @pytest.mark.asyncio
    async def test_returns_parsed_score(self) -> None:
        # Arrange
        j = _make_judge()
        llm_output = json.dumps({"score": 0.9, "reasoning": "Grounded in context."})
        mock_result = mock.MagicMock()
        mock_result.output = llm_output

        from src.chunk.domain import model as chunk_model

        chunk = chunk_model.Chunk.create(
            document_id="doc1",
            content="AI is artificial intelligence.",
            char_start=0,
            char_end=30,
            chunk_index=0,
            token_count=5,
        )

        with mock.patch.object(j._faithfulness_agent, "run", return_value=mock_result):
            # Act
            score = await j.score_faithfulness(
                question="What is AI?",
                answer="AI is artificial intelligence.",
                context_chunks=[chunk],
            )

        # Assert
        assert score == 0.9

    @pytest.mark.asyncio
    async def test_llm_error_returns_zero(self) -> None:
        # Arrange
        j = _make_judge()

        with mock.patch.object(
            j._faithfulness_agent,
            "run",
            side_effect=RuntimeError("LLM unavailable"),
        ):
            # Act
            score = await j.score_faithfulness(
                question="What is AI?",
                answer="AI is artificial intelligence.",
                context_chunks=[],
            )

        # Assert
        assert score == 0.0


class TestScoreAnswerRelevancy:
    """Tests for LLMJudge.score_answer_relevancy with mocked agent."""

    @pytest.mark.asyncio
    async def test_returns_parsed_score(self) -> None:
        # Arrange
        j = _make_judge()
        llm_output = json.dumps({"score": 0.8, "reasoning": "Relevant."})
        mock_result = mock.MagicMock()
        mock_result.output = llm_output

        with mock.patch.object(j._relevancy_agent, "run", return_value=mock_result):
            # Act
            score = await j.score_answer_relevancy(
                question="What is AI?",
                answer="AI is a branch of computer science.",
            )

        # Assert
        assert score == 0.8

    @pytest.mark.asyncio
    async def test_llm_error_returns_zero(self) -> None:
        # Arrange
        j = _make_judge()

        with mock.patch.object(
            j._relevancy_agent,
            "run",
            side_effect=RuntimeError("LLM unavailable"),
        ):
            # Act
            score = await j.score_answer_relevancy(
                question="What is AI?",
                answer="Something irrelevant.",
            )

        # Assert
        assert score == 0.0
