"""Tests for evaluation domain models."""

import pytest

from src.evaluation.domain import model


class TestDatasetStatus:
    """Tests for DatasetStatus enum."""

    def test_pending_is_generatable(self) -> None:
        assert model.DatasetStatus.PENDING.is_generatable is True

    def test_generating_is_not_generatable(self) -> None:
        assert model.DatasetStatus.GENERATING.is_generatable is False

    def test_completed_is_runnable(self) -> None:
        assert model.DatasetStatus.COMPLETED.is_runnable is True

    def test_pending_is_not_runnable(self) -> None:
        assert model.DatasetStatus.PENDING.is_runnable is False

    def test_failed_is_not_runnable(self) -> None:
        assert model.DatasetStatus.FAILED.is_runnable is False


class TestRunStatus:
    """Tests for RunStatus enum."""

    def test_pending_is_runnable(self) -> None:
        assert model.RunStatus.PENDING.is_runnable is True

    def test_running_is_not_runnable(self) -> None:
        assert model.RunStatus.RUNNING.is_runnable is False

    def test_completed_is_not_runnable(self) -> None:
        assert model.RunStatus.COMPLETED.is_runnable is False


class TestQuestionDifficulty:
    """Tests for QuestionDifficulty enum."""

    def test_factual_value(self) -> None:
        assert model.QuestionDifficulty.FACTUAL == "factual"

    def test_analytical_value(self) -> None:
        assert model.QuestionDifficulty.ANALYTICAL == "analytical"

    def test_inferential_value(self) -> None:
        assert model.QuestionDifficulty.INFERENTIAL == "inferential"

    def test_paraphrased_value(self) -> None:
        assert model.QuestionDifficulty.PARAPHRASED == "paraphrased"

    def test_is_str_enum(self) -> None:
        import enum

        assert issubclass(model.QuestionDifficulty, enum.StrEnum)

    def test_has_exactly_five_members(self) -> None:
        assert len(model.QuestionDifficulty) == 5


class TestTestCase:
    """Tests for TestCase entity."""

    def test_create_test_case(self) -> None:
        test_case = model.TestCase.create(
            question="What is AI?",
            ground_truth_chunk_ids=("chunk1", "chunk2"),
            source_chunk_id="chunk1",
        )

        assert test_case.id is not None
        assert len(test_case.id) == 32
        assert test_case.question == "What is AI?"
        assert test_case.ground_truth_chunk_ids == ("chunk1", "chunk2")
        assert test_case.source_chunk_id == "chunk1"
        assert test_case.created_at is not None

    def test_test_case_immutability(self) -> None:
        test_case = model.TestCase.create(
            question="test",
            ground_truth_chunk_ids=("c1",),
            source_chunk_id="c1",
        )
        with pytest.raises(Exception):
            test_case.question = "modified"

    def test_create_without_difficulty_defaults_to_none(self) -> None:
        test_case = model.TestCase.create(
            question="What is AI?",
            ground_truth_chunk_ids=("chunk1",),
            source_chunk_id="chunk1",
        )

        assert test_case.difficulty is None

    def test_create_with_factual_difficulty(self) -> None:
        test_case = model.TestCase.create(
            question="What is AI?",
            ground_truth_chunk_ids=("chunk1",),
            source_chunk_id="chunk1",
            difficulty=model.QuestionDifficulty.FACTUAL,
        )

        assert test_case.difficulty == model.QuestionDifficulty.FACTUAL

    def test_create_with_analytical_difficulty(self) -> None:
        test_case = model.TestCase.create(
            question="How does AI compare to ML?",
            ground_truth_chunk_ids=("chunk1",),
            source_chunk_id="chunk1",
            difficulty=model.QuestionDifficulty.ANALYTICAL,
        )

        assert test_case.difficulty == model.QuestionDifficulty.ANALYTICAL

    def test_create_with_inferential_difficulty(self) -> None:
        test_case = model.TestCase.create(
            question="What might happen if AI advances?",
            ground_truth_chunk_ids=("chunk1",),
            source_chunk_id="chunk1",
            difficulty=model.QuestionDifficulty.INFERENTIAL,
        )

        assert test_case.difficulty == model.QuestionDifficulty.INFERENTIAL

    def test_create_with_paraphrased_difficulty(self) -> None:
        test_case = model.TestCase.create(
            question="Explain artificial intelligence",
            ground_truth_chunk_ids=("chunk1",),
            source_chunk_id="chunk1",
            difficulty=model.QuestionDifficulty.PARAPHRASED,
        )

        assert test_case.difficulty == model.QuestionDifficulty.PARAPHRASED

    def test_immutability_with_difficulty_field(self) -> None:
        test_case = model.TestCase.create(
            question="test",
            ground_truth_chunk_ids=("c1",),
            source_chunk_id="c1",
            difficulty=model.QuestionDifficulty.FACTUAL,
        )
        with pytest.raises(Exception):
            test_case.difficulty = model.QuestionDifficulty.ANALYTICAL


class TestTestCaseResult:
    """Tests for TestCaseResult entity."""

    def test_create_test_case_result(self) -> None:
        case_metrics = model.CaseMetrics(
            precision=0.33,
            recall=1.0,
            hit=True,
            reciprocal_rank=1.0,
        )
        result = model.TestCaseResult.create(
            test_case_id="tc1",
            retrieved_chunk_ids=("c1", "c2", "c3"),
            retrieved_scores=(0.9, 0.8, 0.7),
            metrics=case_metrics,
        )

        assert result.id is not None
        assert len(result.id) == 32
        assert result.test_case_id == "tc1"
        assert result.retrieved_chunk_ids == ("c1", "c2", "c3")
        assert result.retrieved_scores == (0.9, 0.8, 0.7)
        assert result.precision == 0.33
        assert result.recall == 1.0
        assert result.hit is True
        assert result.reciprocal_rank == 1.0


class TestRetrievalMetrics:
    """Tests for RetrievalMetrics value object."""

    def test_create_metrics(self) -> None:
        metrics = model.RetrievalMetrics(
            precision_at_k=0.24,
            recall_at_k=0.80,
            hit_rate_at_k=0.80,
            mrr=0.65,
            k=5,
        )

        assert metrics.precision_at_k == 0.24
        assert metrics.recall_at_k == 0.80
        assert metrics.hit_rate_at_k == 0.80
        assert metrics.mrr == 0.65
        assert metrics.k == 5

    def test_metrics_immutability(self) -> None:
        metrics = model.RetrievalMetrics(
            precision_at_k=0.5, recall_at_k=0.5,
            hit_rate_at_k=0.5, mrr=0.5, k=5,
        )
        with pytest.raises(Exception):
            metrics.precision_at_k = 1.0


class TestEvaluationDataset:
    """Tests for EvaluationDataset entity."""

    def test_create_dataset(self) -> None:
        dataset = model.EvaluationDataset.create(
            notebook_id="nb1",
            name="baseline-v1",
            questions_per_chunk=3,
            max_chunks_sample=100,
        )

        assert dataset.id is not None
        assert len(dataset.id) == 32
        assert dataset.notebook_id == "nb1"
        assert dataset.name == "baseline-v1"
        assert dataset.status == model.DatasetStatus.PENDING
        assert dataset.questions_per_chunk == 3
        assert dataset.max_chunks_sample == 100
        assert dataset.test_cases == ()
        assert dataset.error_message is None

    def test_create_dataset_defaults(self) -> None:
        dataset = model.EvaluationDataset.create(
            notebook_id="nb1", name="test"
        )

        assert dataset.questions_per_chunk == 2
        assert dataset.max_chunks_sample == 50

    def test_mark_generating(self) -> None:
        dataset = model.EvaluationDataset.create(notebook_id="nb1", name="test")
        generating = dataset.mark_generating()

        assert generating.status == model.DatasetStatus.GENERATING
        assert dataset.status == model.DatasetStatus.PENDING  # immutability

    def test_mark_generating_invalid_state(self) -> None:
        dataset = model.EvaluationDataset.create(notebook_id="nb1", name="test")
        generating = dataset.mark_generating()

        with pytest.raises(Exception):
            generating.mark_generating()

    def test_mark_completed(self) -> None:
        dataset = model.EvaluationDataset.create(notebook_id="nb1", name="test")
        generating = dataset.mark_generating()

        test_case = model.TestCase.create(
            question="q1",
            ground_truth_chunk_ids=("c1",),
            source_chunk_id="c1",
        )
        completed = generating.mark_completed(test_cases=(test_case,))

        assert completed.status == model.DatasetStatus.COMPLETED
        assert len(completed.test_cases) == 1
        assert completed.test_cases[0].question == "q1"

    def test_mark_completed_invalid_state(self) -> None:
        dataset = model.EvaluationDataset.create(notebook_id="nb1", name="test")

        with pytest.raises(Exception):
            dataset.mark_completed(test_cases=())

    def test_mark_failed(self) -> None:
        dataset = model.EvaluationDataset.create(notebook_id="nb1", name="test")
        generating = dataset.mark_generating()
        failed = generating.mark_failed("LLM error")

        assert failed.status == model.DatasetStatus.FAILED
        assert failed.error_message == "LLM error"

    def test_dataset_immutability(self) -> None:
        dataset = model.EvaluationDataset.create(notebook_id="nb1", name="test")
        with pytest.raises(Exception):
            dataset.name = "modified"


class TestEvaluationRun:
    """Tests for EvaluationRun entity."""

    def test_create_run(self) -> None:
        run = model.EvaluationRun.create(dataset_id="ds1", k=10)

        assert run.id is not None
        assert len(run.id) == 32
        assert run.dataset_id == "ds1"
        assert run.status == model.RunStatus.PENDING
        assert run.k == 10
        assert run.precision_at_k is None
        assert run.results == ()

    def test_create_run_default_k(self) -> None:
        run = model.EvaluationRun.create(dataset_id="ds1")
        assert run.k == 5

    def test_mark_running(self) -> None:
        run = model.EvaluationRun.create(dataset_id="ds1")
        running = run.mark_running()

        assert running.status == model.RunStatus.RUNNING
        assert run.status == model.RunStatus.PENDING  # immutability

    def test_mark_running_invalid_state(self) -> None:
        run = model.EvaluationRun.create(dataset_id="ds1")
        running = run.mark_running()

        with pytest.raises(Exception):
            running.mark_running()

    def test_mark_completed(self) -> None:
        run = model.EvaluationRun.create(dataset_id="ds1", k=5)
        running = run.mark_running()

        metrics = model.RetrievalMetrics(
            precision_at_k=0.2,
            recall_at_k=0.8,
            hit_rate_at_k=0.8,
            mrr=0.65,
            k=5,
        )
        case_metrics = model.CaseMetrics(
            precision=0.2,
            recall=0.8,
            hit=True,
            reciprocal_rank=1.0,
        )
        result = model.TestCaseResult.create(
            test_case_id="tc1",
            retrieved_chunk_ids=("c1",),
            retrieved_scores=(0.9,),
            metrics=case_metrics,
        )
        completed = running.mark_completed(
            metrics=metrics, results=(result,)
        )

        assert completed.status == model.RunStatus.COMPLETED
        assert completed.precision_at_k == 0.2
        assert completed.recall_at_k == 0.8
        assert completed.hit_rate_at_k == 0.8
        assert completed.mrr == 0.65
        assert len(completed.results) == 1

    def test_mark_completed_invalid_state(self) -> None:
        run = model.EvaluationRun.create(dataset_id="ds1")
        metrics = model.RetrievalMetrics(
            precision_at_k=0.0, recall_at_k=0.0,
            hit_rate_at_k=0.0, mrr=0.0, k=5,
        )

        with pytest.raises(Exception):
            run.mark_completed(metrics=metrics, results=())

    def test_mark_failed(self) -> None:
        run = model.EvaluationRun.create(dataset_id="ds1")
        running = run.mark_running()
        failed = running.mark_failed("Retrieval error")

        assert failed.status == model.RunStatus.FAILED
        assert failed.error_message == "Retrieval error"

    def test_run_immutability(self) -> None:
        run = model.EvaluationRun.create(dataset_id="ds1")
        with pytest.raises(Exception):
            run.k = 10

    def test_create_run_with_evaluation_type(self) -> None:
        run = model.EvaluationRun.create(
            dataset_id="ds1",
            evaluation_type=model.EvaluationType.FULL_RAG,
        )

        assert run.evaluation_type == model.EvaluationType.FULL_RAG

    def test_create_run_default_evaluation_type_is_retrieval_only(self) -> None:
        run = model.EvaluationRun.create(dataset_id="ds1")

        assert run.evaluation_type == model.EvaluationType.RETRIEVAL_ONLY

    def test_mark_completed_with_generation_metrics(self) -> None:
        run = model.EvaluationRun.create(dataset_id="ds1", k=5)
        running = run.mark_running()

        retrieval_metrics = model.RetrievalMetrics(
            precision_at_k=0.2,
            recall_at_k=0.8,
            hit_rate_at_k=0.8,
            mrr=0.65,
            k=5,
        )
        generation_metrics = model.GenerationMetrics(
            mean_faithfulness=0.85,
            mean_answer_relevancy=0.90,
        )
        case_metrics = model.CaseMetrics(
            precision=0.2,
            recall=0.8,
            hit=True,
            reciprocal_rank=1.0,
        )
        result = model.TestCaseResult.create(
            test_case_id="tc1",
            retrieved_chunk_ids=("c1",),
            retrieved_scores=(0.9,),
            metrics=case_metrics,
        )
        completed = running.mark_completed(
            metrics=retrieval_metrics,
            results=(result,),
            generation_metrics=generation_metrics,
        )

        assert completed.mean_faithfulness == 0.85
        assert completed.mean_answer_relevancy == 0.90

    def test_mark_completed_without_generation_metrics_backward_compat(self) -> None:
        run = model.EvaluationRun.create(dataset_id="ds1", k=5)
        running = run.mark_running()

        retrieval_metrics = model.RetrievalMetrics(
            precision_at_k=0.2,
            recall_at_k=0.8,
            hit_rate_at_k=0.8,
            mrr=0.65,
            k=5,
        )
        case_metrics = model.CaseMetrics(
            precision=0.2,
            recall=0.8,
            hit=True,
            reciprocal_rank=1.0,
        )
        result = model.TestCaseResult.create(
            test_case_id="tc1",
            retrieved_chunk_ids=("c1",),
            retrieved_scores=(0.9,),
            metrics=case_metrics,
        )
        completed = running.mark_completed(
            metrics=retrieval_metrics,
            results=(result,),
        )

        assert completed.mean_faithfulness is None
        assert completed.mean_answer_relevancy is None


class TestEvaluationType:
    """Tests for EvaluationType enum."""

    def test_retrieval_only_value(self) -> None:
        assert model.EvaluationType.RETRIEVAL_ONLY == "retrieval_only"

    def test_full_rag_value(self) -> None:
        assert model.EvaluationType.FULL_RAG == "full_rag"

    def test_is_str_enum(self) -> None:
        import enum

        assert issubclass(model.EvaluationType, enum.StrEnum)

    def test_has_exactly_two_members(self) -> None:
        assert len(model.EvaluationType) == 2


class TestGenerationCaseMetrics:
    """Tests for GenerationCaseMetrics value object."""

    def test_create_generation_case_metrics(self) -> None:
        metrics = model.GenerationCaseMetrics(
            faithfulness=0.85,
            answer_relevancy=0.90,
        )

        assert metrics.faithfulness == 0.85
        assert metrics.answer_relevancy == 0.90

    def test_immutability(self) -> None:
        metrics = model.GenerationCaseMetrics(
            faithfulness=0.85,
            answer_relevancy=0.90,
        )
        with pytest.raises(Exception):
            metrics.faithfulness = 0.5

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(Exception):
            model.GenerationCaseMetrics(
                faithfulness=0.85,
                answer_relevancy=0.90,
                extra_field=0.5,
            )


class TestGenerationMetrics:
    """Tests for GenerationMetrics value object."""

    def test_create_generation_metrics(self) -> None:
        metrics = model.GenerationMetrics(
            mean_faithfulness=0.85,
            mean_answer_relevancy=0.90,
        )

        assert metrics.mean_faithfulness == 0.85
        assert metrics.mean_answer_relevancy == 0.90

    def test_immutability(self) -> None:
        metrics = model.GenerationMetrics(
            mean_faithfulness=0.85,
            mean_answer_relevancy=0.90,
        )
        with pytest.raises(Exception):
            metrics.mean_faithfulness = 0.5


class TestTestCaseResultGeneration:
    """Tests for TestCaseResult generation fields."""

    def test_create_with_generation_metrics(self) -> None:
        case_metrics = model.CaseMetrics(
            precision=0.33,
            recall=1.0,
            hit=True,
            reciprocal_rank=1.0,
        )
        generation_metrics = model.GenerationCaseMetrics(
            faithfulness=0.85,
            answer_relevancy=0.90,
        )
        result = model.TestCaseResult.create(
            test_case_id="tc1",
            retrieved_chunk_ids=("c1", "c2", "c3"),
            retrieved_scores=(0.9, 0.8, 0.7),
            metrics=case_metrics,
            generation_metrics=generation_metrics,
            generated_answer="AI is artificial intelligence.",
        )

        assert result.faithfulness == 0.85
        assert result.answer_relevancy == 0.90
        assert result.generated_answer == "AI is artificial intelligence."

    def test_create_without_generation_metrics_backward_compat(self) -> None:
        case_metrics = model.CaseMetrics(
            precision=0.33,
            recall=1.0,
            hit=True,
            reciprocal_rank=1.0,
        )
        result = model.TestCaseResult.create(
            test_case_id="tc1",
            retrieved_chunk_ids=("c1",),
            retrieved_scores=(0.9,),
            metrics=case_metrics,
        )

        assert result.faithfulness is None
        assert result.answer_relevancy is None
        assert result.generated_answer is None

    def test_generation_fields_are_none_by_default(self) -> None:
        case_metrics = model.CaseMetrics(
            precision=0.5,
            recall=0.5,
            hit=True,
            reciprocal_rank=0.5,
        )
        result = model.TestCaseResult.create(
            test_case_id="tc1",
            retrieved_chunk_ids=("c1",),
            retrieved_scores=(0.9,),
            metrics=case_metrics,
        )

        assert result.generated_answer is None
        assert result.faithfulness is None
        assert result.answer_relevancy is None
