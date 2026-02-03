"""Tests for conversation repository."""

import datetime
import uuid

import pytest

from src.conversation.adapter.repository import ConversationRepository
from src.conversation.domain.model import Conversation, Message, MessageRole
from src.common import ListQuery
from src.notebook.adapter.repository import NotebookRepository
from src.notebook.domain.model import Notebook


class TestConversationRepository:
    """Tests for ConversationRepository."""

    @pytest.fixture
    async def notebook(self, test_session) -> Notebook:
        """Create a test notebook."""
        notebook = Notebook.create(
            name="Test Notebook",
            description="For conversation tests",
        )
        repo = NotebookRepository(test_session)
        await repo.save(notebook)
        return notebook

    @pytest.fixture
    def repository(self, test_session) -> ConversationRepository:
        """Create repository instance."""
        return ConversationRepository(test_session)

    @pytest.mark.asyncio
    async def test_save_and_find_conversation(self, repository, notebook):
        """Test saving and finding a conversation."""
        now = datetime.datetime.now(datetime.timezone.utc)
        conversation = Conversation(
            id=uuid.uuid4().hex,
            notebook_id=notebook.id,
            title="Test Conversation",
            messages=(),
            created_at=now,
            updated_at=now,
        )

        await repository.save(conversation)
        found = await repository.find_by_id(conversation.id)

        assert found is not None
        assert found.id == conversation.id
        assert found.title == "Test Conversation"
        assert found.notebook_id == notebook.id

    @pytest.mark.asyncio
    async def test_find_nonexistent_conversation(self, repository):
        """Test finding non-existent conversation returns None."""
        found = await repository.find_by_id("nonexistent")
        assert found is None

    @pytest.mark.asyncio
    async def test_add_message_to_conversation(self, repository, notebook):
        """Test adding a message to a conversation."""
        now = datetime.datetime.now(datetime.timezone.utc)
        conversation = Conversation(
            id=uuid.uuid4().hex,
            notebook_id=notebook.id,
            title=None,
            messages=(),
            created_at=now,
            updated_at=now,
        )
        await repository.save(conversation)

        # Add a message
        message = Message(
            id=uuid.uuid4().hex,
            role=MessageRole.USER,
            content="Hello, what is AI?",
            citations=None,
            created_at=now,
        )
        await repository.add_message(conversation.id, message)

        # Find and verify
        found = await repository.find_by_id(conversation.id)
        assert found is not None
        assert len(found.messages) == 1
        assert found.messages[0].content == "Hello, what is AI?"
        assert found.messages[0].role == MessageRole.USER

    @pytest.mark.asyncio
    async def test_delete_conversation(self, repository, notebook):
        """Test deleting a conversation."""
        now = datetime.datetime.now(datetime.timezone.utc)
        conversation = Conversation(
            id=uuid.uuid4().hex,
            notebook_id=notebook.id,
            title="To Delete",
            messages=(),
            created_at=now,
            updated_at=now,
        )
        await repository.save(conversation)

        # Delete
        result = await repository.delete(conversation.id)
        assert result is True

        # Verify deleted
        found = await repository.find_by_id(conversation.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_conversation(self, repository):
        """Test deleting non-existent conversation returns False."""
        result = await repository.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_conversations_by_notebook(self, repository, notebook):
        """Test listing conversations by notebook."""
        now = datetime.datetime.now(datetime.timezone.utc)

        # Create multiple conversations
        for i in range(3):
            conversation = Conversation(
                id=uuid.uuid4().hex,
                notebook_id=notebook.id,
                title=f"Conversation {i}",
                messages=(),
                created_at=now,
                updated_at=now,
            )
            await repository.save(conversation)

        # List conversations
        result = await repository.list_by_notebook(
            notebook_id=notebook.id,
            query=ListQuery(page=1, size=10),
        )

        assert result.total == 3
        assert len(result.items) == 3

    @pytest.mark.asyncio
    async def test_list_conversations_pagination(self, repository, notebook):
        """Test conversation list pagination."""
        now = datetime.datetime.now(datetime.timezone.utc)

        # Create 5 conversations
        for i in range(5):
            conversation = Conversation(
                id=uuid.uuid4().hex,
                notebook_id=notebook.id,
                title=f"Conversation {i}",
                messages=(),
                created_at=now,
                updated_at=now,
            )
            await repository.save(conversation)

        # Get page 1 with size 2
        result = await repository.list_by_notebook(
            notebook_id=notebook.id,
            query=ListQuery(page=1, size=2),
        )

        assert result.total == 5
        assert len(result.items) == 2
        assert result.pages == 3

    @pytest.mark.asyncio
    async def test_conversation_with_multiple_messages(self, repository, notebook):
        """Test conversation with multiple messages maintains order."""
        now = datetime.datetime.now(datetime.timezone.utc)
        conversation = Conversation(
            id=uuid.uuid4().hex,
            notebook_id=notebook.id,
            title="Multi-message",
            messages=(),
            created_at=now,
            updated_at=now,
        )
        await repository.save(conversation)

        # Add multiple messages
        messages = [
            Message(
                id=uuid.uuid4().hex,
                role=MessageRole.USER,
                content="Question 1",
                citations=None,
                created_at=now + datetime.timedelta(seconds=1),
            ),
            Message(
                id=uuid.uuid4().hex,
                role=MessageRole.ASSISTANT,
                content="Answer 1",
                citations=None,
                created_at=now + datetime.timedelta(seconds=2),
            ),
            Message(
                id=uuid.uuid4().hex,
                role=MessageRole.USER,
                content="Question 2",
                citations=None,
                created_at=now + datetime.timedelta(seconds=3),
            ),
        ]

        for msg in messages:
            await repository.add_message(conversation.id, msg)

        # Find and verify order
        found = await repository.find_by_id(conversation.id)
        assert found is not None
        assert len(found.messages) == 3
        assert found.messages[0].content == "Question 1"
        assert found.messages[1].content == "Answer 1"
        assert found.messages[2].content == "Question 2"
