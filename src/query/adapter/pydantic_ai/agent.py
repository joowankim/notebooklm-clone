"""PydanticAI RAG agent implementation."""

import re

from pydantic_ai import Agent

from src.query.adapter.pydantic_ai import prompts
from src.query.schema.response import Citation, QueryAnswer
from src.query.service.retrieval import RetrievedChunk
from src.settings import settings


class RAGAgent:
    """RAG agent using PydanticAI for question answering with citations."""

    def __init__(self, model: str = "openai:gpt-4o-mini"):
        self._model = model
        self._agent = Agent(
            model=self._model,
            system_prompt=prompts.SYSTEM_PROMPT,
        )

    async def answer(
        self,
        question: str,
        retrieved_chunks: list[RetrievedChunk],
    ) -> QueryAnswer:
        """Generate an answer with citations.

        Args:
            question: The user's question.
            retrieved_chunks: Retrieved chunks with document context.

        Returns:
            QueryAnswer with answer text and citations.
        """
        if not retrieved_chunks:
            return QueryAnswer(
                answer="I cannot find any relevant information in the sources to answer this question.",
                citations=[],
                sources_used=0,
            )

        # Build sources for the prompt
        sources = []
        chunk_map: dict[int, RetrievedChunk] = {}  # index -> chunk

        for i, retrieved in enumerate(retrieved_chunks, start=1):
            sources.append({
                "index": i,
                "title": retrieved.document.title,
                "url": retrieved.document.url,
                "content": retrieved.chunk.content,
            })
            chunk_map[i] = retrieved

        # Format the prompt
        sources_text = prompts.format_sources(sources)
        user_prompt = prompts.format_user_prompt(question, sources_text)

        # Run the agent
        result = await self._agent.run(user_prompt)
        answer_text = result.output

        # Extract citations from the answer
        citations = self._extract_citations(answer_text, chunk_map)

        return QueryAnswer(
            answer=answer_text,
            citations=citations,
            sources_used=len(retrieved_chunks),
        )

    def _extract_citations(
        self,
        answer: str,
        chunk_map: dict[int, RetrievedChunk],
    ) -> list[Citation]:
        """Extract citation objects from the answer text.

        Finds [1], [2], etc. patterns and maps them to source chunks.
        """
        # Find all citation references
        pattern = r"\[(\d+)\]"
        matches = re.findall(pattern, answer)

        # Deduplicate while preserving order
        seen: set[int] = set()
        unique_indices: list[int] = []
        for match in matches:
            idx = int(match)
            if idx not in seen and idx in chunk_map:
                seen.add(idx)
                unique_indices.append(idx)

        # Build citation objects
        citations: list[Citation] = []
        for idx in unique_indices:
            retrieved = chunk_map[idx]
            chunk = retrieved.chunk
            document = retrieved.document

            # Create snippet (truncate if too long)
            snippet = chunk.content[:200]
            if len(chunk.content) > 200:
                snippet += "..."

            citations.append(
                Citation(
                    citation_index=idx,
                    document_id=document.id,
                    chunk_id=chunk.id,
                    document_title=document.title,
                    document_url=document.url,
                    char_start=chunk.char_start,
                    char_end=chunk.char_end,
                    snippet=snippet,
                )
            )

        return citations
