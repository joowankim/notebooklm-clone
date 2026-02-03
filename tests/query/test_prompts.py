"""Tests for RAG prompts."""

import pytest

from src.query.adapter.pydantic_ai.prompts import (
    SYSTEM_PROMPT,
    format_conversation_context,
    format_sources,
    format_user_prompt,
    format_user_prompt_with_history,
)


class TestFormatSources:
    """Tests for format_sources function."""

    def test_format_single_source(self):
        """Test formatting a single source."""
        sources = [
            {
                "index": 1,
                "title": "Test Document",
                "url": "https://example.com",
                "content": "This is the content.",
            }
        ]
        result = format_sources(sources)
        assert "[1] Test Document" in result
        assert "URL: https://example.com" in result
        assert "This is the content." in result

    def test_format_multiple_sources(self):
        """Test formatting multiple sources."""
        sources = [
            {
                "index": 1,
                "title": "Document 1",
                "url": "https://example1.com",
                "content": "Content 1",
            },
            {
                "index": 2,
                "title": "Document 2",
                "url": "https://example2.com",
                "content": "Content 2",
            },
        ]
        result = format_sources(sources)
        assert "[1] Document 1" in result
        assert "[2] Document 2" in result
        assert "---" in result  # Separator

    def test_format_source_without_title(self):
        """Test formatting source without title uses 'Untitled'."""
        sources = [
            {
                "index": 1,
                "title": None,
                "url": "https://example.com",
                "content": "Content",
            }
        ]
        result = format_sources(sources)
        assert "[1] Untitled" in result


class TestFormatUserPrompt:
    """Tests for format_user_prompt function."""

    def test_format_user_prompt(self):
        """Test formatting user prompt."""
        question = "What is AI?"
        sources_text = "[1] Document\nContent here"
        result = format_user_prompt(question, sources_text)

        assert "What is AI?" in result
        assert "SOURCES:" in result
        assert "[1] Document" in result
        assert "Remember: Use citations" in result


class TestFormatConversationContext:
    """Tests for format_conversation_context function."""

    def test_format_empty_history(self):
        """Test formatting empty conversation history."""
        result = format_conversation_context([])
        assert result == ""

    def test_format_conversation_history(self):
        """Test formatting conversation history."""
        history = [
            {"role": "user", "content": "What is machine learning?"},
            {"role": "assistant", "content": "Machine learning is..."},
        ]
        result = format_conversation_context(history)

        assert "PREVIOUS CONVERSATION:" in result
        assert "USER: What is machine learning?" in result
        assert "ASSISTANT: Machine learning is..." in result

    def test_truncates_long_messages(self):
        """Test that long messages are truncated."""
        long_content = "x" * 600
        history = [{"role": "user", "content": long_content}]
        result = format_conversation_context(history)

        assert "..." in result
        assert len(result) < 600


class TestFormatUserPromptWithHistory:
    """Tests for format_user_prompt_with_history function."""

    def test_format_with_history(self):
        """Test formatting prompt with conversation history."""
        question = "Follow up question?"
        sources_text = "[1] Source"
        history = [
            {"role": "user", "content": "Initial question"},
            {"role": "assistant", "content": "Initial answer"},
        ]
        result = format_user_prompt_with_history(question, sources_text, history)

        assert "PREVIOUS CONVERSATION:" in result
        assert "Initial question" in result
        assert "Follow up question?" in result
        assert "SOURCES:" in result

    def test_format_without_history(self):
        """Test formatting prompt without history (empty list)."""
        question = "Question?"
        sources_text = "[1] Source"
        result = format_user_prompt_with_history(question, sources_text, [])

        assert "PREVIOUS CONVERSATION:" not in result
        assert "Question?" in result


class TestSystemPrompt:
    """Tests for system prompt content."""

    def test_system_prompt_contains_critical_rules(self):
        """Test that system prompt contains critical RAG rules."""
        assert "ONLY using information from the provided sources" in SYSTEM_PROMPT
        assert "EVERY factual claim MUST have a citation" in SYSTEM_PROMPT
        assert "[1], [2]" in SYSTEM_PROMPT

    def test_system_prompt_contains_citation_format(self):
        """Test that system prompt explains citation format."""
        assert "Citation format:" in SYSTEM_PROMPT
        assert "Use [1], [2]" in SYSTEM_PROMPT
