"""Evaluation command and query handlers."""

import collections
import logging

from src import exceptions
from src.chunk.adapter import repository as chunk_repository_module
from src.chunk.domain import model as chunk_model
from src.document.adapter import repository as document_repository_module
from src.document.domain import status as document_status_module
from src.evaluation.adapter import generator as generator_module
from src.evaluation.adapter import judge as judge_module
from src.evaluation.adapter import repository as evaluation_repository_module
from src.evaluation.domain import metric as metric_module
from src.evaluation.domain import model
from src.evaluation.schema import command, response
from src.notebook.adapter import repository as notebook_repository_module
from src.query.adapter.pydantic_ai import agent as rag_agent_module
from src.query.service import retrieval

logger = logging.getLogger(__name__)


class GenerateDatasetHandler:
    """Handler for generating evaluation datasets."""

    def __init__(
        self,
        notebook_repository: notebook_repository_module.NotebookRepository,
        document_repository: document_repository_module.DocumentRepository,
        chunk_repository: chunk_repository_module.ChunkRepository,
        dataset_repository: evaluation_repository_module.DatasetRepository,
        test_generator: generator_module.SyntheticTestGenerator,
    ) -> None:
        self._notebook_repository = notebook_repository
        self._document_repository = document_repository
        self._chunk_repository = chunk_repository
        self._dataset_repository = dataset_repository
        self._test_generator = test_generator

    async def handle(
        self, notebook_id: str, cmd: command.GenerateDataset
    ) -> response.DatasetSummary:
        """Generate an evaluation dataset for a notebook."""
        await self._verify_notebook_exists(notebook_id)

        dataset = model.EvaluationDataset.create(
            notebook_id=notebook_id,
            name=cmd.name,
            questions_per_chunk=cmd.questions_per_chunk,
            max_chunks_sample=cmd.max_chunks_sample,
        )
        dataset = dataset.mark_generating()
        await self._dataset_repository.save(dataset)

        try:
            chunks = await self._collect_notebook_chunks(notebook_id)
            test_cases = await self._generate_test_cases(chunks, cmd)
            dataset = dataset.mark_completed(test_cases=tuple(test_cases))
            saved = await self._dataset_repository.save_with_test_cases(dataset)
            return response.DatasetSummary.from_entity(saved)

        except exceptions.ApplicationError:
            raise
        except Exception as exc:
            dataset = dataset.mark_failed(str(exc))
            await self._dataset_repository.save(dataset)
            raise exceptions.ExternalServiceError(
                f"Failed to generate dataset: {exc}"
            ) from exc

    async def _verify_notebook_exists(self, notebook_id: str) -> None:
        """Verify notebook exists or raise NotFoundError."""
        notebook = await self._notebook_repository.find_by_id(notebook_id)
        if notebook is None:
            raise exceptions.NotFoundError(f"Notebook not found: {notebook_id}")

    async def _collect_notebook_chunks(
        self, notebook_id: str
    ) -> list[chunk_model.Chunk]:
        """Collect all chunks from completed documents in a notebook."""
        documents = await self._document_repository.list_by_status(
            notebook_id, document_status_module.DocumentStatus.COMPLETED
        )
        if not documents:
            raise exceptions.ValidationError(
                "No completed documents found in notebook"
            )

        all_chunks = []
        for doc in documents:
            chunks = await self._chunk_repository.list_by_document(doc.id)
            all_chunks.extend(chunks)

        if not all_chunks:
            raise exceptions.ValidationError(
                "No chunks found in notebook documents"
            )
        return all_chunks

    async def _generate_test_cases(
        self, chunks: list[chunk_model.Chunk], cmd: command.GenerateDataset
    ) -> list[model.TestCase]:
        """Generate test cases from chunks using LLM."""
        test_cases = await self._test_generator.generate_test_cases(
            chunks=chunks,
            questions_per_chunk=cmd.questions_per_chunk,
            max_chunks_sample=cmd.max_chunks_sample,
        )
        if not test_cases:
            raise exceptions.ValidationError(
                "Failed to generate any test cases"
            )
        return test_cases


class RunEvaluationHandler:
    """Handler for running evaluations."""

    def __init__(
        self,
        dataset_repository: evaluation_repository_module.DatasetRepository,
        run_repository: evaluation_repository_module.RunRepository,
        retrieval_service: retrieval.RetrievalService,
        rag_agent: rag_agent_module.RAGAgent | None = None,
        llm_judge: judge_module.LLMJudge | None = None,
    ) -> None:
        self._dataset_repository = dataset_repository
        self._run_repository = run_repository
        self._retrieval_service = retrieval_service
        self._rag_agent = rag_agent
        self._llm_judge = llm_judge

    async def handle(
        self, dataset_id: str, cmd: command.RunEvaluation
    ) -> response.RunDetail:
        """Run evaluation against a dataset."""
        dataset = await self._load_runnable_dataset(dataset_id)

        run = model.EvaluationRun.create(
            dataset_id=dataset_id,
            k=cmd.k,
            evaluation_type=cmd.evaluation_type,
        )
        run = run.mark_running()
        await self._run_repository.save(run)

        try:
            generation_metrics = None
            if cmd.evaluation_type == model.EvaluationType.FULL_RAG:
                results, generation_metrics = await self._evaluate_full_rag(
                    dataset, cmd.k,
                )
            else:
                results = await self._evaluate_retrieval_only(dataset, cmd.k)

            retrieval_metrics = self._compute_aggregate_metrics(results, cmd.k)
            run = run.mark_completed(
                metrics=retrieval_metrics,
                results=tuple(results),
                generation_metrics=generation_metrics,
            )
            saved = await self._run_repository.save_with_results(run)
            return response.RunDetail.from_entity(saved)

        except exceptions.ApplicationError:
            raise
        except Exception as exc:
            run = run.mark_failed(str(exc))
            await self._run_repository.save(run)
            raise exceptions.ExternalServiceError(
                f"Failed to run evaluation: {exc}"
            ) from exc

    async def _load_runnable_dataset(
        self, dataset_id: str
    ) -> model.EvaluationDataset:
        """Load dataset and verify it is ready for evaluation."""
        dataset = await self._dataset_repository.find_by_id(dataset_id)
        if dataset is None:
            raise exceptions.NotFoundError(f"Dataset not found: {dataset_id}")
        if not dataset.status.is_runnable:
            raise exceptions.InvalidStateError(
                f"Dataset is not ready for evaluation (status: {dataset.status})"
            )
        return dataset

    async def _evaluate_retrieval_only(
        self, dataset: model.EvaluationDataset, k: int
    ) -> list[model.TestCaseResult]:
        """Evaluate each test case with retrieval only."""
        results: list[model.TestCaseResult] = []

        for test_case in dataset.test_cases:
            retrieved_chunks = await self._retrieval_service.retrieve(
                notebook_id=dataset.notebook_id,
                query=test_case.question,
                max_chunks=k,
            )
            result = self._build_retrieval_result(test_case, retrieved_chunks, k)
            results.append(result)

        return results

    async def _evaluate_full_rag(
        self, dataset: model.EvaluationDataset, k: int
    ) -> tuple[list[model.TestCaseResult], model.GenerationMetrics]:
        """Evaluate with full RAG pipeline including generation."""
        if not self._rag_agent or not self._llm_judge:
            raise exceptions.ValidationError(
                "RAGAgent and LLMJudge required for FULL_RAG evaluation"
            )

        results: list[model.TestCaseResult] = []
        faithfulness_scores: list[float] = []
        relevancy_scores: list[float] = []

        for test_case in dataset.test_cases:
            result, faithfulness, relevancy = await self._evaluate_single_rag(
                dataset.notebook_id, test_case, k,
            )
            results.append(result)
            faithfulness_scores.append(faithfulness)
            relevancy_scores.append(relevancy)

        mean_f, mean_r = metric_module.aggregate_generation_metrics(
            faithfulness_scores, relevancy_scores,
        )
        generation_metrics = model.GenerationMetrics(
            mean_faithfulness=mean_f,
            mean_answer_relevancy=mean_r,
        )
        return results, generation_metrics

    async def _evaluate_single_rag(
        self,
        notebook_id: str,
        test_case: model.TestCase,
        k: int,
    ) -> tuple[model.TestCaseResult, float, float]:
        """Evaluate a single test case with full RAG pipeline."""
        retrieved_chunks = await self._retrieval_service.retrieve(
            notebook_id=notebook_id,
            query=test_case.question,
            max_chunks=k,
        )

        answer_result = await self._rag_agent.answer(
            question=test_case.question,
            retrieved_chunks=retrieved_chunks,
        )

        context_chunks = [rc.chunk for rc in retrieved_chunks]
        faithfulness = await self._llm_judge.score_faithfulness(
            question=test_case.question,
            answer=answer_result.answer,
            context_chunks=context_chunks,
        )
        relevancy = await self._llm_judge.score_answer_relevancy(
            question=test_case.question,
            answer=answer_result.answer,
        )

        case_metrics = self._compute_case_metrics(
            test_case, retrieved_chunks, k,
        )
        generation_case_metrics = model.GenerationCaseMetrics(
            faithfulness=faithfulness,
            answer_relevancy=relevancy,
        )

        result = model.TestCaseResult.create(
            test_case_id=test_case.id,
            retrieved_chunk_ids=tuple(rc.chunk.id for rc in retrieved_chunks),
            retrieved_scores=tuple(rc.score for rc in retrieved_chunks),
            metrics=case_metrics,
            generation_metrics=generation_case_metrics,
            generated_answer=answer_result.answer,
        )
        return result, faithfulness, relevancy

    @staticmethod
    def _build_retrieval_result(
        test_case: model.TestCase,
        retrieved_chunks: list[retrieval.RetrievedChunk],
        k: int,
    ) -> model.TestCaseResult:
        """Build a retrieval-only test case result."""
        retrieved_ids = [rc.chunk.id for rc in retrieved_chunks]
        retrieved_scores = [rc.score for rc in retrieved_chunks]
        relevant_ids = set(test_case.ground_truth_chunk_ids)

        case_metrics = model.CaseMetrics(
            precision=metric_module.precision_at_k(retrieved_ids, relevant_ids, k),
            recall=metric_module.recall_at_k(retrieved_ids, relevant_ids, k),
            hit=metric_module.hit_at_k(retrieved_ids, relevant_ids, k),
            reciprocal_rank=metric_module.reciprocal_rank(retrieved_ids, relevant_ids, k),
            ndcg=metric_module.ndcg_at_k(retrieved_ids, relevant_ids, k),
            map_score=metric_module.average_precision_at_k(retrieved_ids, relevant_ids, k),
        )

        return model.TestCaseResult.create(
            test_case_id=test_case.id,
            retrieved_chunk_ids=tuple(retrieved_ids),
            retrieved_scores=tuple(retrieved_scores),
            metrics=case_metrics,
        )

    @staticmethod
    def _compute_case_metrics(
        test_case: model.TestCase,
        retrieved_chunks: list[retrieval.RetrievedChunk],
        k: int,
    ) -> model.CaseMetrics:
        """Compute retrieval metrics for a single test case."""
        retrieved_ids = [rc.chunk.id for rc in retrieved_chunks]
        relevant_ids = set(test_case.ground_truth_chunk_ids)

        return model.CaseMetrics(
            precision=metric_module.precision_at_k(retrieved_ids, relevant_ids, k),
            recall=metric_module.recall_at_k(retrieved_ids, relevant_ids, k),
            hit=metric_module.hit_at_k(retrieved_ids, relevant_ids, k),
            reciprocal_rank=metric_module.reciprocal_rank(retrieved_ids, relevant_ids, k),
            ndcg=metric_module.ndcg_at_k(retrieved_ids, relevant_ids, k),
            map_score=metric_module.average_precision_at_k(retrieved_ids, relevant_ids, k),
        )

    @staticmethod
    def _compute_aggregate_metrics(
        results: list[model.TestCaseResult], k: int
    ) -> model.RetrievalMetrics:
        """Compute aggregate metrics from individual test case results."""
        precisions = [r.precision for r in results]
        recalls = [r.recall for r in results]
        hits = [r.hit for r in results]
        reciprocal_ranks = [r.reciprocal_rank for r in results]

        mean_p, mean_r, hit_rate, mrr = metric_module.aggregate_metrics(
            precisions, recalls, hits, reciprocal_ranks
        )

        ndcg_values = [r.ndcg for r in results]
        map_values = [r.map_score for r in results]
        mean_ndcg = sum(ndcg_values) / len(ndcg_values) if ndcg_values else 0.0
        mean_map = sum(map_values) / len(map_values) if map_values else 0.0

        return model.RetrievalMetrics(
            precision_at_k=mean_p,
            recall_at_k=mean_r,
            hit_rate_at_k=hit_rate,
            mrr=mrr,
            k=k,
            ndcg_at_k=mean_ndcg,
            map_at_k=mean_map,
        )


class GetDatasetHandler:
    """Handler for getting dataset details."""

    def __init__(
        self, dataset_repository: evaluation_repository_module.DatasetRepository
    ) -> None:
        self._dataset_repository = dataset_repository

    async def handle(self, dataset_id: str) -> response.DatasetDetail:
        """Get dataset with test cases."""
        dataset = await self._dataset_repository.find_by_id(dataset_id)
        if dataset is None:
            raise exceptions.NotFoundError(f"Dataset not found: {dataset_id}")
        return response.DatasetDetail.from_entity(dataset)


class GetRunHandler:
    """Handler for getting run details."""

    def __init__(
        self,
        run_repository: evaluation_repository_module.RunRepository,
        dataset_repository: evaluation_repository_module.DatasetRepository,
    ) -> None:
        self._run_repository = run_repository
        self._dataset_repository = dataset_repository

    async def handle(self, run_id: str) -> response.RunDetail:
        """Get run with results and metrics."""
        run = await self._run_repository.find_by_id(run_id)
        if run is None:
            raise exceptions.NotFoundError(f"Run not found: {run_id}")

        base_response = response.RunDetail.from_entity(run)
        difficulty_metrics = await self._compute_difficulty_metrics(run)
        return base_response.model_copy(
            update={"metrics_by_difficulty": difficulty_metrics or None},
        )

    async def _compute_difficulty_metrics(
        self, run: model.EvaluationRun
    ) -> list[response.DifficultyMetrics]:
        """Compute per-difficulty metrics from run results."""
        dataset = await self._dataset_repository.find_by_id(run.dataset_id)
        if dataset is None:
            return []

        difficulty_map = {
            tc.id: tc.difficulty
            for tc in dataset.test_cases
            if tc.difficulty is not None
        }
        if not difficulty_map:
            return []

        return self._aggregate_by_difficulty(run.results, difficulty_map)

    @staticmethod
    def _aggregate_by_difficulty(
        results: tuple[model.TestCaseResult, ...],
        difficulty_map: dict[str, model.QuestionDifficulty],
    ) -> list[response.DifficultyMetrics]:
        """Group results by difficulty and compute aggregated metrics."""
        results_by_difficulty: dict[
            model.QuestionDifficulty, list[model.TestCaseResult]
        ] = collections.defaultdict(list)

        for result in results:
            difficulty = difficulty_map.get(result.test_case_id)
            if difficulty is not None:
                results_by_difficulty[difficulty].append(result)

        metrics_list: list[response.DifficultyMetrics] = []
        for difficulty, group in sorted(
            results_by_difficulty.items(), key=lambda x: x[0].value
        ):
            precisions = [r.precision for r in group]
            recalls = [r.recall for r in group]
            hits = [r.hit for r in group]
            reciprocal_ranks = [r.reciprocal_rank for r in group]
            mean_p, mean_r, hit_rate, mrr = metric_module.aggregate_metrics(
                precisions, recalls, hits, reciprocal_ranks,
            )
            metrics_list.append(response.DifficultyMetrics(
                difficulty=difficulty.value,
                test_case_count=len(group),
                precision_at_k=mean_p,
                recall_at_k=mean_r,
                hit_rate_at_k=hit_rate,
                mrr=mrr,
            ))
        return metrics_list


class CompareRunsHandler:
    """Handler for comparing multiple evaluation runs."""

    def __init__(
        self,
        run_repository: evaluation_repository_module.RunRepository,
        dataset_repository: evaluation_repository_module.DatasetRepository,
    ) -> None:
        self._run_repository = run_repository
        self._dataset_repository = dataset_repository

    async def handle(
        self, cmd: command.CompareRuns
    ) -> response.RunComparisonResponse:
        """Compare multiple evaluation runs."""
        runs = await self._load_and_validate_runs(cmd.run_ids)
        dataset = await self._load_dataset(runs[0].dataset_id)

        difficulty_map = {
            tc.id: tc.difficulty
            for tc in dataset.test_cases
            if tc.difficulty is not None
        }

        aggregate_metrics = [
            self._build_aggregate_metrics(run) for run in runs
        ]
        test_case_comparisons = self._build_test_case_comparisons(
            runs, dataset.test_cases, difficulty_map,
        )

        return response.RunComparisonResponse(
            dataset_id=runs[0].dataset_id,
            k=runs[0].k,
            run_count=len(runs),
            aggregate_metrics=aggregate_metrics,
            test_case_comparisons=test_case_comparisons,
        )

    async def _load_and_validate_runs(
        self, run_ids: list[str]
    ) -> list[model.EvaluationRun]:
        """Load runs and validate they can be compared."""
        runs = await self._run_repository.list_by_ids(run_ids)
        if len(runs) != len(run_ids):
            found_ids = {r.id for r in runs}
            missing = [rid for rid in run_ids if rid not in found_ids]
            raise exceptions.NotFoundError(
                f"Runs not found: {', '.join(missing)}"
            )

        dataset_ids = {r.dataset_id for r in runs}
        if len(dataset_ids) > 1:
            raise exceptions.ValidationError(
                "All runs must belong to the same dataset"
            )

        incomplete = [r.id for r in runs if r.status != model.RunStatus.COMPLETED]
        if incomplete:
            raise exceptions.ValidationError(
                f"All runs must be completed: {', '.join(incomplete)}"
            )

        k_values = {r.k for r in runs}
        if len(k_values) > 1:
            raise exceptions.ValidationError(
                "All runs must use the same k value"
            )

        return runs

    async def _load_dataset(
        self, dataset_id: str
    ) -> model.EvaluationDataset:
        """Load dataset for test case metadata."""
        dataset = await self._dataset_repository.find_by_id(dataset_id)
        if dataset is None:
            raise exceptions.NotFoundError(
                f"Dataset not found: {dataset_id}"
            )
        return dataset

    @staticmethod
    def _build_aggregate_metrics(
        run: model.EvaluationRun,
    ) -> response.RunComparisonMetrics:
        """Build aggregate metrics for a single run."""
        return response.RunComparisonMetrics(
            run_id=run.id,
            created_at=run.created_at,
            evaluation_type=run.evaluation_type.value,
            precision_at_k=run.precision_at_k or 0.0,
            recall_at_k=run.recall_at_k or 0.0,
            hit_rate_at_k=run.hit_rate_at_k or 0.0,
            mrr=run.mrr or 0.0,
            mean_faithfulness=run.mean_faithfulness,
            mean_answer_relevancy=run.mean_answer_relevancy,
        )

    @staticmethod
    def _build_test_case_comparisons(
        runs: list[model.EvaluationRun],
        test_cases: tuple[model.TestCase, ...],
        difficulty_map: dict[str, model.QuestionDifficulty],
    ) -> list[response.TestCaseComparison]:
        """Build per-test-case cross-run comparisons."""
        tc_map = {tc.id: tc for tc in test_cases}

        all_tc_ids: list[str] = []
        seen: set[str] = set()
        for run in runs:
            for result in run.results:
                if result.test_case_id not in seen:
                    all_tc_ids.append(result.test_case_id)
                    seen.add(result.test_case_id)

        comparisons: list[response.TestCaseComparison] = []
        for tc_id in all_tc_ids:
            tc = tc_map.get(tc_id)
            question = tc.question if tc else ""
            difficulty = difficulty_map.get(tc_id)

            entries: list[response.TestCaseComparisonEntry] = []
            for run in runs:
                result = next(
                    (r for r in run.results if r.test_case_id == tc_id),
                    None,
                )
                if result is not None:
                    entries.append(response.TestCaseComparisonEntry(
                        run_id=run.id,
                        precision=result.precision,
                        recall=result.recall,
                        hit=result.hit,
                        reciprocal_rank=result.reciprocal_rank,
                        faithfulness=result.faithfulness,
                        answer_relevancy=result.answer_relevancy,
                        generated_answer=result.generated_answer,
                    ))

            comparisons.append(response.TestCaseComparison(
                test_case_id=tc_id,
                question=question,
                difficulty=difficulty.value if difficulty else None,
                entries=entries,
            ))

        return comparisons


class ListDatasetsHandler:
    """Handler for listing datasets."""

    def __init__(
        self,
        notebook_repository: notebook_repository_module.NotebookRepository,
        dataset_repository: evaluation_repository_module.DatasetRepository,
    ) -> None:
        self._notebook_repository = notebook_repository
        self._dataset_repository = dataset_repository

    async def handle(
        self, notebook_id: str
    ) -> list[response.DatasetSummary]:
        """List datasets for a notebook."""
        notebook = await self._notebook_repository.find_by_id(notebook_id)
        if notebook is None:
            raise exceptions.NotFoundError(f"Notebook not found: {notebook_id}")

        datasets = await self._dataset_repository.list_by_notebook(notebook_id)
        return [response.DatasetSummary.from_entity(d) for d in datasets]
