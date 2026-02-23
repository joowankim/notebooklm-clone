"""Tests for LLMJudge hallucination analysis."""

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


class TestAnalyzeHallucinations:
    """Tests for LLMJudge.analyze_hallucinations."""

    @pytest.mark.asyncio
    async def test_returns_parsed_claims(self) -> None:
        # Arrange
        j = _make_judge()
        llm_output = json.dumps({
            "claims": [
                {
                    "claim_text": "AI is a branch of computer science.",
                    "verdict": "supported",
                    "supporting_chunks": [1],
                    "reasoning": "Directly stated in context.",
                },
                {
                    "claim_text": "AI was invented in 2020.",
                    "verdict": "fabricated",
                    "supporting_chunks": [],
                    "reasoning": "Not found in context.",
                },
            ]
        })
        mock_result = mock.MagicMock()
        mock_result.output = llm_output

        chunk = _make_chunk("AI is a branch of computer science.")

        with mock.patch.object(j._hallucination_agent, "run", return_value=mock_result):
            # Act
            result = await j.analyze_hallucinations(
                question="What is AI?",
                answer="AI is a branch of computer science. AI was invented in 2020.",
                context_chunks=[chunk],
            )

        # Assert
        assert "claims" in result
        assert len(result["claims"]) == 2
        assert result["claims"][0]["claim_text"] == "AI is a branch of computer science."
        assert result["claims"][0]["verdict"] == "supported"
        assert result["claims"][1]["verdict"] == "fabricated"

    @pytest.mark.asyncio
    async def test_llm_error_returns_empty_claims(self) -> None:
        # Arrange
        j = _make_judge()

        with mock.patch.object(
            j._hallucination_agent,
            "run",
            side_effect=RuntimeError("LLM unavailable"),
        ):
            # Act
            result = await j.analyze_hallucinations(
                question="What is AI?",
                answer="AI is intelligent.",
                context_chunks=[],
            )

        # Assert
        assert "claims" in result
        assert result["claims"] == []

    @pytest.mark.asyncio
    async def test_invalid_json_returns_empty_claims(self) -> None:
        # Arrange
        j = _make_judge()
        mock_result = mock.MagicMock()
        mock_result.output = "not valid json"

        with mock.patch.object(j._hallucination_agent, "run", return_value=mock_result):
            # Act
            result = await j.analyze_hallucinations(
                question="What is AI?",
                answer="AI is intelligent.",
                context_chunks=[],
            )

        # Assert
        assert "claims" in result
        assert result["claims"] == []

    @pytest.mark.asyncio
    async def test_markdown_wrapped_json_parsed(self) -> None:
        # Arrange
        j = _make_judge()
        raw = json.dumps({
            "claims": [
                {
                    "claim_text": "Test claim.",
                    "verdict": "supported",
                    "supporting_chunks": [1],
                    "reasoning": "Found in context.",
                }
            ]
        })
        llm_output = f"```json\n{raw}\n```"
        mock_result = mock.MagicMock()
        mock_result.output = llm_output

        with mock.patch.object(j._hallucination_agent, "run", return_value=mock_result):
            # Act
            result = await j.analyze_hallucinations(
                question="Test?",
                answer="Test claim.",
                context_chunks=[],
            )

        # Assert
        assert len(result["claims"]) == 1
        assert result["claims"][0]["verdict"] == "supported"
