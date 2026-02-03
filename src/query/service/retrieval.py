"""Retrieval service for RAG queries."""

from src.chunk.adapter.embedding.port import EmbeddingProviderPort
from src.chunk.adapter.repository import ChunkRepository
from src.chunk.domain.model import Chunk
from src.document.adapter.repository import DocumentRepository
from src.document.domain.model import Document


class RetrievedChunk:
    """A retrieved chunk with its source document."""

    def __init__(self, chunk: Chunk, document: Document, score: float):
        self.chunk = chunk
        self.document = document
        self.score = score


class RetrievalService:
    """Service for retrieving relevant chunks for a query."""

    def __init__(
        self,
        chunk_repository: ChunkRepository,
        document_repository: DocumentRepository,
        embedding_provider: EmbeddingProviderPort,
    ):
        self._chunk_repository = chunk_repository
        self._document_repository = document_repository
        self._embedding_provider = embedding_provider

    async def retrieve(
        self,
        notebook_id: str,
        query: str,
        max_chunks: int = 5,
    ) -> list[RetrievedChunk]:
        """Retrieve relevant chunks for a query.

        Args:
            notebook_id: Notebook to search within.
            query: The search query.
            max_chunks: Maximum number of chunks to return.

        Returns:
            List of RetrievedChunk with document context.
        """
        # Generate query embedding
        query_embedding = await self._embedding_provider.embed(query)

        # Search for similar chunks
        results = await self._chunk_repository.search_similar_in_notebook(
            embedding=query_embedding,
            notebook_id=notebook_id,
            limit=max_chunks,
        )

        if not results:
            return []

        # Fetch documents for the chunks
        document_ids = list(set(chunk.document_id for chunk, _ in results))
        documents: dict[str, Document] = {}

        for doc_id in document_ids:
            doc = await self._document_repository.find_by_id(doc_id)
            if doc:
                documents[doc_id] = doc

        # Combine chunks with documents
        retrieved: list[RetrievedChunk] = []
        for chunk, score in results:
            document = documents.get(chunk.document_id)
            if document:
                retrieved.append(RetrievedChunk(chunk, document, score))

        return retrieved
