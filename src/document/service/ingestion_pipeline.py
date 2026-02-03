"""Ingestion pipeline service for processing documents."""

import asyncio
import logging

from src.chunk.adapter.embedding.port import EmbeddingProviderPort
from src.chunk.adapter.repository import ChunkRepository
from src.chunk.domain.model import Chunk
from src.document.adapter.extractor.port import ContentExtractorPort
from src.document.adapter.repository import DocumentRepository
from src.document.domain.model import Document
from src.document.service.chunking.service import ChunkingService

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Pipeline for ingesting documents: Extract → Chunk → Embed → Store.

    This service orchestrates the complete document processing flow:
    1. Extract content from URL
    2. Chunk content with position tracking
    3. Generate embeddings for each chunk
    4. Store chunks with embeddings
    """

    def __init__(
        self,
        document_repository: DocumentRepository,
        chunk_repository: ChunkRepository,
        content_extractor: ContentExtractorPort,
        embedding_provider: EmbeddingProviderPort,
        chunking_service: ChunkingService,
        batch_size: int = 10,
    ):
        self._document_repository = document_repository
        self._chunk_repository = chunk_repository
        self._content_extractor = content_extractor
        self._embedding_provider = embedding_provider
        self._chunking_service = chunking_service
        self._batch_size = batch_size

    async def process(self, document: Document) -> Document:
        """Process a document through the complete ingestion pipeline.

        Args:
            document: Document in PENDING status to process.

        Returns:
            Updated document with COMPLETED or FAILED status.
        """
        # Mark as processing
        document = document.mark_processing()
        await self._document_repository.save(document)

        try:
            # Step 1: Extract content
            logger.info(f"Extracting content from: {document.url}")
            extracted = await self._content_extractor.extract(document.url)

            # Step 2: Chunk content
            logger.info(f"Chunking content: {extracted.word_count} words")
            chunked_contents = self._chunking_service.chunk(extracted.content)
            logger.info(f"Created {len(chunked_contents)} chunks")

            # Step 3: Create chunk entities
            chunks = [
                Chunk.create(
                    document_id=document.id,
                    content=c.content,
                    char_start=c.char_start,
                    char_end=c.char_end,
                    chunk_index=c.chunk_index,
                    token_count=c.token_count,
                )
                for c in chunked_contents
            ]

            # Step 4: Generate embeddings in batches
            logger.info("Generating embeddings...")
            chunks_with_embeddings = await self._generate_embeddings(chunks)

            # Step 5: Delete existing chunks for this document (in case of retry)
            await self._chunk_repository.delete_by_document(document.id)

            # Step 6: Save chunks with embeddings
            await self._chunk_repository.save_batch(chunks_with_embeddings)
            logger.info(f"Saved {len(chunks_with_embeddings)} chunks")

            # Step 7: Mark document as completed
            document = document.mark_completed(
                title=extracted.title,
                content_hash=extracted.content_hash,
            )
            await self._document_repository.save(document)

            logger.info(f"Document ingestion completed: {document.id}")
            return document

        except Exception as e:
            # Mark as failed
            logger.error(f"Document ingestion failed: {document.id}, error: {e}")
            document = document.mark_failed(str(e))
            await self._document_repository.save(document)
            return document

    async def _generate_embeddings(self, chunks: list[Chunk]) -> list[Chunk]:
        """Generate embeddings for chunks in batches."""
        if not chunks:
            return []

        result: list[Chunk] = []

        # Process in batches
        for i in range(0, len(chunks), self._batch_size):
            batch = chunks[i : i + self._batch_size]
            texts = [chunk.content for chunk in batch]

            embeddings = await self._embedding_provider.embed_batch(texts)

            for chunk, embedding in zip(batch, embeddings):
                result.append(chunk.with_embedding(embedding))

        return result


class BackgroundIngestionService:
    """Service for triggering background ingestion of documents."""

    def __init__(self, pipeline: IngestionPipeline):
        self._pipeline = pipeline
        self._tasks: dict[str, asyncio.Task] = {}

    def trigger_ingestion(self, document: Document) -> None:
        """Trigger async ingestion for a document.

        Creates an asyncio task to process the document in the background.
        """
        if document.id in self._tasks:
            # Already processing
            return

        task = asyncio.create_task(self._process_with_cleanup(document))
        self._tasks[document.id] = task

    async def _process_with_cleanup(self, document: Document) -> None:
        """Process document and cleanup task reference."""
        try:
            await self._pipeline.process(document)
        finally:
            self._tasks.pop(document.id, None)

    def is_processing(self, document_id: str) -> bool:
        """Check if a document is currently being processed."""
        return document_id in self._tasks
