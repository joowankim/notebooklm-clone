"""Tests for conversation domain model."""

import datetime
import uuid

import pytest

from src.conversation.domain.model import Conversation, Message, MessageRole


class TestMessageModel:
    """Tests for Message entity."""

    def test_create_user_message(self):
        """Test creating a user message."""
        now = datetime.datetime.now(datetime.timezone.utc)
        message = Message(
            id=uuid.uuid4().hex,
            role=MessageRole.USER,
            content="Hello, what is AI?",
            citations=None,
            created_at=now,
        )

        assert message.role == MessageRole.USER
        assert message.content == "Hello, what is AI?"
        assert message.citations is None

    def test_create_assistant_message_with_citations(self):
        """Test creating an assistant message with citations."""
        now = datetime.datetime.now(datetime.timezone.utc)
        citations = [
            {"citation_index": 1, "document_id": "doc1", "chunk_id": "chunk1"}
        ]
        message = Message(
            id=uuid.uuid4().hex,
            role=MessageRole.ASSISTANT,
            content="AI is artificial intelligence [1].",
            citations=citations,
            created_at=now,
        )

        assert message.role == MessageRole.ASSISTANT
        assert message.citations == citations


class TestConversationModel:
    """Tests for Conversation entity."""

    def test_create_conversation(self):
        """Test creating a conversation."""
        now = datetime.datetime.now(datetime.timezone.utc)
        conversation = Conversation(
            id=uuid.uuid4().hex,
            notebook_id="notebook123",
            title="Test Conversation",
            messages=(),
            created_at=now,
            updated_at=now,
        )

        assert conversation.notebook_id == "notebook123"
        assert conversation.title == "Test Conversation"
        assert len(conversation.messages) == 0

    def test_add_message_to_conversation(self):
        """Test adding a message to a conversation."""
        now = datetime.datetime.now(datetime.timezone.utc)
        conversation = Conversation(
            id=uuid.uuid4().hex,
            notebook_id="notebook123",
            title=None,
            messages=(),
            created_at=now,
            updated_at=now,
        )

        message = Message(
            id=uuid.uuid4().hex,
            role=MessageRole.USER,
            content="What is machine learning?",
            citations=None,
            created_at=now,
        )

        updated_conversation = conversation.add_message(message)

        # Original should be unchanged (immutability)
        assert len(conversation.messages) == 0
        # New conversation should have the message
        assert len(updated_conversation.messages) == 1
        assert updated_conversation.messages[0].content == "What is machine learning?"

    def test_auto_title_generation(self):
        """Test that title is auto-generated from first user message."""
        now = datetime.datetime.now(datetime.timezone.utc)
        conversation = Conversation(
            id=uuid.uuid4().hex,
            notebook_id="notebook123",
            title=None,
            messages=(),
            created_at=now,
            updated_at=now,
        )

        message = Message(
            id=uuid.uuid4().hex,
            role=MessageRole.USER,
            content="What is the difference between AI and machine learning?",
            citations=None,
            created_at=now,
        )

        updated = conversation.add_message(message)

        assert updated.title == "What is the difference between AI and machine lear..."

    def test_title_not_overwritten(self):
        """Test that existing title is not overwritten."""
        now = datetime.datetime.now(datetime.timezone.utc)
        conversation = Conversation(
            id=uuid.uuid4().hex,
            notebook_id="notebook123",
            title="My Research",
            messages=(),
            created_at=now,
            updated_at=now,
        )

        message = Message(
            id=uuid.uuid4().hex,
            role=MessageRole.USER,
            content="Some question here?",
            citations=None,
            created_at=now,
        )

        updated = conversation.add_message(message)

        assert updated.title == "My Research"  # Unchanged

    def test_get_context_for_rag(self):
        """Test getting conversation context for RAG."""
        now = datetime.datetime.now(datetime.timezone.utc)
        messages = (
            Message(
                id="m1",
                role=MessageRole.USER,
                content="What is AI?",
                citations=None,
                created_at=now,
            ),
            Message(
                id="m2",
                role=MessageRole.ASSISTANT,
                content="AI is artificial intelligence.",
                citations=None,
                created_at=now,
            ),
            Message(
                id="m3",
                role=MessageRole.USER,
                content="Tell me more about it.",
                citations=None,
                created_at=now,
            ),
        )

        conversation = Conversation(
            id=uuid.uuid4().hex,
            notebook_id="notebook123",
            title="AI Discussion",
            messages=messages,
            created_at=now,
            updated_at=now,
        )

        context = conversation.get_context_for_rag(max_turns=5)

        assert len(context) == 3
        assert context[0]["role"] == "user"
        assert context[0]["content"] == "What is AI?"
        assert context[1]["role"] == "assistant"
        assert context[2]["role"] == "user"

    def test_get_context_for_rag_limited_turns(self):
        """Test that context is limited to max_turns."""
        now = datetime.datetime.now(datetime.timezone.utc)
        # Create 6 messages (3 turns)
        messages = tuple(
            Message(
                id=f"m{i}",
                role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                content=f"Message {i}",
                citations=None,
                created_at=now,
            )
            for i in range(6)
        )

        conversation = Conversation(
            id=uuid.uuid4().hex,
            notebook_id="notebook123",
            title=None,
            messages=messages,
            created_at=now,
            updated_at=now,
        )

        # Only get last 2 turns (4 messages)
        context = conversation.get_context_for_rag(max_turns=2)

        assert len(context) == 4  # Last 4 messages

    def test_conversation_immutability(self):
        """Test that conversation is immutable."""
        now = datetime.datetime.now(datetime.timezone.utc)
        conversation = Conversation(
            id=uuid.uuid4().hex,
            notebook_id="notebook123",
            title="Test",
            messages=(),
            created_at=now,
            updated_at=now,
        )

        with pytest.raises(Exception):  # Should raise on mutation
            conversation.title = "New Title"
