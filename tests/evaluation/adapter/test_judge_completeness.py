"""Tests for LLMJudge answer completeness scoring."""

import json
from unittest import mock

import pytest

from src.chunk.domain import model as chunk_model
from src.evaluation.adapter import judge


def _make_judge() -> judge.LLMJudge:
    """Create a judge with a test model to avoid OpenAI key requirement."""
    return judge.LLMJudge(eval_model="test")


def _make_chunk(content: str) -> chunk_model.Chunk:
    """Create a test chunk."""
    return chunk_model.Chunk.create(
        document_id="doc1",
        content=content,
        char_start=0,
        char_end=len(content),
        chunk_index=0,
        token_count=5,
    )


class TestScoreAnswerCompleteness:
    """Tests for LLMJudge.score_answer_completeness."""

    @pytest.mark.asyncio
    async def test_returns_parsed_score(self) -> None:
        # Arrange
        j = _make_judge()
        llm_output = json.dumps({"score": 0.92, "reasoning": "Comprehensive answer."})
        mock_result = mock.MagicMock()
        mock_result.output = llm_output

        chunk = _make_chunk("AI is artificial intelligence, a branch of computer science.")

        with mock.patch.object(j._completeness_agent, "run", return_value=mock_result):
            # Act
            score = await j.score_answer_completeness(
                question="What is AI?",
                answer="AI is artificial intelligence, a branch of computer science.",
                context_chunks=[chunk],
            )

        # Assert
        assert score == 0.92

    @pytest.mark.asyncio
    async def test_llm_error_returns_zero(self) -> None:
        # Arrange
        j = _make_judge()

        with mock.patch.object(
            j._completeness_agent,
            "run",
            side_effect=RuntimeError("LLM unavailable"),
        ):
            # Act
            score = await j.score_answer_completeness(
                question="What is AI?",
                answer="AI is intelligent.",
                context_chunks=[],
            )

        # Assert
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_score_clamped_to_max_one(self) -> None:
        # Arrange
        j = _make_judge()
        llm_output = json.dumps({"score": 1.3, "reasoning": "Over max."})
        mock_result = mock.MagicMock()
        mock_result.output = llm_output

        with mock.patch.object(j._completeness_agent, "run", return_value=mock_result):
            # Act
            score = await j.score_answer_completeness(
                question="Test?",
                answer="Test answer.",
                context_chunks=[],
            )

        # Assert
        assert score == 1.0

    @pytest.mark.asyncio
    async def test_score_clamped_to_min_zero(self) -> None:
        # Arrange
        j = _make_judge()
        llm_output = json.dumps({"score": -0.2, "reasoning": "Below min."})
        mock_result = mock.MagicMock()
        mock_result.output = llm_output

        with mock.patch.object(j._completeness_agent, "run", return_value=mock_result):
            # Act
            score = await j.score_answer_completeness(
                question="Test?",
                answer="Test answer.",
                context_chunks=[],
            )

        # Assert
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_multiple_context_chunks_formatted(self) -> None:
        # Arrange
        j = _make_judge()
        llm_output = json.dumps({"score": 0.75, "reasoning": "Partial coverage."})
        mock_result = mock.MagicMock()
        mock_result.output = llm_output

        chunks = [
            _make_chunk("AI is artificial intelligence."),
            _make_chunk("Machine learning is a subset of AI."),
        ]

        with mock.patch.object(j._completeness_agent, "run", return_value=mock_result) as mock_run:
            # Act
            score = await j.score_answer_completeness(
                question="What is AI?",
                answer="AI is artificial intelligence.",
                context_chunks=chunks,
            )

        # Assert
        assert score == 0.75
        call_args = mock_run.call_args[0][0]
        assert "[1]" in call_args
        assert "[2]" in call_args
