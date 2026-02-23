"""LLM-as-Judge for evaluating generation quality."""

import json
import logging

import pydantic_ai

from src.chunk.domain import model as chunk_model

logger = logging.getLogger(__name__)

FAITHFULNESS_SYSTEM_PROMPT = """You are an evaluation agent that assesses whether a generated answer is grounded in the provided context chunks.

Your task: Score faithfulness on a scale of 0.0 to 1.0:
- 1.0: Answer is fully grounded in the context, no hallucinations
- 0.5: Answer is partially grounded, contains some unsupported claims
- 0.0: Answer contradicts context or is entirely hallucinated

Return only valid JSON: {"score": <float>, "reasoning": "<brief explanation>"}"""

FAITHFULNESS_USER_TEMPLATE = """Question: {question}

Generated Answer: {answer}

Context Chunks:
{context}

Score the faithfulness of the answer based on the context."""

RELEVANCY_SYSTEM_PROMPT = """You are an evaluation agent that assesses whether a generated answer is relevant to the question.

Your task: Score answer relevancy on a scale of 0.0 to 1.0:
- 1.0: Answer directly and completely addresses the question
- 0.5: Answer is partially relevant but incomplete or tangential
- 0.0: Answer does not address the question

Return only valid JSON: {"score": <float>, "reasoning": "<brief explanation>"}"""

RELEVANCY_USER_TEMPLATE = """Question: {question}

Generated Answer: {answer}

Score the relevancy of the answer to the question."""

CITATION_SUPPORT_SYSTEM_PROMPT = """You are an evaluation agent that assesses whether a cited source genuinely supports the claim it is cited for.

Your task: Score citation support on a scale of 0.0 to 1.0:
- 1.0: The cited source directly and completely supports the claim
- 0.5: The cited source partially supports or is tangentially related
- 0.0: The cited source does not support the claim at all

Return only valid JSON: {"score": <float>, "reasoning": "<brief explanation>"}"""

CITATION_SUPPORT_USER_TEMPLATE = """Claim: {claim}

Cited Source Content: {chunk_content}

Score how well the cited source supports the claim."""

HALLUCINATION_SYSTEM_PROMPT = """You are an evaluation agent that performs claim-level hallucination analysis.

Your task: Decompose the answer into atomic claims and verify each against the context.
For each claim, classify as:
- "supported": Claim is directly supported by context
- "partially_supported": Claim is partially supported
- "contradicted": Claim contradicts the context
- "fabricated": Claim has no basis in context
- "unverifiable": Cannot be verified from context

Return only valid JSON: {"claims": [{"claim_text": "<text>", "verdict": "<verdict>", "supporting_chunks": [<indices>], "reasoning": "<brief>"}, ...]}"""

HALLUCINATION_USER_TEMPLATE = """Question: {question}

Generated Answer: {answer}

Context Chunks:
{context}

Decompose the answer into atomic claims and verify each against the context."""

COMPLETENESS_SYSTEM_PROMPT = """You are an evaluation agent that assesses how comprehensively an answer uses the relevant information from the provided context.

Your task: Score answer completeness on a scale of 0.0 to 1.0:
- 1.0: Answer comprehensively uses all relevant information from context
- 0.5: Answer uses some relevant information but misses key details
- 0.0: Answer fails to use relevant context information

Return only valid JSON: {"score": <float>, "reasoning": "<brief explanation>"}"""

COMPLETENESS_USER_TEMPLATE = """Question: {question}

Generated Answer: {answer}

Context Chunks:
{context}

Score how comprehensively the answer uses the relevant information from the context."""


class LLMJudge:
    """LLM-as-Judge for evaluating generation quality."""

    def __init__(self, eval_model: str) -> None:
        self._faithfulness_agent = pydantic_ai.Agent(
            model=eval_model,
            system_prompt=FAITHFULNESS_SYSTEM_PROMPT,
        )
        self._relevancy_agent = pydantic_ai.Agent(
            model=eval_model,
            system_prompt=RELEVANCY_SYSTEM_PROMPT,
        )
        self._citation_agent = pydantic_ai.Agent(
            model=eval_model,
            system_prompt=CITATION_SUPPORT_SYSTEM_PROMPT,
        )
        self._hallucination_agent = pydantic_ai.Agent(
            model=eval_model,
            system_prompt=HALLUCINATION_SYSTEM_PROMPT,
        )
        self._completeness_agent = pydantic_ai.Agent(
            model=eval_model,
            system_prompt=COMPLETENESS_SYSTEM_PROMPT,
        )

    async def score_faithfulness(
        self,
        question: str,
        answer: str,
        context_chunks: list[chunk_model.Chunk],
    ) -> float:
        """Score answer faithfulness (grounding in context)."""
        context_text = "\n\n".join(
            f"[{i + 1}] {chunk.content}"
            for i, chunk in enumerate(context_chunks)
        )
        prompt = FAITHFULNESS_USER_TEMPLATE.format(
            question=question,
            answer=answer,
            context=context_text,
        )

        try:
            result = await self._faithfulness_agent.run(prompt)
            return self._parse_score(result.output)
        except Exception as exc:
            logger.warning("Failed to score faithfulness: %s", exc)
            return 0.0

    async def score_answer_relevancy(
        self,
        question: str,
        answer: str,
    ) -> float:
        """Score answer relevancy to question."""
        prompt = RELEVANCY_USER_TEMPLATE.format(
            question=question,
            answer=answer,
        )

        try:
            result = await self._relevancy_agent.run(prompt)
            return self._parse_score(result.output)
        except Exception as exc:
            logger.warning("Failed to score relevancy: %s", exc)
            return 0.0

    async def score_citation_support(
        self,
        claim_with_citation: str,
        cited_chunk_content: str,
    ) -> float:
        """Score whether a cited source supports the claim."""
        prompt = CITATION_SUPPORT_USER_TEMPLATE.format(
            claim=claim_with_citation,
            chunk_content=cited_chunk_content,
        )

        try:
            result = await self._citation_agent.run(prompt)
            return self._parse_score(result.output)
        except Exception as exc:
            logger.warning("Failed to score citation support: %s", exc)
            return 0.0

    async def analyze_hallucinations(
        self,
        question: str,
        answer: str,
        context_chunks: list[chunk_model.Chunk],
    ) -> dict[str, list[dict[str, object]]]:
        """Decompose answer into claims and verify against context."""
        context_text = "\n\n".join(
            f"[{i + 1}] {chunk.content}"
            for i, chunk in enumerate(context_chunks)
        )
        prompt = HALLUCINATION_USER_TEMPLATE.format(
            question=question,
            answer=answer,
            context=context_text,
        )

        try:
            result = await self._hallucination_agent.run(prompt)
            return self._parse_claims(result.output)
        except Exception as exc:
            logger.warning("Failed to analyze hallucinations: %s", exc)
            return {"claims": []}

    async def score_answer_completeness(
        self,
        question: str,
        answer: str,
        context_chunks: list[chunk_model.Chunk],
    ) -> float:
        """Score how completely the answer uses relevant context."""
        context_text = "\n\n".join(
            f"[{i + 1}] {chunk.content}"
            for i, chunk in enumerate(context_chunks)
        )
        prompt = COMPLETENESS_USER_TEMPLATE.format(
            question=question,
            answer=answer,
            context=context_text,
        )

        try:
            result = await self._completeness_agent.run(prompt)
            return self._parse_score(result.output)
        except Exception as exc:
            logger.warning("Failed to score answer completeness: %s", exc)
            return 0.0

    def _parse_score(self, output: str) -> float:
        """Parse LLM output to extract score."""
        try:
            cleaned = self._strip_markdown_code_block(output)
            data = json.loads(cleaned)
            score = float(data.get("score", 0.0))
            return max(0.0, min(1.0, score))
        except (json.JSONDecodeError, ValueError, TypeError):
            logger.warning(
                "Failed to parse score from output: %s", output[:200]
            )
            return 0.0

    def _parse_claims(
        self, output: str,
    ) -> dict[str, list[dict[str, object]]]:
        """Parse LLM output to extract claims data."""
        try:
            cleaned = self._strip_markdown_code_block(output)
            data = json.loads(cleaned)
            claims = data.get("claims", [])
            if not isinstance(claims, list):
                return {"claims": []}
            return {"claims": claims}
        except (json.JSONDecodeError, ValueError, TypeError):
            logger.warning(
                "Failed to parse claims from output: %s", output[:200]
            )
            return {"claims": []}

    @staticmethod
    def _strip_markdown_code_block(output: str) -> str:
        """Remove markdown code block markers from output."""
        cleaned = output.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if len(lines) > 2:
                cleaned = "\n".join(lines[1:-1])
        return cleaned
