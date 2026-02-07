"""Synthetic test case generator using LLM."""

import json
import logging
import random

import pydantic_ai

from src.chunk.domain import model as chunk_model
from src.evaluation.domain import model

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a test data generator for a retrieval evaluation system.
Your task is to generate diverse, realistic questions that can be answered from the given passage.

Rules:
- Questions must be self-contained (do not reference "the passage", "the text", "the above", etc.)
- Do not generate yes/no questions
- Generate diverse question types: factual, analytical, comparative, explanatory
- Questions should require information specifically from the passage to answer
- Return valid JSON only"""

USER_PROMPT_TEMPLATE = """Based on the following passage, generate exactly {count} questions that can be answered using the information in this passage.

Passage:
{content}

Return your response as a JSON object with this exact format:
{{"questions": ["question 1", "question 2", ...]}}"""


class SyntheticTestGenerator:
    """Generates synthetic test cases from document chunks using LLM."""

    def __init__(self, eval_model: str = "openai:gpt-4o-mini") -> None:
        self._agent = pydantic_ai.Agent(
            model=eval_model,
            system_prompt=SYSTEM_PROMPT,
        )

    async def generate_questions(
        self,
        chunk: chunk_model.Chunk,
        count: int = 2,
    ) -> list[str]:
        """Generate questions from a chunk's content.

        Args:
            chunk: The source chunk to generate questions from.
            count: Number of questions to generate.

        Returns:
            List of generated questions.
        """
        prompt = USER_PROMPT_TEMPLATE.format(
            count=count,
            content=chunk.content,
        )

        try:
            result = await self._agent.run(prompt)
            return self._parse_questions(result.output, count)
        except Exception as exc:
            logger.warning("Failed to generate questions for chunk %s: %s", chunk.id, exc)
            return []

    def _parse_questions(self, output: str, expected_count: int) -> list[str]:
        """Parse LLM output into a list of questions."""
        # Try to extract JSON from the output
        try:
            # Handle potential markdown code blocks
            cleaned = output.strip()
            if cleaned.startswith("```"):
                # Remove markdown code block markers
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned

            data = json.loads(cleaned)
            questions = data.get("questions", [])
            if isinstance(questions, list):
                return [q for q in questions if isinstance(q, str) and q.strip()]
        except (json.JSONDecodeError, AttributeError):
            logger.warning("Failed to parse LLM output as JSON: %s", output[:200])

        return []

    @staticmethod
    def sample_chunks(
        chunks: list[chunk_model.Chunk],
        max_sample: int,
    ) -> list[chunk_model.Chunk]:
        """Sample chunks for test generation.

        Args:
            chunks: All available chunks.
            max_sample: Maximum number of chunks to sample.

        Returns:
            Sampled list of chunks.
        """
        if len(chunks) <= max_sample:
            return chunks
        return random.sample(chunks, max_sample)

    async def generate_test_cases(
        self,
        chunks: list[chunk_model.Chunk],
        questions_per_chunk: int = 2,
        max_chunks_sample: int = 50,
    ) -> list[model.TestCase]:
        """Generate test cases from a list of chunks.

        Args:
            chunks: Available chunks to generate questions from.
            questions_per_chunk: Number of questions per chunk.
            max_chunks_sample: Maximum chunks to sample.

        Returns:
            List of generated TestCase entities.
        """
        sampled = self.sample_chunks(chunks, max_chunks_sample)
        test_cases: list[model.TestCase] = []

        for chunk in sampled:
            questions = await self.generate_questions(chunk, questions_per_chunk)
            for question in questions:
                test_case = model.TestCase.create(
                    question=question,
                    ground_truth_chunk_ids=(chunk.id,),
                    source_chunk_id=chunk.id,
                )
                test_cases.append(test_case)

        return test_cases
