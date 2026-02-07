"""Query command and query handlers."""

from src import exceptions
from src.notebook.adapter import repository as notebook_repository_module
from src.query.adapter.pydantic_ai import agent as rag_agent_module
from src.query.schema import command, response
from src.query.service import retrieval


class QueryNotebookHandler:
    """Handler for querying notebooks with RAG."""

    def __init__(
        self,
        notebook_repository: notebook_repository_module.NotebookRepository,
        retrieval_service: retrieval.RetrievalService,
        rag_agent: rag_agent_module.RAGAgent,
    ) -> None:
        self._notebook_repository = notebook_repository
        self._retrieval_service = retrieval_service
        self._rag_agent = rag_agent

    async def handle(
        self, notebook_id: str, cmd: command.QueryNotebook
    ) -> response.QueryAnswer:
        """Process a RAG query against a notebook.

        1. Verify notebook exists
        2. Retrieve relevant chunks
        3. Generate answer with citations
        """
        # Verify notebook exists
        notebook = await self._notebook_repository.find_by_id(notebook_id)
        if notebook is None:
            raise exceptions.NotFoundError(f"Notebook not found: {notebook_id}")

        # Retrieve relevant chunks
        retrieved_chunks = await self._retrieval_service.retrieve(
            notebook_id=notebook_id,
            query=cmd.question,
            max_chunks=cmd.max_sources,
        )

        # Generate answer with citations
        answer = await self._rag_agent.answer(
            question=cmd.question,
            retrieved_chunks=retrieved_chunks,
        )

        return answer
