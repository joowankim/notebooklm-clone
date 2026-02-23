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
- Generate diverse question types and classify each by difficulty
- Questions should require information specifically from the passage to answer
- Return valid JSON only

Difficulty classifications:
- factual: Direct information recall from the passage
- analytical: Requires analyzing or comparing information
- inferential: Requires drawing conclusions beyond explicit text
- paraphrased: Rewording of passage content"""

USER_PROMPT_TEMPLATE = """Based on the following passage, generate exactly {count} questions that can be answered using the information in this passage.

Passage:
{content}

Return your response as a JSON object with this exact format:
{{"questions": [{{"text": "question 1", "difficulty": "factual"}}, ...]}}

Valid difficulty values: factual, analytical, inferential, paraphrased"""


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
    ) -> list[tuple[str, model.QuestionDifficulty | None]]:
        """Generate questions from a chunk's content.

        Args:
            chunk: The source chunk to generate questions from.
            count: Number of questions to generate.

        Returns:
            List of (question_text, difficulty) tuples.
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

    def _parse_questions(
        self,
        output: str,
        expected_count: int,
    ) -> list[tuple[str, model.QuestionDifficulty | None]]:
        """Parse LLM output into a list of (question, difficulty) tuples."""
        try:
            cleaned = self._strip_markdown_code_block(output)
            data = json.loads(cleaned)
            questions = data.get("questions", [])
            if isinstance(questions, list):
                return self._extract_question_tuples(questions)
        except (json.JSONDecodeError, AttributeError):
            logger.warning("Failed to parse LLM output as JSON: %s", output[:200])

        return []

    @staticmethod
    def _strip_markdown_code_block(output: str) -> str:
        """Remove markdown code block markers from output."""
        cleaned = output.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned
        return cleaned

    def _extract_question_tuples(
        self,
        questions: list[dict[str, str] | str],
    ) -> list[tuple[str, model.QuestionDifficulty | None]]:
        """Extract (text, difficulty) tuples from parsed question items."""
        results: list[tuple[str, model.QuestionDifficulty | None]] = []
        for item in questions:
            if isinstance(item, str) and item.strip():
                results.append((item, None))
            elif isinstance(item, dict):
                text = item.get("text", "")
                if not text or not text.strip():
                    continue
                difficulty = self._parse_difficulty(item.get("difficulty"))
                results.append((text, difficulty))
        return results

    def _parse_difficulty(
        self,
        raw_value: str | None,
    ) -> model.QuestionDifficulty | None:
        """Parse a difficulty string into a QuestionDifficulty enum."""
        if raw_value is None:
            return None
        try:
            return model.QuestionDifficulty(raw_value.lower())
        except ValueError:
            logger.warning("Unknown difficulty value: %s", raw_value)
            return None

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
            for question_text, difficulty in questions:
                test_case = model.TestCase.create(
                    question=question_text,
                    ground_truth_chunk_ids=(chunk.id,),
                    source_chunk_id=chunk.id,
                    difficulty=difficulty,
                )
                test_cases.append(test_case)

        return test_cases
