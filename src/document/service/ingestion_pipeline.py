"""Ingestion pipeline service for processing documents."""

import asyncio
import logging

from src.chunk.adapter.embedding import port as embedding_port
from src.chunk.adapter import repository as chunk_repository_module
from src.chunk.domain import model as chunk_model
from src import database as database_module
from src.document.adapter.extractor import port as extractor_port
from src.document.adapter import repository as document_repository_module
from src.document.domain import model
from src.document.service.chunking import service as chunking_service_module

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
        content_extractor: extractor_port.ContentExtractorPort,
        embedding_provider: embedding_port.EmbeddingProviderPort,
        chunking_service: chunking_service_module.ChunkingService,
        batch_size: int = 10,
    ) -> None:
        self._content_extractor = content_extractor
        self._embedding_provider = embedding_provider
        self._chunking_service = chunking_service
        self._batch_size = batch_size

    async def process(self, document_id: str) -> model.Document | None:
        """Process a document through the complete ingestion pipeline.

        Creates its own database session to work independently of request lifecycle.

        Args:
            document_id: ID of document in PENDING status to process.

        Returns:
            Updated document with COMPLETED or FAILED status.
        """
        async with database_module.async_session_factory() as session:
            document_repository = document_repository_module.DocumentRepository(session)
            chunk_repository = chunk_repository_module.ChunkRepository(session)

            # Load document
            document = await document_repository.find_by_id(document_id)
            if document is None:
                logger.error(f"Document not found: {document_id}")
                return None

            # Mark as processing
            document = document.mark_processing()
            await document_repository.save(document)
            await session.commit()

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
                    chunk_model.Chunk.create(
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
                await chunk_repository.delete_by_document(document.id)

                # Step 6: Save chunks with embeddings
                await chunk_repository.save_batch(chunks_with_embeddings)
                logger.info(f"Saved {len(chunks_with_embeddings)} chunks")

                # Step 7: Mark document as completed
                document = document.mark_completed(
                    title=extracted.title,
                    content_hash=extracted.content_hash,
                )
                await document_repository.save(document)
                await session.commit()

                logger.info(f"Document ingestion completed: {document.id}")
                return document

            except Exception as e:
                # Mark as failed
                logger.error(f"Document ingestion failed: {document.id}, error: {e}")
                await session.rollback()

                # Create new transaction for failure update
                document = await document_repository.find_by_id(document_id)
                if document:
                    document = document.mark_failed(str(e))
                    await document_repository.save(document)
                    await session.commit()

                return document

    async def _generate_embeddings(self, chunks: list[chunk_model.Chunk]) -> list[chunk_model.Chunk]:
        """Generate embeddings for chunks in batches."""
        if not chunks:
            return []

        result: list[chunk_model.Chunk] = []

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

    def __init__(self, pipeline: IngestionPipeline) -> None:
        self._pipeline = pipeline
        self._tasks: dict[str, asyncio.Task] = {}  # type: ignore[type-arg]

    def trigger_ingestion(self, document: model.Document) -> None:
        """Trigger async ingestion for a document.

        Creates an asyncio task to process the document in the background.
        The task uses its own database session, independent of the request.
        """
        if document.id in self._tasks:
            # Already processing
            return

        task = asyncio.create_task(self._process_with_cleanup(document.id))
        self._tasks[document.id] = task

    async def _process_with_cleanup(self, document_id: str) -> None:
        """Process document and cleanup task reference."""
        try:
            await self._pipeline.process(document_id)
        except Exception as e:
            logger.error(f"Background ingestion error for {document_id}: {e}")
        finally:
            self._tasks.pop(document_id, None)

    def is_processing(self, document_id: str) -> bool:
        """Check if a document is currently being processed."""
        return document_id in self._tasks
