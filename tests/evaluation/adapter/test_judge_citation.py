"""Tests for LLMJudge citation support scoring."""

import json
from unittest import mock

import pytest

from src.evaluation.adapter import judge


def _make_judge() -> judge.LLMJudge:
    """Create a judge with a test model to avoid OpenAI key requirement."""
    return judge.LLMJudge(eval_model="test")


class TestScoreCitationSupport:
    """Tests for LLMJudge.score_citation_support."""

    @pytest.mark.asyncio
    async def test_returns_parsed_score(self) -> None:
        # Arrange
        j = _make_judge()
        llm_output = json.dumps({"score": 0.85, "reasoning": "Source supports claim."})
        mock_result = mock.MagicMock()
        mock_result.output = llm_output

        with mock.patch.object(j._citation_agent, "run", return_value=mock_result):
            # Act
            score = await j.score_citation_support(
                claim_with_citation="AI is a branch of computer science.",
                cited_chunk_content="AI, or artificial intelligence, is a branch of computer science.",
            )

        # Assert
        assert score == 0.85

    @pytest.mark.asyncio
    async def test_llm_error_returns_zero(self) -> None:
        # Arrange
        j = _make_judge()

        with mock.patch.object(
            j._citation_agent,
            "run",
            side_effect=RuntimeError("LLM unavailable"),
        ):
            # Act
            score = await j.score_citation_support(
                claim_with_citation="AI is intelligent.",
                cited_chunk_content="Some unrelated text.",
            )

        # Assert
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_score_clamped_to_max_one(self) -> None:
        # Arrange
        j = _make_judge()
        llm_output = json.dumps({"score": 1.5, "reasoning": "Over max."})
        mock_result = mock.MagicMock()
        mock_result.output = llm_output

        with mock.patch.object(j._citation_agent, "run", return_value=mock_result):
            # Act
            score = await j.score_citation_support(
                claim_with_citation="Test claim",
                cited_chunk_content="Test content",
            )

        # Assert
        assert score == 1.0

    @pytest.mark.asyncio
    async def test_score_clamped_to_min_zero(self) -> None:
        # Arrange
        j = _make_judge()
        llm_output = json.dumps({"score": -0.5, "reasoning": "Below min."})
        mock_result = mock.MagicMock()
        mock_result.output = llm_output

        with mock.patch.object(j._citation_agent, "run", return_value=mock_result):
            # Act
            score = await j.score_citation_support(
                claim_with_citation="Test claim",
                cited_chunk_content="Test content",
            )

        # Assert
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_invalid_json_returns_zero(self) -> None:
        # Arrange
        j = _make_judge()
        mock_result = mock.MagicMock()
        mock_result.output = "not valid json"

        with mock.patch.object(j._citation_agent, "run", return_value=mock_result):
            # Act
            score = await j.score_citation_support(
                claim_with_citation="Test claim",
                cited_chunk_content="Test content",
            )

        # Assert
        assert score == 0.0
