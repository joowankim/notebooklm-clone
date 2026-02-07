"""Evaluation command and query handlers."""

import logging

from src import exceptions
from src.chunk.adapter import repository as chunk_repository_module
from src.document.adapter import repository as document_repository_module
from src.document.domain import status as document_status_module
from src.evaluation.adapter import generator as generator_module
from src.evaluation.adapter import repository as evaluation_repository_module
from src.evaluation.domain import metric as metric_module
from src.evaluation.domain import model
from src.evaluation.schema import command, response
from src.notebook.adapter import repository as notebook_repository_module
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
        # Verify notebook exists
        notebook = await self._notebook_repository.find_by_id(notebook_id)
        if notebook is None:
            raise exceptions.NotFoundError(f"Notebook not found: {notebook_id}")

        # Create dataset
        dataset = model.EvaluationDataset.create(
            notebook_id=notebook_id,
            name=cmd.name,
            questions_per_chunk=cmd.questions_per_chunk,
            max_chunks_sample=cmd.max_chunks_sample,
        )
        dataset = dataset.mark_generating()
        await self._dataset_repository.save(dataset)

        try:
            # Collect chunks from completed documents
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

            # Generate test cases
            test_cases = await self._test_generator.generate_test_cases(
                chunks=all_chunks,
                questions_per_chunk=cmd.questions_per_chunk,
                max_chunks_sample=cmd.max_chunks_sample,
            )

            if not test_cases:
                raise exceptions.ValidationError(
                    "Failed to generate any test cases"
                )

            # Complete dataset
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


class RunEvaluationHandler:
    """Handler for running evaluations."""

    def __init__(
        self,
        dataset_repository: evaluation_repository_module.DatasetRepository,
        run_repository: evaluation_repository_module.RunRepository,
        retrieval_service: retrieval.RetrievalService,
    ) -> None:
        self._dataset_repository = dataset_repository
        self._run_repository = run_repository
        self._retrieval_service = retrieval_service

    async def handle(
        self, dataset_id: str, cmd: command.RunEvaluation
    ) -> response.RunDetail:
        """Run evaluation against a dataset."""
        # Load dataset
        dataset = await self._dataset_repository.find_by_id(dataset_id)
        if dataset is None:
            raise exceptions.NotFoundError(f"Dataset not found: {dataset_id}")

        if not dataset.status.is_runnable:
            raise exceptions.InvalidStateError(
                f"Dataset is not ready for evaluation (status: {dataset.status})"
            )

        # Create run
        run = model.EvaluationRun.create(dataset_id=dataset_id, k=cmd.k)
        run = run.mark_running()
        await self._run_repository.save(run)

        try:
            # Evaluate each test case
            precisions: list[float] = []
            recalls: list[float] = []
            hits: list[bool] = []
            reciprocal_ranks: list[float] = []
            results: list[model.TestCaseResult] = []

            for test_case in dataset.test_cases:
                # Retrieve chunks using the same pipeline as production
                retrieved_chunks = await self._retrieval_service.retrieve(
                    notebook_id=dataset.notebook_id,
                    query=test_case.question,
                    max_chunks=cmd.k,
                )

                retrieved_ids = [rc.chunk.id for rc in retrieved_chunks]
                retrieved_scores = [rc.score for rc in retrieved_chunks]
                relevant_ids = set(test_case.ground_truth_chunk_ids)

                # Calculate per-case metrics
                p = metric_module.precision_at_k(retrieved_ids, relevant_ids, cmd.k)
                r = metric_module.recall_at_k(retrieved_ids, relevant_ids, cmd.k)
                h = metric_module.hit_at_k(retrieved_ids, relevant_ids, cmd.k)
                rr = metric_module.reciprocal_rank(retrieved_ids, relevant_ids, cmd.k)

                precisions.append(p)
                recalls.append(r)
                hits.append(h)
                reciprocal_ranks.append(rr)

                result = model.TestCaseResult.create(
                    test_case_id=test_case.id,
                    retrieved_chunk_ids=tuple(retrieved_ids),
                    retrieved_scores=tuple(retrieved_scores),
                    precision=p,
                    recall=r,
                    hit=h,
                    reciprocal_rank=rr,
                )
                results.append(result)

            # Calculate aggregate metrics
            mean_p, mean_r, hit_rate, mrr = metric_module.aggregate_metrics(
                precisions, recalls, hits, reciprocal_ranks
            )

            metrics = model.RetrievalMetrics(
                precision_at_k=mean_p,
                recall_at_k=mean_r,
                hit_rate_at_k=hit_rate,
                mrr=mrr,
                k=cmd.k,
            )

            run = run.mark_completed(metrics=metrics, results=tuple(results))
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
        self, run_repository: evaluation_repository_module.RunRepository
    ) -> None:
        self._run_repository = run_repository

    async def handle(self, run_id: str) -> response.RunDetail:
        """Get run with results and metrics."""
        run = await self._run_repository.find_by_id(run_id)
        if run is None:
            raise exceptions.NotFoundError(f"Run not found: {run_id}")
        return response.RunDetail.from_entity(run)


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
