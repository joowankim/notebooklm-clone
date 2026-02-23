"""Tests for evaluation handlers."""

import datetime
from unittest import mock

import pytest

from src import exceptions
from src.evaluation.adapter import repository as evaluation_repository_module
from src.evaluation.domain import model
from src.evaluation.handler import handlers
from src.evaluation.schema import command, response


def _make_test_case(
    test_case_id: str,
    difficulty: model.QuestionDifficulty | None = None,
) -> model.TestCase:
    """Create a test case with given id and difficulty."""
    return model.TestCase(
        id=test_case_id,
        question=f"Question for {test_case_id}",
        ground_truth_chunk_ids=("chunk1",),
        source_chunk_id="chunk1",
        difficulty=difficulty,
        created_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
    )


def _make_test_case_result(
    test_case_id: str,
    precision: float = 0.5,
    recall: float = 0.5,
    hit: bool = True,
    reciprocal_rank: float = 1.0,
) -> model.TestCaseResult:
    """Create a test case result with given metrics."""
    return model.TestCaseResult(
        id=f"result_{test_case_id}",
        test_case_id=test_case_id,
        retrieved_chunk_ids=("chunk1",),
        retrieved_scores=(0.9,),
        precision=precision,
        recall=recall,
        hit=hit,
        reciprocal_rank=reciprocal_rank,
    )


def _make_completed_run(
    dataset_id: str,
    results: tuple[model.TestCaseResult, ...],
) -> model.EvaluationRun:
    """Create a completed evaluation run."""
    return model.EvaluationRun(
        id="run-001",
        dataset_id=dataset_id,
        status=model.RunStatus.COMPLETED,
        k=5,
        precision_at_k=0.5,
        recall_at_k=0.5,
        hit_rate_at_k=1.0,
        mrr=1.0,
        results=results,
        created_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        updated_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
    )


def _make_dataset(
    dataset_id: str,
    test_cases: tuple[model.TestCase, ...],
) -> model.EvaluationDataset:
    """Create a completed dataset with test cases."""
    return model.EvaluationDataset(
        id=dataset_id,
        notebook_id="nb-001",
        name="test-dataset",
        status=model.DatasetStatus.COMPLETED,
        questions_per_chunk=2,
        max_chunks_sample=50,
        test_cases=test_cases,
        created_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        updated_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
    )


class TestGetRunHandler:
    """Tests for GetRunHandler."""

    @pytest.fixture()
    def run_repository(self) -> mock.AsyncMock:
        return mock.AsyncMock(spec=evaluation_repository_module.RunRepository)

    @pytest.fixture()
    def dataset_repository(self) -> mock.AsyncMock:
        return mock.AsyncMock(spec=evaluation_repository_module.DatasetRepository)

    @pytest.fixture()
    def handler(
        self,
        run_repository: mock.AsyncMock,
        dataset_repository: mock.AsyncMock,
    ) -> handlers.GetRunHandler:
        return handlers.GetRunHandler(
            run_repository=run_repository,
            dataset_repository=dataset_repository,
        )

    @pytest.mark.asyncio()
    async def test_handle_raises_not_found_when_run_missing(
        self,
        handler: handlers.GetRunHandler,
        run_repository: mock.AsyncMock,
    ) -> None:
        # Arrange
        run_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(exceptions.NotFoundError):
            await handler.handle("nonexistent-run")

    @pytest.mark.asyncio()
    async def test_handle_returns_run_detail_with_difficulty_metrics(
        self,
        handler: handlers.GetRunHandler,
        run_repository: mock.AsyncMock,
        dataset_repository: mock.AsyncMock,
    ) -> None:
        # Arrange
        tc_factual = _make_test_case("tc1", model.QuestionDifficulty.FACTUAL)
        tc_analytical = _make_test_case("tc2", model.QuestionDifficulty.ANALYTICAL)

        result_factual = _make_test_case_result(
            "tc1", precision=0.8, recall=1.0, hit=True, reciprocal_rank=1.0,
        )
        result_analytical = _make_test_case_result(
            "tc2", precision=0.4, recall=0.5, hit=True, reciprocal_rank=0.5,
        )

        dataset = _make_dataset("ds-001", (tc_factual, tc_analytical))
        run = _make_completed_run("ds-001", (result_factual, result_analytical))

        run_repository.find_by_id.return_value = run
        dataset_repository.find_by_id.return_value = dataset

        # Act
        detail = await handler.handle("run-001")

        # Assert
        assert detail.metrics_by_difficulty is not None
        assert len(detail.metrics_by_difficulty) == 2

        # Sorted alphabetically by difficulty value: analytical < factual
        analytical_metrics = detail.metrics_by_difficulty[0]
        assert analytical_metrics.difficulty == "analytical"
        assert analytical_metrics.test_case_count == 1
        assert analytical_metrics.precision_at_k == 0.4
        assert analytical_metrics.recall_at_k == 0.5
        assert analytical_metrics.hit_rate_at_k == 1.0
        assert analytical_metrics.mrr == 0.5

        factual_metrics = detail.metrics_by_difficulty[1]
        assert factual_metrics.difficulty == "factual"
        assert factual_metrics.test_case_count == 1
        assert factual_metrics.precision_at_k == 0.8
        assert factual_metrics.recall_at_k == 1.0
        assert factual_metrics.hit_rate_at_k == 1.0
        assert factual_metrics.mrr == 1.0

    @pytest.mark.asyncio()
    async def test_handle_returns_none_metrics_by_difficulty_when_no_difficulties(
        self,
        handler: handlers.GetRunHandler,
        run_repository: mock.AsyncMock,
        dataset_repository: mock.AsyncMock,
    ) -> None:
        # Arrange - test cases without difficulty
        tc_no_diff = _make_test_case("tc1", difficulty=None)
        result = _make_test_case_result("tc1")

        dataset = _make_dataset("ds-001", (tc_no_diff,))
        run = _make_completed_run("ds-001", (result,))

        run_repository.find_by_id.return_value = run
        dataset_repository.find_by_id.return_value = dataset

        # Act
        detail = await handler.handle("run-001")

        # Assert
        assert detail.metrics_by_difficulty is None

    @pytest.mark.asyncio()
    async def test_handle_groups_multiple_results_per_difficulty(
        self,
        handler: handlers.GetRunHandler,
        run_repository: mock.AsyncMock,
        dataset_repository: mock.AsyncMock,
    ) -> None:
        # Arrange - two factual test cases
        tc1 = _make_test_case("tc1", model.QuestionDifficulty.FACTUAL)
        tc2 = _make_test_case("tc2", model.QuestionDifficulty.FACTUAL)

        result1 = _make_test_case_result(
            "tc1", precision=0.6, recall=0.8, hit=True, reciprocal_rank=1.0,
        )
        result2 = _make_test_case_result(
            "tc2", precision=0.4, recall=0.6, hit=False, reciprocal_rank=0.0,
        )

        dataset = _make_dataset("ds-001", (tc1, tc2))
        run = _make_completed_run("ds-001", (result1, result2))

        run_repository.find_by_id.return_value = run
        dataset_repository.find_by_id.return_value = dataset

        # Act
        detail = await handler.handle("run-001")

        # Assert
        assert detail.metrics_by_difficulty is not None
        assert len(detail.metrics_by_difficulty) == 1

        factual = detail.metrics_by_difficulty[0]
        assert factual.difficulty == "factual"
        assert factual.test_case_count == 2
        assert factual.precision_at_k == pytest.approx(0.5)  # (0.6 + 0.4) / 2
        assert factual.recall_at_k == pytest.approx(0.7)  # (0.8 + 0.6) / 2
        assert factual.hit_rate_at_k == pytest.approx(0.5)  # 1 hit out of 2
        assert factual.mrr == pytest.approx(0.5)  # (1.0 + 0.0) / 2

    @pytest.mark.asyncio()
    async def test_handle_returns_none_metrics_when_dataset_not_found(
        self,
        handler: handlers.GetRunHandler,
        run_repository: mock.AsyncMock,
        dataset_repository: mock.AsyncMock,
    ) -> None:
        # Arrange
        result = _make_test_case_result("tc1")
        run = _make_completed_run("ds-001", (result,))

        run_repository.find_by_id.return_value = run
        dataset_repository.find_by_id.return_value = None

        # Act
        detail = await handler.handle("run-001")

        # Assert
        assert detail.metrics_by_difficulty is None

    @pytest.mark.asyncio()
    async def test_handle_sorts_difficulty_groups_by_enum_value(
        self,
        handler: handlers.GetRunHandler,
        run_repository: mock.AsyncMock,
        dataset_repository: mock.AsyncMock,
    ) -> None:
        # Arrange - add in reverse order to verify sorting
        tc_para = _make_test_case("tc1", model.QuestionDifficulty.PARAPHRASED)
        tc_fact = _make_test_case("tc2", model.QuestionDifficulty.FACTUAL)
        tc_infer = _make_test_case("tc3", model.QuestionDifficulty.INFERENTIAL)
        tc_anal = _make_test_case("tc4", model.QuestionDifficulty.ANALYTICAL)

        results = tuple(
            _make_test_case_result(f"tc{i}")
            for i in range(1, 5)
        )

        dataset = _make_dataset("ds-001", (tc_para, tc_fact, tc_infer, tc_anal))
        run = _make_completed_run("ds-001", results)

        run_repository.find_by_id.return_value = run
        dataset_repository.find_by_id.return_value = dataset

        # Act
        detail = await handler.handle("run-001")

        # Assert - sorted alphabetically by difficulty string value
        assert detail.metrics_by_difficulty is not None
        difficulties = [dm.difficulty for dm in detail.metrics_by_difficulty]
        assert difficulties == ["analytical", "factual", "inferential", "paraphrased"]


class TestRunEvaluationHandlerFullRag:
    """Tests for RunEvaluationHandler with FULL_RAG evaluation."""

    @pytest.fixture()
    def dataset_repository(self) -> mock.AsyncMock:
        return mock.AsyncMock(spec=evaluation_repository_module.DatasetRepository)

    @pytest.fixture()
    def run_repository(self) -> mock.AsyncMock:
        return mock.AsyncMock(spec=evaluation_repository_module.RunRepository)

    @pytest.fixture()
    def retrieval_service(self) -> mock.AsyncMock:
        return mock.AsyncMock()

    @pytest.fixture()
    def rag_agent(self) -> mock.AsyncMock:
        return mock.AsyncMock()

    @pytest.fixture()
    def llm_judge(self) -> mock.AsyncMock:
        return mock.AsyncMock()

    @pytest.fixture()
    def handler_full_rag(
        self,
        dataset_repository: mock.AsyncMock,
        run_repository: mock.AsyncMock,
        retrieval_service: mock.AsyncMock,
        rag_agent: mock.AsyncMock,
        llm_judge: mock.AsyncMock,
    ) -> handlers.RunEvaluationHandler:
        return handlers.RunEvaluationHandler(
            dataset_repository=dataset_repository,
            run_repository=run_repository,
            retrieval_service=retrieval_service,
            rag_agent=rag_agent,
            llm_judge=llm_judge,
        )

    @pytest.fixture()
    def handler_retrieval_only(
        self,
        dataset_repository: mock.AsyncMock,
        run_repository: mock.AsyncMock,
        retrieval_service: mock.AsyncMock,
    ) -> handlers.RunEvaluationHandler:
        return handlers.RunEvaluationHandler(
            dataset_repository=dataset_repository,
            run_repository=run_repository,
            retrieval_service=retrieval_service,
        )

    @staticmethod
    def _make_retrieved_chunk(chunk_id: str, score: float) -> mock.MagicMock:
        """Create a mock RetrievedChunk."""
        from src.chunk.domain import model as chunk_model

        chunk = chunk_model.Chunk(
            id=chunk_id,
            document_id="doc1",
            content="Some content.",
            char_start=0,
            char_end=13,
            chunk_index=0,
            token_count=3,
            created_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        )
        rc = mock.MagicMock()
        rc.chunk = chunk
        rc.score = score
        rc.document = mock.MagicMock()
        return rc

    @pytest.mark.asyncio()
    async def test_full_rag_evaluation_returns_generation_metrics(
        self,
        handler_full_rag: handlers.RunEvaluationHandler,
        dataset_repository: mock.AsyncMock,
        run_repository: mock.AsyncMock,
        retrieval_service: mock.AsyncMock,
        rag_agent: mock.AsyncMock,
        llm_judge: mock.AsyncMock,
    ) -> None:
        # Arrange
        from src.evaluation.schema import command

        tc = _make_test_case("tc1", model.QuestionDifficulty.FACTUAL)
        dataset = _make_dataset("ds-001", (tc,))
        dataset_repository.find_by_id.return_value = dataset

        rc = self._make_retrieved_chunk("chunk1", 0.95)
        retrieval_service.retrieve.return_value = [rc]

        answer_mock = mock.MagicMock()
        answer_mock.answer = "AI is artificial intelligence."
        rag_agent.answer.return_value = answer_mock

        llm_judge.score_faithfulness.return_value = 0.9
        llm_judge.score_answer_relevancy.return_value = 0.8

        run_repository.save.return_value = None
        run_repository.save_with_results.side_effect = lambda run: run

        cmd = command.RunEvaluation(
            k=5, evaluation_type=model.EvaluationType.FULL_RAG,
        )

        # Act
        detail = await handler_full_rag.handle("ds-001", cmd)

        # Assert
        assert detail.evaluation_type == "full_rag"
        assert detail.mean_faithfulness == 0.9
        assert detail.mean_answer_relevancy == 0.8
        assert len(detail.results) == 1
        assert detail.results[0].generated_answer == "AI is artificial intelligence."
        assert detail.results[0].faithfulness == 0.9
        assert detail.results[0].answer_relevancy == 0.8

    @pytest.mark.asyncio()
    async def test_retrieval_only_still_works_without_generation(
        self,
        handler_retrieval_only: handlers.RunEvaluationHandler,
        dataset_repository: mock.AsyncMock,
        run_repository: mock.AsyncMock,
        retrieval_service: mock.AsyncMock,
    ) -> None:
        # Arrange
        from src.evaluation.schema import command

        tc = _make_test_case("tc1")
        dataset = _make_dataset("ds-001", (tc,))
        dataset_repository.find_by_id.return_value = dataset

        rc = self._make_retrieved_chunk("chunk1", 0.95)
        retrieval_service.retrieve.return_value = [rc]

        run_repository.save.return_value = None
        run_repository.save_with_results.side_effect = lambda run: run

        cmd = command.RunEvaluation(k=5)

        # Act
        detail = await handler_retrieval_only.handle("ds-001", cmd)

        # Assert
        assert detail.evaluation_type == "retrieval_only"
        assert detail.mean_faithfulness is None
        assert detail.mean_answer_relevancy is None
        assert len(detail.results) == 1
        assert detail.results[0].generated_answer is None

    @pytest.mark.asyncio()
    async def test_full_rag_without_agents_raises_validation_error(
        self,
        handler_retrieval_only: handlers.RunEvaluationHandler,
        dataset_repository: mock.AsyncMock,
        run_repository: mock.AsyncMock,
    ) -> None:
        # Arrange
        from src.evaluation.schema import command

        tc = _make_test_case("tc1")
        dataset = _make_dataset("ds-001", (tc,))
        dataset_repository.find_by_id.return_value = dataset
        run_repository.save.return_value = None

        cmd = command.RunEvaluation(
            k=5, evaluation_type=model.EvaluationType.FULL_RAG,
        )

        # Act & Assert
        with pytest.raises(exceptions.ValidationError):
            await handler_retrieval_only.handle("ds-001", cmd)


class TestCompareRunsHandler:
    """Tests for CompareRunsHandler."""

    @pytest.fixture()
    def run_repository(self) -> mock.AsyncMock:
        return mock.AsyncMock(spec=evaluation_repository_module.RunRepository)

    @pytest.fixture()
    def dataset_repository(self) -> mock.AsyncMock:
        return mock.AsyncMock(spec=evaluation_repository_module.DatasetRepository)

    @pytest.fixture()
    def handler(
        self,
        run_repository: mock.AsyncMock,
        dataset_repository: mock.AsyncMock,
    ) -> handlers.CompareRunsHandler:
        return handlers.CompareRunsHandler(
            run_repository=run_repository,
            dataset_repository=dataset_repository,
        )

    @staticmethod
    def _make_run(
        run_id: str,
        dataset_id: str = "ds-001",
        k: int = 5,
        results: tuple[model.TestCaseResult, ...] = (),
        evaluation_type: model.EvaluationType = model.EvaluationType.RETRIEVAL_ONLY,
    ) -> model.EvaluationRun:
        return model.EvaluationRun(
            id=run_id,
            dataset_id=dataset_id,
            status=model.RunStatus.COMPLETED,
            k=k,
            evaluation_type=evaluation_type,
            precision_at_k=0.8,
            recall_at_k=0.7,
            hit_rate_at_k=0.9,
            mrr=0.85,
            results=results,
            created_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
            updated_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        )

    @pytest.mark.asyncio()
    async def test_handle_returns_comparison_response(
        self,
        handler: handlers.CompareRunsHandler,
        run_repository: mock.AsyncMock,
        dataset_repository: mock.AsyncMock,
    ) -> None:
        # Arrange
        tc = _make_test_case("tc1", model.QuestionDifficulty.FACTUAL)
        r1 = _make_test_case_result("tc1", precision=0.8)
        r2 = _make_test_case_result("tc1", precision=0.6)

        run1 = self._make_run("run1", results=(r1,))
        run2 = self._make_run("run2", results=(r2,))

        run_repository.list_by_ids.return_value = [run1, run2]
        dataset_repository.find_by_id.return_value = _make_dataset("ds-001", (tc,))

        cmd = command.CompareRuns(run_ids=["run1", "run2"])

        # Act
        result = await handler.handle(cmd)

        # Assert
        assert result.dataset_id == "ds-001"
        assert result.k == 5
        assert result.run_count == 2
        assert len(result.aggregate_metrics) == 2
        assert len(result.test_case_comparisons) == 1
        assert result.test_case_comparisons[0].difficulty == "factual"
        assert len(result.test_case_comparisons[0].entries) == 2

    @pytest.mark.asyncio()
    async def test_handle_raises_not_found_for_missing_runs(
        self,
        handler: handlers.CompareRunsHandler,
        run_repository: mock.AsyncMock,
    ) -> None:
        # Arrange
        run_repository.list_by_ids.return_value = [self._make_run("run1")]
        cmd = command.CompareRuns(run_ids=["run1", "run2"])

        # Act & Assert
        with pytest.raises(exceptions.NotFoundError):
            await handler.handle(cmd)

    @pytest.mark.asyncio()
    async def test_handle_raises_validation_for_different_datasets(
        self,
        handler: handlers.CompareRunsHandler,
        run_repository: mock.AsyncMock,
    ) -> None:
        # Arrange
        run1 = self._make_run("run1", dataset_id="ds-001")
        run2 = self._make_run("run2", dataset_id="ds-002")
        run_repository.list_by_ids.return_value = [run1, run2]

        cmd = command.CompareRuns(run_ids=["run1", "run2"])

        # Act & Assert
        with pytest.raises(exceptions.ValidationError):
            await handler.handle(cmd)

    @pytest.mark.asyncio()
    async def test_handle_raises_validation_for_incomplete_runs(
        self,
        handler: handlers.CompareRunsHandler,
        run_repository: mock.AsyncMock,
    ) -> None:
        # Arrange
        run1 = self._make_run("run1")
        run2 = model.EvaluationRun(
            id="run2",
            dataset_id="ds-001",
            status=model.RunStatus.RUNNING,
            k=5,
            created_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
            updated_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        )
        run_repository.list_by_ids.return_value = [run1, run2]

        cmd = command.CompareRuns(run_ids=["run1", "run2"])

        # Act & Assert
        with pytest.raises(exceptions.ValidationError):
            await handler.handle(cmd)

    @pytest.mark.asyncio()
    async def test_handle_raises_validation_for_different_k(
        self,
        handler: handlers.CompareRunsHandler,
        run_repository: mock.AsyncMock,
    ) -> None:
        # Arrange
        run1 = self._make_run("run1", k=5)
        run2 = self._make_run("run2", k=10)
        run_repository.list_by_ids.return_value = [run1, run2]

        cmd = command.CompareRuns(run_ids=["run1", "run2"])

        # Act & Assert
        with pytest.raises(exceptions.ValidationError):
            await handler.handle(cmd)

    @pytest.mark.asyncio()
    async def test_aggregate_metrics_include_generation_fields(
        self,
        handler: handlers.CompareRunsHandler,
        run_repository: mock.AsyncMock,
        dataset_repository: mock.AsyncMock,
    ) -> None:
        # Arrange
        tc = _make_test_case("tc1")
        r1 = _make_test_case_result("tc1")

        run1 = model.EvaluationRun(
            id="run1",
            dataset_id="ds-001",
            status=model.RunStatus.COMPLETED,
            k=5,
            evaluation_type=model.EvaluationType.FULL_RAG,
            precision_at_k=0.8,
            recall_at_k=0.7,
            hit_rate_at_k=0.9,
            mrr=0.85,
            mean_faithfulness=0.9,
            mean_answer_relevancy=0.8,
            results=(r1,),
            created_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
            updated_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        )
        run2 = self._make_run("run2", results=(r1,))

        run_repository.list_by_ids.return_value = [run1, run2]
        dataset_repository.find_by_id.return_value = _make_dataset("ds-001", (tc,))

        cmd = command.CompareRuns(run_ids=["run1", "run2"])

        # Act
        result = await handler.handle(cmd)

        # Assert
        assert result.aggregate_metrics[0].mean_faithfulness == 0.9
        assert result.aggregate_metrics[0].mean_answer_relevancy == 0.8
        assert result.aggregate_metrics[1].mean_faithfulness is None
