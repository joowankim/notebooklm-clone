"""Conversation command and query handlers."""

import datetime
import uuid

from src import exceptions
from src.common import pagination
from src.conversation.adapter import repository as conversation_repository_module
from src.conversation.domain import model
from src.conversation.schema import command, query, response
from src.notebook.adapter import repository as notebook_repository_module
from src.query.adapter.pydantic_ai import agent as rag_agent_module
from src.query.service import retrieval


class CreateConversationHandler:
    """Handler for creating a new conversation."""

    def __init__(
        self,
        notebook_repository: notebook_repository_module.NotebookRepository,
        conversation_repository: conversation_repository_module.ConversationRepository,
    ) -> None:
        self._notebook_repository = notebook_repository
        self._conversation_repository = conversation_repository

    async def handle(
        self, notebook_id: str, cmd: command.CreateConversation
    ) -> response.ConversationId:
        """Create a new conversation in a notebook."""
        # Verify notebook exists
        notebook = await self._notebook_repository.find_by_id(notebook_id)
        if notebook is None:
            raise exceptions.NotFoundError(f"Notebook not found: {notebook_id}")

        now = datetime.datetime.now(datetime.timezone.utc)
        conversation = model.Conversation(
            id=uuid.uuid4().hex,
            notebook_id=notebook_id,
            title=cmd.title,
            messages=(),
            created_at=now,
            updated_at=now,
        )

        await self._conversation_repository.save(conversation)
        return response.ConversationId(id=conversation.id)


class GetConversationHandler:
    """Handler for getting conversation details."""

    def __init__(self, conversation_repository: conversation_repository_module.ConversationRepository) -> None:
        self._conversation_repository = conversation_repository

    async def handle(self, conversation_id: str) -> response.ConversationDetail:
        """Get conversation with all messages."""
        conversation = await self._conversation_repository.find_by_id(conversation_id)
        if conversation is None:
            raise exceptions.NotFoundError(f"Conversation not found: {conversation_id}")
        return response.ConversationDetail.from_model(conversation)


class ListConversationsHandler:
    """Handler for listing conversations."""

    def __init__(self, conversation_repository: conversation_repository_module.ConversationRepository) -> None:
        self._conversation_repository = conversation_repository

    async def handle(
        self, qry: query.ListConversations
    ) -> pagination.PaginationSchema[response.ConversationDetail]:
        """List conversations for a notebook with pagination."""
        result = await self._conversation_repository.list_by_notebook(
            notebook_id=qry.notebook_id,
            query=qry,
        )
        return pagination.PaginationSchema(
            items=[response.ConversationDetail.from_model(c) for c in result.items],
            total=result.total,
            page=result.page,
            size=result.size,
            pages=result.pages,
        )


class DeleteConversationHandler:
    """Handler for deleting a conversation."""

    def __init__(self, conversation_repository: conversation_repository_module.ConversationRepository) -> None:
        self._conversation_repository = conversation_repository

    async def handle(self, conversation_id: str) -> None:
        """Delete a conversation."""
        deleted = await self._conversation_repository.delete(conversation_id)
        if not deleted:
            raise exceptions.NotFoundError(f"Conversation not found: {conversation_id}")


class SendMessageHandler:
    """Handler for sending a message in a conversation (multi-turn RAG)."""

    def __init__(
        self,
        conversation_repository: conversation_repository_module.ConversationRepository,
        retrieval_service: retrieval.RetrievalService,
        rag_agent: rag_agent_module.RAGAgent,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._retrieval_service = retrieval_service
        self._rag_agent = rag_agent

    async def handle(
        self, conversation_id: str, cmd: command.SendMessage
    ) -> response.MessageResponse:
        """Send a message and get AI response.

        1. Get conversation with history
        2. Add user message
        3. Retrieve relevant chunks
        4. Generate answer with conversation context
        5. Add assistant message
        6. Return both messages
        """
        # Get conversation
        conversation = await self._conversation_repository.find_by_id(conversation_id)
        if conversation is None:
            raise exceptions.NotFoundError(f"Conversation not found: {conversation_id}")

        now = datetime.datetime.now(datetime.timezone.utc)

        # Create user message
        user_message = model.Message(
            id=uuid.uuid4().hex,
            role=model.MessageRole.USER,
            content=cmd.content,
            citations=None,
            created_at=now,
        )

        # Add user message to conversation
        conversation = conversation.add_message(user_message)
        await self._conversation_repository.add_message(conversation_id, user_message)

        # Update conversation title if first message
        if conversation.title and len(conversation.messages) == 1:
            await self._conversation_repository.save(conversation)

        # Get conversation context for RAG
        conversation_context = conversation.get_context_for_rag(max_turns=5)

        # Retrieve relevant chunks
        retrieved_chunks = await self._retrieval_service.retrieve(
            notebook_id=conversation.notebook_id,
            query=cmd.content,
            max_chunks=10,
        )

        # Generate answer with conversation context
        answer = await self._rag_agent.answer(
            question=cmd.content,
            retrieved_chunks=retrieved_chunks,
            conversation_history=conversation_context[:-1],  # Exclude current message
        )

        # Create assistant message
        assistant_message = model.Message(
            id=uuid.uuid4().hex,
            role=model.MessageRole.ASSISTANT,
            content=answer.answer,
            citations=[c.model_dump() for c in answer.citations] if answer.citations else None,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )

        # Add assistant message
        await self._conversation_repository.add_message(conversation_id, assistant_message)

        return response.MessageResponse(
            user_message=response.MessageDetail.from_model(user_message),
            assistant_message=response.MessageDetail.from_model(assistant_message),
        )
