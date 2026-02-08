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
