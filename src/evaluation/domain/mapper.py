"""Mapper between Evaluation entities and ORM schemas."""

import json

from src.evaluation.domain import model
from src.infrastructure.models import evaluation as evaluation_schema


class DatasetMapper:
    """Maps between EvaluationDataset domain entity and ORM schema."""

    @staticmethod
    def to_entity(record: evaluation_schema.EvaluationDatasetSchema) -> model.EvaluationDataset:
        """Convert ORM record to domain entity."""
        test_cases = tuple(
            model.TestCase(
                id=tc.id,
                question=tc.question,
                ground_truth_chunk_ids=tuple(json.loads(tc.ground_truth_chunk_ids)),
                source_chunk_id=tc.source_chunk_id,
                difficulty=model.QuestionDifficulty(tc.difficulty) if tc.difficulty else None,
                created_at=tc.created_at,
            )
            for tc in sorted(record.test_cases, key=lambda t: t.created_at)
        )

        return model.EvaluationDataset(
            id=record.id,
            notebook_id=record.notebook_id,
            name=record.name,
            status=model.DatasetStatus(record.status),
            questions_per_chunk=record.questions_per_chunk,
            max_chunks_sample=record.max_chunks_sample,
            expand_ground_truth=record.expand_ground_truth if record.expand_ground_truth is not None else False,
            similarity_threshold=record.similarity_threshold,
            error_message=record.error_message,
            test_cases=test_cases,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def to_record(entity: model.EvaluationDataset) -> evaluation_schema.EvaluationDatasetSchema:
        """Convert domain entity to ORM record."""
        return evaluation_schema.EvaluationDatasetSchema(
            id=entity.id,
            notebook_id=entity.notebook_id,
            name=entity.name,
            status=entity.status.value,
            questions_per_chunk=entity.questions_per_chunk,
            max_chunks_sample=entity.max_chunks_sample,
            expand_ground_truth=entity.expand_ground_truth,
            similarity_threshold=entity.similarity_threshold,
            error_message=entity.error_message,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def test_case_to_record(
        test_case: model.TestCase,
        dataset_id: str,
    ) -> evaluation_schema.EvaluationTestCaseSchema:
        """Convert TestCase to ORM record."""
        return evaluation_schema.EvaluationTestCaseSchema(
            id=test_case.id,
            dataset_id=dataset_id,
            question=test_case.question,
            ground_truth_chunk_ids=json.dumps(list(test_case.ground_truth_chunk_ids)),
            source_chunk_id=test_case.source_chunk_id,
            difficulty=test_case.difficulty.value if test_case.difficulty else None,
            created_at=test_case.created_at,
        )


class RunMapper:
    """Maps between EvaluationRun domain entity and ORM schema."""

    @staticmethod
    def to_entity(record: evaluation_schema.EvaluationRunSchema) -> model.EvaluationRun:
        """Convert ORM record to domain entity."""
        results = tuple(
            model.TestCaseResult(
                id=r.id,
                test_case_id=r.test_case_id,
                retrieved_chunk_ids=tuple(json.loads(r.retrieved_chunk_ids)),
                retrieved_scores=tuple(json.loads(r.retrieved_scores)),
                precision=r.precision,
                recall=r.recall,
                hit=r.hit,
                reciprocal_rank=r.reciprocal_rank,
                generated_answer=r.generated_answer,
                faithfulness=r.faithfulness,
                answer_relevancy=r.answer_relevancy,
                ndcg=r.ndcg if r.ndcg is not None else 0.0,
                map_score=r.map_score if r.map_score is not None else 0.0,
                citation_precision=r.citation_precision,
                citation_recall=r.citation_recall,
                phantom_citation_count=r.phantom_citation_count,
                citation_support_score=r.citation_support_score,
                hallucination_rate=r.hallucination_rate,
                contradiction_count=r.contradiction_count,
                fabrication_count=r.fabrication_count,
                total_claims=r.total_claims,
                answer_completeness=r.answer_completeness,
            )
            for r in record.results
        )

        return model.EvaluationRun(
            id=record.id,
            dataset_id=record.dataset_id,
            status=model.RunStatus(record.status),
            k=record.k,
            evaluation_type=model.EvaluationType(record.evaluation_type),
            precision_at_k=record.precision_at_k,
            recall_at_k=record.recall_at_k,
            hit_rate_at_k=record.hit_rate_at_k,
            mrr=record.mrr,
            mean_faithfulness=record.mean_faithfulness,
            mean_answer_relevancy=record.mean_answer_relevancy,
            ndcg_at_k=record.ndcg_at_k,
            map_at_k=record.map_at_k,
            generation_model=record.generation_model,
            mean_citation_precision=record.mean_citation_precision,
            mean_citation_recall=record.mean_citation_recall,
            mean_hallucination_rate=record.mean_hallucination_rate,
            mean_answer_completeness=record.mean_answer_completeness,
            total_input_tokens=record.total_input_tokens,
            total_output_tokens=record.total_output_tokens,
            estimated_cost_usd=record.estimated_cost_usd,
            error_message=record.error_message,
            results=results,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def to_record(entity: model.EvaluationRun) -> evaluation_schema.EvaluationRunSchema:
        """Convert domain entity to ORM record."""
        return evaluation_schema.EvaluationRunSchema(
            id=entity.id,
            dataset_id=entity.dataset_id,
            status=entity.status.value,
            k=entity.k,
            evaluation_type=entity.evaluation_type.value,
            precision_at_k=entity.precision_at_k,
            recall_at_k=entity.recall_at_k,
            hit_rate_at_k=entity.hit_rate_at_k,
            mrr=entity.mrr,
            mean_faithfulness=entity.mean_faithfulness,
            mean_answer_relevancy=entity.mean_answer_relevancy,
            ndcg_at_k=entity.ndcg_at_k,
            map_at_k=entity.map_at_k,
            generation_model=entity.generation_model,
            mean_citation_precision=entity.mean_citation_precision,
            mean_citation_recall=entity.mean_citation_recall,
            mean_hallucination_rate=entity.mean_hallucination_rate,
            mean_answer_completeness=entity.mean_answer_completeness,
            total_input_tokens=entity.total_input_tokens,
            total_output_tokens=entity.total_output_tokens,
            estimated_cost_usd=entity.estimated_cost_usd,
            error_message=entity.error_message,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def result_to_record(
        result: model.TestCaseResult,
        run_id: str,
    ) -> evaluation_schema.EvaluationTestCaseResultSchema:
        """Convert TestCaseResult to ORM record."""
        return evaluation_schema.EvaluationTestCaseResultSchema(
            id=result.id,
            run_id=run_id,
            test_case_id=result.test_case_id,
            retrieved_chunk_ids=json.dumps(list(result.retrieved_chunk_ids)),
            retrieved_scores=json.dumps(list(result.retrieved_scores)),
            precision=result.precision,
            recall=result.recall,
            hit=result.hit,
            reciprocal_rank=result.reciprocal_rank,
            generated_answer=result.generated_answer,
            faithfulness=result.faithfulness,
            answer_relevancy=result.answer_relevancy,
            ndcg=result.ndcg,
            map_score=result.map_score,
            citation_precision=result.citation_precision,
            citation_recall=result.citation_recall,
            phantom_citation_count=result.phantom_citation_count,
            citation_support_score=result.citation_support_score,
            hallucination_rate=result.hallucination_rate,
            contradiction_count=result.contradiction_count,
            fabrication_count=result.fabrication_count,
            total_claims=result.total_claims,
            answer_completeness=result.answer_completeness,
        )
