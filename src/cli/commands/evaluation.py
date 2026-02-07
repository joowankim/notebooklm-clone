"""Evaluation CLI commands."""

import asyncio

import rich.console
import rich.panel
import rich.table
import typer

from src import settings as settings_module
from src.chunk.adapter import repository as chunk_repository_module
from src.chunk.adapter.embedding import openai_embedding
from src.cli import utils as cli_utils
from src.document.adapter import repository as document_repository_module
from src.document.domain import status as document_status_module
from src.evaluation.adapter import generator as generator_module
from src.evaluation.adapter import repository as evaluation_repository_module
from src.evaluation.domain import metric as metric_module
from src.evaluation.domain import model
from src.notebook.adapter import repository as notebook_repository_module
from src.query.service import retrieval as retrieval_module

console = rich.console.Console()
app = typer.Typer()


@app.command("generate")
def generate_dataset(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
    name: str = typer.Option("default", "--name", "-n", help="Dataset name"),
    questions: int = typer.Option(2, "--questions", "-q", help="Questions per chunk"),
    max_chunks: int = typer.Option(50, "--max-chunks", "-m", help="Max chunks to sample"),
) -> None:
    """Generate an evaluation dataset from notebook chunks."""
    asyncio.run(_generate_dataset(notebook_id, name, questions, max_chunks))


async def _generate_dataset(
    notebook_id: str, name: str, questions: int, max_chunks: int
) -> None:
    async with cli_utils.get_session_context() as session:
        notebook_repo = notebook_repository_module.NotebookRepository(session)
        document_repo = document_repository_module.DocumentRepository(session)
        chunk_repo = chunk_repository_module.ChunkRepository(session)
        dataset_repo = evaluation_repository_module.DatasetRepository(session)
        test_gen = generator_module.SyntheticTestGenerator(
            eval_model=settings_module.settings.eval_model
        )

        # Verify notebook
        notebook = await notebook_repo.find_by_id(notebook_id)
        if notebook is None:
            console.print(f"[red]Notebook not found:[/red] {notebook_id}")
            raise typer.Exit(1)

        # Create dataset
        dataset = model.EvaluationDataset.create(
            notebook_id=notebook_id,
            name=name,
            questions_per_chunk=questions,
            max_chunks_sample=max_chunks,
        )
        dataset = dataset.mark_generating()
        await dataset_repo.save(dataset)

        console.print(f"[yellow]Generating dataset...[/yellow] (id: {dataset.id})")

        # Collect chunks
        documents = await document_repo.list_by_status(
            notebook_id, document_status_module.DocumentStatus.COMPLETED
        )
        if not documents:
            console.print("[red]No completed documents found in notebook.[/red]")
            raise typer.Exit(1)

        all_chunks = []
        for doc in documents:
            chunks = await chunk_repo.list_by_document(doc.id)
            all_chunks.extend(chunks)

        console.print(f"  Found {len(all_chunks)} chunks from {len(documents)} documents")

        # Generate test cases
        test_cases = await test_gen.generate_test_cases(
            chunks=all_chunks,
            questions_per_chunk=questions,
            max_chunks_sample=max_chunks,
        )

        if not test_cases:
            dataset = dataset.mark_failed("No test cases generated")
            await dataset_repo.save(dataset)
            await session.commit()
            console.print("[red]Failed to generate any test cases.[/red]")
            raise typer.Exit(1)

        dataset = dataset.mark_completed(test_cases=tuple(test_cases))
        await dataset_repo.save_with_test_cases(dataset)
        await session.commit()

        console.print(f"[green]Generated {len(test_cases)} test cases[/green]")
        console.print(f"  Dataset ID: {dataset.id}")


@app.command("list")
def list_datasets(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
) -> None:
    """List evaluation datasets for a notebook."""
    asyncio.run(_list_datasets(notebook_id))


async def _list_datasets(notebook_id: str) -> None:
    async with cli_utils.get_session_context() as session:
        dataset_repo = evaluation_repository_module.DatasetRepository(session)
        datasets = await dataset_repo.list_by_notebook(notebook_id)

        if not datasets:
            console.print("[yellow]No datasets found.[/yellow]")
            return

        table = rich.table.Table(title="Evaluation Datasets")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Status")
        table.add_column("Test Cases", justify="right")
        table.add_column("Created", style="dim")

        for ds in datasets:
            status_style = {
                "completed": "green",
                "failed": "red",
                "generating": "yellow",
                "pending": "dim",
            }.get(ds.status.value, "")

            table.add_row(
                ds.id,
                ds.name,
                f"[{status_style}]{ds.status.value}[/{status_style}]",
                str(len(ds.test_cases)),
                ds.created_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)


@app.command("run")
def run_evaluation(
    dataset_id: str = typer.Argument(..., help="Dataset ID"),
    k: int = typer.Option(5, "--k", "-k", help="Number of top results to evaluate"),
) -> None:
    """Run retrieval evaluation against a dataset."""
    asyncio.run(_run_evaluation(dataset_id, k))


async def _run_evaluation(dataset_id: str, k: int) -> None:
    async with cli_utils.get_session_context() as session:
        dataset_repo = evaluation_repository_module.DatasetRepository(session)
        run_repo = evaluation_repository_module.RunRepository(session)
        chunk_repo = chunk_repository_module.ChunkRepository(session)
        document_repo = document_repository_module.DocumentRepository(session)
        embedding_provider = openai_embedding.OpenAIEmbeddingProvider()
        retrieval_service = retrieval_module.RetrievalService(
            chunk_repository=chunk_repo,
            document_repository=document_repo,
            embedding_provider=embedding_provider,
        )

        # Load dataset
        dataset = await dataset_repo.find_by_id(dataset_id)
        if dataset is None:
            console.print(f"[red]Dataset not found:[/red] {dataset_id}")
            raise typer.Exit(1)

        if not dataset.status.is_runnable:
            console.print(f"[red]Dataset not ready (status: {dataset.status})[/red]")
            raise typer.Exit(1)

        console.print(f"[yellow]Running evaluation (k={k})...[/yellow]")
        console.print(f"  Dataset: {dataset.name} ({len(dataset.test_cases)} test cases)")

        # Create run
        run = model.EvaluationRun.create(dataset_id=dataset_id, k=k)
        run = run.mark_running()
        await run_repo.save(run)

        # Evaluate each test case
        precisions: list[float] = []
        recalls: list[float] = []
        hits: list[bool] = []
        reciprocal_ranks: list[float] = []
        results: list[model.TestCaseResult] = []

        for i, test_case in enumerate(dataset.test_cases, start=1):
            console.print(f"  Evaluating {i}/{len(dataset.test_cases)}...", end="\r")

            retrieved_chunks = await retrieval_service.retrieve(
                notebook_id=dataset.notebook_id,
                query=test_case.question,
                max_chunks=k,
            )

            retrieved_ids = [rc.chunk.id for rc in retrieved_chunks]
            retrieved_scores = [rc.score for rc in retrieved_chunks]
            relevant_ids = set(test_case.ground_truth_chunk_ids)

            p = metric_module.precision_at_k(retrieved_ids, relevant_ids, k)
            r = metric_module.recall_at_k(retrieved_ids, relevant_ids, k)
            h = metric_module.hit_at_k(retrieved_ids, relevant_ids, k)
            rr = metric_module.reciprocal_rank(retrieved_ids, relevant_ids, k)

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

        # Aggregate
        mean_p, mean_r, hit_rate, mrr = metric_module.aggregate_metrics(
            precisions, recalls, hits, reciprocal_ranks
        )

        metrics = model.RetrievalMetrics(
            precision_at_k=mean_p,
            recall_at_k=mean_r,
            hit_rate_at_k=hit_rate,
            mrr=mrr,
            k=k,
        )

        run = run.mark_completed(metrics=metrics, results=tuple(results))
        await run_repo.save_with_results(run)
        await session.commit()

        # Display results
        _print_metrics(metrics, run.id)


@app.command("results")
def show_results(
    run_id: str = typer.Argument(..., help="Run ID"),
) -> None:
    """Show evaluation results."""
    asyncio.run(_show_results(run_id))


async def _show_results(run_id: str) -> None:
    async with cli_utils.get_session_context() as session:
        run_repo = evaluation_repository_module.RunRepository(session)
        run = await run_repo.find_by_id(run_id)

        if run is None:
            console.print(f"[red]Run not found:[/red] {run_id}")
            raise typer.Exit(1)

        if run.status != model.RunStatus.COMPLETED:
            console.print(f"[red]Run not completed (status: {run.status})[/red]")
            if run.error_message:
                console.print(f"  Error: {run.error_message}")
            raise typer.Exit(1)

        metrics = model.RetrievalMetrics(
            precision_at_k=run.precision_at_k or 0.0,
            recall_at_k=run.recall_at_k or 0.0,
            hit_rate_at_k=run.hit_rate_at_k or 0.0,
            mrr=run.mrr or 0.0,
            k=run.k,
        )
        _print_metrics(metrics, run.id)


def _print_metrics(metrics: model.RetrievalMetrics, run_id: str) -> None:
    """Print metrics in a rich panel."""
    panel_content = (
        f"Precision@{metrics.k}:  {metrics.precision_at_k:.4f}\n"
        f"Recall@{metrics.k}:     {metrics.recall_at_k:.4f}\n"
        f"Hit Rate@{metrics.k}:   {metrics.hit_rate_at_k:.4f}\n"
        f"MRR:          {metrics.mrr:.4f}"
    )

    console.print()
    console.print(
        rich.panel.Panel(
            panel_content,
            title=f"Evaluation Results (k={metrics.k})",
            subtitle=f"Run: {run_id}",
            border_style="green",
        )
    )
