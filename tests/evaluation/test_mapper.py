"""Tests for evaluation domain mappers."""

import datetime
import json

from src.evaluation.domain import mapper
from src.evaluation.domain import model
from src.infrastructure.models import evaluation as evaluation_schema


class TestDatasetMapperTestCaseToRecord:
    """Tests for DatasetMapper.test_case_to_record with difficulty field."""

    def test_test_case_to_record_preserves_difficulty_value(self) -> None:
        # Arrange
        now = datetime.datetime.now(datetime.UTC)
        test_case = model.TestCase(
            id="tc1",
            question="What is AI?",
            ground_truth_chunk_ids=("chunk1", "chunk2"),
            source_chunk_id="chunk1",
            difficulty=model.QuestionDifficulty.ANALYTICAL,
            created_at=now,
        )

        # Act
        record = mapper.DatasetMapper.test_case_to_record(
            test_case=test_case,
            dataset_id="ds1",
        )

        # Assert
        expected = evaluation_schema.EvaluationTestCaseSchema(
            id="tc1",
            dataset_id="ds1",
            question="What is AI?",
            ground_truth_chunk_ids=json.dumps(["chunk1", "chunk2"]),
            source_chunk_id="chunk1",
            difficulty="analytical",
            created_at=now,
        )
        assert record.id == expected.id
        assert record.dataset_id == expected.dataset_id
        assert record.question == expected.question
        assert record.ground_truth_chunk_ids == expected.ground_truth_chunk_ids
        assert record.source_chunk_id == expected.source_chunk_id
        assert record.difficulty == expected.difficulty
        assert record.created_at == expected.created_at

    def test_test_case_to_record_handles_difficulty_none(self) -> None:
        # Arrange
        now = datetime.datetime.now(datetime.UTC)
        test_case = model.TestCase(
            id="tc2",
            question="What is ML?",
            ground_truth_chunk_ids=("chunk3",),
            source_chunk_id="chunk3",
            difficulty=None,
            created_at=now,
        )

        # Act
        record = mapper.DatasetMapper.test_case_to_record(
            test_case=test_case,
            dataset_id="ds1",
        )

        # Assert
        assert record.difficulty is None


class TestDatasetMapperToEntity:
    """Tests for DatasetMapper.to_entity with difficulty field."""

    def test_to_entity_preserves_difficulty_value_from_record(self) -> None:
        # Arrange
        now = datetime.datetime.now(datetime.UTC)
        dataset_record = evaluation_schema.EvaluationDatasetSchema(
            id="ds1",
            notebook_id="nb1",
            name="test-dataset",
            status="completed",
            questions_per_chunk=2,
            max_chunks_sample=50,
            error_message=None,
            created_at=now,
            updated_at=now,
        )
        test_case_record = evaluation_schema.EvaluationTestCaseSchema(
            id="tc1",
            dataset_id="ds1",
            question="How does AI work?",
            ground_truth_chunk_ids=json.dumps(["chunk1"]),
            source_chunk_id="chunk1",
            difficulty="inferential",
            created_at=now,
        )
        dataset_record.test_cases = [test_case_record]

        # Act
        entity = mapper.DatasetMapper.to_entity(dataset_record)

        # Assert
        assert len(entity.test_cases) == 1
        assert entity.test_cases[0].difficulty == model.QuestionDifficulty.INFERENTIAL

    def test_to_entity_handles_record_with_difficulty_none(self) -> None:
        # Arrange
        now = datetime.datetime.now(datetime.UTC)
        dataset_record = evaluation_schema.EvaluationDatasetSchema(
            id="ds2",
            notebook_id="nb1",
            name="test-dataset-2",
            status="completed",
            questions_per_chunk=2,
            max_chunks_sample=50,
            error_message=None,
            created_at=now,
            updated_at=now,
        )
        test_case_record = evaluation_schema.EvaluationTestCaseSchema(
            id="tc2",
            dataset_id="ds2",
            question="What is ML?",
            ground_truth_chunk_ids=json.dumps(["chunk2"]),
            source_chunk_id="chunk2",
            difficulty=None,
            created_at=now,
        )
        dataset_record.test_cases = [test_case_record]

        # Act
        entity = mapper.DatasetMapper.to_entity(dataset_record)

        # Assert
        assert len(entity.test_cases) == 1
        assert entity.test_cases[0].difficulty is None

    def test_to_entity_preserves_all_difficulty_types(self) -> None:
        # Arrange
        now = datetime.datetime.now(datetime.UTC)
        dataset_record = evaluation_schema.EvaluationDatasetSchema(
            id="ds3",
            notebook_id="nb1",
            name="test-dataset-3",
            status="completed",
            questions_per_chunk=2,
            max_chunks_sample=50,
            error_message=None,
            created_at=now,
            updated_at=now,
        )
        difficulties = ["factual", "analytical", "inferential", "paraphrased"]
        test_case_records = []
        for i, diff in enumerate(difficulties):
            tc = evaluation_schema.EvaluationTestCaseSchema(
                id=f"tc{i}",
                dataset_id="ds3",
                question=f"Question {i}",
                ground_truth_chunk_ids=json.dumps([f"chunk{i}"]),
                source_chunk_id=f"chunk{i}",
                difficulty=diff,
                created_at=now + datetime.timedelta(seconds=i),
            )
            test_case_records.append(tc)
        dataset_record.test_cases = test_case_records

        # Act
        entity = mapper.DatasetMapper.to_entity(dataset_record)

        # Assert
        expected_difficulties = [
            model.QuestionDifficulty.FACTUAL,
            model.QuestionDifficulty.ANALYTICAL,
            model.QuestionDifficulty.INFERENTIAL,
            model.QuestionDifficulty.PARAPHRASED,
        ]
        for tc, expected_diff in zip(entity.test_cases, expected_difficulties):
            assert tc.difficulty == expected_diff


class TestRunMapperToRecord:
    """Tests for RunMapper.to_record with generation fields."""

    def test_to_record_includes_evaluation_type(self) -> None:
        # Arrange
        now = datetime.datetime.now(datetime.UTC)
        entity = model.EvaluationRun(
            id="run1",
            dataset_id="ds1",
            status=model.RunStatus.PENDING,
            k=5,
            evaluation_type=model.EvaluationType.FULL_RAG,
            created_at=now,
            updated_at=now,
        )

        # Act
        record = mapper.RunMapper.to_record(entity)

        # Assert
        assert record.evaluation_type == "full_rag"

    def test_to_record_includes_mean_faithfulness_and_answer_relevancy(self) -> None:
        # Arrange
        now = datetime.datetime.now(datetime.UTC)
        entity = model.EvaluationRun(
            id="run2",
            dataset_id="ds1",
            status=model.RunStatus.COMPLETED,
            k=5,
            evaluation_type=model.EvaluationType.FULL_RAG,
            precision_at_k=0.8,
            recall_at_k=0.7,
            hit_rate_at_k=0.9,
            mrr=0.85,
            mean_faithfulness=0.92,
            mean_answer_relevancy=0.88,
            created_at=now,
            updated_at=now,
        )

        # Act
        record = mapper.RunMapper.to_record(entity)

        # Assert
        assert record.mean_faithfulness == 0.92
        assert record.mean_answer_relevancy == 0.88

    def test_to_record_defaults_evaluation_type_to_retrieval_only(self) -> None:
        # Arrange
        now = datetime.datetime.now(datetime.UTC)
        entity = model.EvaluationRun(
            id="run3",
            dataset_id="ds1",
            status=model.RunStatus.PENDING,
            k=5,
            created_at=now,
            updated_at=now,
        )

        # Act
        record = mapper.RunMapper.to_record(entity)

        # Assert
        assert record.evaluation_type == "retrieval_only"

    def test_to_record_handles_none_generation_metrics(self) -> None:
        # Arrange
        now = datetime.datetime.now(datetime.UTC)
        entity = model.EvaluationRun(
            id="run4",
            dataset_id="ds1",
            status=model.RunStatus.PENDING,
            k=5,
            evaluation_type=model.EvaluationType.RETRIEVAL_ONLY,
            created_at=now,
            updated_at=now,
        )

        # Act
        record = mapper.RunMapper.to_record(entity)

        # Assert
        assert record.mean_faithfulness is None
        assert record.mean_answer_relevancy is None


class TestRunMapperToEntity:
    """Tests for RunMapper.to_entity with generation fields."""

    def test_to_entity_parses_evaluation_type_enum(self) -> None:
        # Arrange
        now = datetime.datetime.now(datetime.UTC)
        record = evaluation_schema.EvaluationRunSchema(
            id="run1",
            dataset_id="ds1",
            status="pending",
            k=5,
            evaluation_type="full_rag",
            created_at=now,
            updated_at=now,
        )
        record.results = []

        # Act
        entity = mapper.RunMapper.to_entity(record)

        # Assert
        assert entity.evaluation_type == model.EvaluationType.FULL_RAG

    def test_to_entity_parses_mean_generation_metrics(self) -> None:
        # Arrange
        now = datetime.datetime.now(datetime.UTC)
        record = evaluation_schema.EvaluationRunSchema(
            id="run2",
            dataset_id="ds1",
            status="completed",
            k=5,
            evaluation_type="full_rag",
            precision_at_k=0.8,
            recall_at_k=0.7,
            hit_rate_at_k=0.9,
            mrr=0.85,
            mean_faithfulness=0.92,
            mean_answer_relevancy=0.88,
            created_at=now,
            updated_at=now,
        )
        record.results = []

        # Act
        entity = mapper.RunMapper.to_entity(record)

        # Assert
        assert entity.mean_faithfulness == 0.92
        assert entity.mean_answer_relevancy == 0.88

    def test_to_entity_handles_none_generation_metrics(self) -> None:
        # Arrange
        now = datetime.datetime.now(datetime.UTC)
        record = evaluation_schema.EvaluationRunSchema(
            id="run3",
            dataset_id="ds1",
            status="pending",
            k=5,
            evaluation_type="retrieval_only",
            mean_faithfulness=None,
            mean_answer_relevancy=None,
            created_at=now,
            updated_at=now,
        )
        record.results = []

        # Act
        entity = mapper.RunMapper.to_entity(record)

        # Assert
        assert entity.evaluation_type == model.EvaluationType.RETRIEVAL_ONLY
        assert entity.mean_faithfulness is None
        assert entity.mean_answer_relevancy is None

    def test_to_entity_parses_result_generation_fields(self) -> None:
        # Arrange
        now = datetime.datetime.now(datetime.UTC)
        record = evaluation_schema.EvaluationRunSchema(
            id="run4",
            dataset_id="ds1",
            status="completed",
            k=5,
            evaluation_type="full_rag",
            precision_at_k=0.8,
            recall_at_k=0.7,
            hit_rate_at_k=0.9,
            mrr=0.85,
            mean_faithfulness=0.92,
            mean_answer_relevancy=0.88,
            created_at=now,
            updated_at=now,
        )
        result_record = evaluation_schema.EvaluationTestCaseResultSchema(
            id="res1",
            run_id="run4",
            test_case_id="tc1",
            retrieved_chunk_ids=json.dumps(["c1", "c2"]),
            retrieved_scores=json.dumps([0.9, 0.8]),
            precision=0.5,
            recall=1.0,
            hit=True,
            reciprocal_rank=1.0,
            generated_answer="The answer is 42.",
            faithfulness=0.95,
            answer_relevancy=0.90,
        )
        record.results = [result_record]

        # Act
        entity = mapper.RunMapper.to_entity(record)

        # Assert
        assert len(entity.results) == 1
        result = entity.results[0]
        assert result.generated_answer == "The answer is 42."
        assert result.faithfulness == 0.95
        assert result.answer_relevancy == 0.90


class TestRunMapperResultToRecord:
    """Tests for RunMapper.result_to_record with generation fields."""

    def test_result_to_record_includes_generation_fields(self) -> None:
        # Arrange
        result = model.TestCaseResult(
            id="res1",
            test_case_id="tc1",
            retrieved_chunk_ids=("c1", "c2"),
            retrieved_scores=(0.9, 0.8),
            precision=0.5,
            recall=1.0,
            hit=True,
            reciprocal_rank=1.0,
            generated_answer="The answer is 42.",
            faithfulness=0.95,
            answer_relevancy=0.90,
        )

        # Act
        record = mapper.RunMapper.result_to_record(result=result, run_id="run1")

        # Assert
        assert record.generated_answer == "The answer is 42."
        assert record.faithfulness == 0.95
        assert record.answer_relevancy == 0.90

    def test_result_to_record_handles_none_generation_fields(self) -> None:
        # Arrange
        result = model.TestCaseResult(
            id="res2",
            test_case_id="tc2",
            retrieved_chunk_ids=("c3",),
            retrieved_scores=(0.7,),
            precision=1.0,
            recall=1.0,
            hit=True,
            reciprocal_rank=1.0,
            generated_answer=None,
            faithfulness=None,
            answer_relevancy=None,
        )

        # Act
        record = mapper.RunMapper.result_to_record(result=result, run_id="run1")

        # Assert
        assert record.generated_answer is None
        assert record.faithfulness is None
        assert record.answer_relevancy is None


class TestRunMapperRoundTrip:
    """Tests for RunMapper round-trip with generation metrics."""

    def test_full_rag_round_trip_preserves_all_fields(self) -> None:
        # Arrange
        now = datetime.datetime.now(datetime.UTC)
        original_entity = model.EvaluationRun(
            id="run_rt",
            dataset_id="ds_rt",
            status=model.RunStatus.COMPLETED,
            k=5,
            evaluation_type=model.EvaluationType.FULL_RAG,
            precision_at_k=0.8,
            recall_at_k=0.7,
            hit_rate_at_k=0.9,
            mrr=0.85,
            mean_faithfulness=0.92,
            mean_answer_relevancy=0.88,
            error_message=None,
            results=(
                model.TestCaseResult(
                    id="res_rt",
                    test_case_id="tc_rt",
                    retrieved_chunk_ids=("c1", "c2"),
                    retrieved_scores=(0.9, 0.8),
                    precision=0.5,
                    recall=1.0,
                    hit=True,
                    reciprocal_rank=1.0,
                    generated_answer="Generated response text.",
                    faithfulness=0.95,
                    answer_relevancy=0.90,
                ),
            ),
            created_at=now,
            updated_at=now,
        )

        # Act - Entity -> Record
        run_record = mapper.RunMapper.to_record(original_entity)
        result_records = [
            mapper.RunMapper.result_to_record(result=r, run_id=original_entity.id)
            for r in original_entity.results
        ]
        run_record.results = result_records

        # Act - Record -> Entity
        restored_entity = mapper.RunMapper.to_entity(run_record)

        # Assert
        assert restored_entity.id == original_entity.id
        assert restored_entity.dataset_id == original_entity.dataset_id
        assert restored_entity.status == original_entity.status
        assert restored_entity.k == original_entity.k
        assert restored_entity.evaluation_type == model.EvaluationType.FULL_RAG
        assert restored_entity.precision_at_k == original_entity.precision_at_k
        assert restored_entity.recall_at_k == original_entity.recall_at_k
        assert restored_entity.hit_rate_at_k == original_entity.hit_rate_at_k
        assert restored_entity.mrr == original_entity.mrr
        assert restored_entity.mean_faithfulness == original_entity.mean_faithfulness
        assert restored_entity.mean_answer_relevancy == original_entity.mean_answer_relevancy
        assert len(restored_entity.results) == 1
        restored_result = restored_entity.results[0]
        assert restored_result.generated_answer == "Generated response text."
        assert restored_result.faithfulness == 0.95
        assert restored_result.answer_relevancy == 0.90
