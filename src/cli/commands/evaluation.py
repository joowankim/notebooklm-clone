"""Evaluation CLI commands."""

import asyncio

import rich.console
import rich.panel
import rich.table
import typer

from src import exceptions as exceptions_module
from src import settings as settings_module
from src.chunk.adapter import repository as chunk_repository_module
from src.chunk.adapter.embedding import openai_embedding
from src.chunk.domain import model as chunk_model
from src.cli import utils as cli_utils
from src.document.adapter import repository as document_repository_module
from src.document.domain import status as document_status_module
from src.evaluation.adapter import generator as generator_module
from src.evaluation.adapter import judge as judge_module
from src.evaluation.adapter import repository as evaluation_repository_module
from src.evaluation.domain import model
from src.evaluation.handler import handlers as handlers_module
from src.evaluation.schema import command as command_module
from src.evaluation.schema import response as response_module
from src.notebook.adapter import repository as notebook_repository_module
from src.query.adapter.pydantic_ai import agent as rag_agent_module
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

        _verify_notebook_or_exit(await notebook_repo.find_by_id(notebook_id), notebook_id)

        dataset = model.EvaluationDataset.create(
            notebook_id=notebook_id,
            name=name,
            questions_per_chunk=questions,
            max_chunks_sample=max_chunks,
        )
        dataset = dataset.mark_generating()
        await dataset_repo.save(dataset)
        console.print(f"[yellow]Generating dataset...[/yellow] (id: {dataset.id})")

        all_chunks = await _collect_chunks(document_repo, chunk_repo, notebook_id)
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


def _verify_notebook_or_exit(notebook: object, notebook_id: str) -> None:
    """Exit with error if notebook is None."""
    if notebook is None:
        console.print(f"[red]Notebook not found:[/red] {notebook_id}")
        raise typer.Exit(1)


async def _collect_chunks(
    document_repo: document_repository_module.DocumentRepository,
    chunk_repo: chunk_repository_module.ChunkRepository,
    notebook_id: str,
) -> list[chunk_model.Chunk]:
    """Collect all chunks from completed documents in a notebook."""
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
    return all_chunks


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
    evaluation_type: str = typer.Option(
        "retrieval_only",
        "--type",
        "-t",
        help="Evaluation type: retrieval_only or full_rag",
    ),
) -> None:
    """Run retrieval evaluation against a dataset."""
    try:
        eval_type = model.EvaluationType(evaluation_type)
    except ValueError:
        console.print(f"[red]Invalid evaluation type: {evaluation_type}[/red]")
        console.print("  Valid types: retrieval_only, full_rag")
        raise typer.Exit(1)

    asyncio.run(_run_evaluation(dataset_id, k, eval_type))


async def _run_evaluation(
    dataset_id: str, k: int, eval_type: model.EvaluationType
) -> None:
    async with cli_utils.get_session_context() as session:
        dataset_repo = evaluation_repository_module.DatasetRepository(session)
        run_repo = evaluation_repository_module.RunRepository(session)
        retrieval_service = _build_retrieval_service(session)

        rag_agent = None
        llm_judge = None
        if eval_type == model.EvaluationType.FULL_RAG:
            rag_agent = rag_agent_module.RAGAgent()
            llm_judge = judge_module.LLMJudge(
                eval_model=settings_module.settings.eval_model,
            )

        handler = handlers_module.RunEvaluationHandler(
            dataset_repository=dataset_repo,
            run_repository=run_repo,
            retrieval_service=retrieval_service,
            rag_agent=rag_agent,
            llm_judge=llm_judge,
        )

        type_label = "Full RAG" if eval_type == model.EvaluationType.FULL_RAG else "Retrieval"
        console.print(f"[yellow]Running {type_label} evaluation (k={k})...[/yellow]")

        cmd = command_module.RunEvaluation(k=k, evaluation_type=eval_type)
        detail = await handler.handle(dataset_id, cmd)
        await session.commit()

        if detail.metrics is not None:
            metrics = model.RetrievalMetrics(
                precision_at_k=detail.metrics.precision_at_k,
                recall_at_k=detail.metrics.recall_at_k,
                hit_rate_at_k=detail.metrics.hit_rate_at_k,
                mrr=detail.metrics.mrr,
                k=detail.metrics.k,
            )
            _print_metrics(metrics, detail.id)

        _print_generation_metrics(detail)


def _build_retrieval_service(
    session: object,
) -> retrieval_module.RetrievalService:
    """Build retrieval service with required dependencies."""
    chunk_repo = chunk_repository_module.ChunkRepository(session)
    document_repo = document_repository_module.DocumentRepository(session)
    embedding_provider = openai_embedding.OpenAIEmbeddingProvider()
    return retrieval_module.RetrievalService(
        chunk_repository=chunk_repo,
        document_repository=document_repo,
        embedding_provider=embedding_provider,
    )


async def _load_runnable_dataset(
    dataset_repo: evaluation_repository_module.DatasetRepository,
    dataset_id: str,
) -> model.EvaluationDataset:
    """Load dataset and verify it is runnable, or exit."""
    dataset = await dataset_repo.find_by_id(dataset_id)
    if dataset is None:
        console.print(f"[red]Dataset not found:[/red] {dataset_id}")
        raise typer.Exit(1)
    if not dataset.status.is_runnable:
        console.print(f"[red]Dataset not ready (status: {dataset.status})[/red]")
        raise typer.Exit(1)
    return dataset


@app.command("results")
def show_results(
    run_id: str = typer.Argument(..., help="Run ID"),
) -> None:
    """Show evaluation results."""
    asyncio.run(_show_results(run_id))


async def _show_results(run_id: str) -> None:
    async with cli_utils.get_session_context() as session:
        run_repo = evaluation_repository_module.RunRepository(session)
        dataset_repo = evaluation_repository_module.DatasetRepository(session)
        handler = handlers_module.GetRunHandler(
            run_repository=run_repo,
            dataset_repository=dataset_repo,
        )

        try:
            detail = await handler.handle(run_id)
        except exceptions_module.NotFoundError:
            console.print(f"[red]Run not found:[/red] {run_id}")
            raise typer.Exit(1)

        if detail.status != model.RunStatus.COMPLETED.value:
            console.print(f"[red]Run not completed (status: {detail.status})[/red]")
            if detail.error_message:
                console.print(f"  Error: {detail.error_message}")
            raise typer.Exit(1)

        if detail.metrics is not None:
            metrics = model.RetrievalMetrics(
                precision_at_k=detail.metrics.precision_at_k,
                recall_at_k=detail.metrics.recall_at_k,
                hit_rate_at_k=detail.metrics.hit_rate_at_k,
                mrr=detail.metrics.mrr,
                k=detail.metrics.k,
            )
            _print_metrics(metrics, detail.id)

        _print_generation_metrics(detail)
        _print_difficulty_breakdown(detail)


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


def _print_generation_metrics(detail: response_module.RunDetail) -> None:
    """Print generation quality metrics if available."""
    if detail.mean_faithfulness is None:
        return

    panel_content = (
        f"Faithfulness:       {detail.mean_faithfulness:.4f}\n"
        f"Answer Relevancy:   {detail.mean_answer_relevancy or 0.0:.4f}"
    )

    console.print(
        rich.panel.Panel(
            panel_content,
            title="Generation Metrics",
            border_style="blue",
        )
    )


@app.command("compare")
def compare_runs(
    run_ids: list[str] = typer.Argument(
        ..., help="Run IDs to compare (2-10 runs)"
    ),
) -> None:
    """Compare multiple evaluation runs side-by-side."""
    if len(run_ids) < 2:
        console.print("[red]Must provide at least 2 run IDs[/red]")
        raise typer.Exit(1)
    if len(run_ids) > 10:
        console.print("[red]Cannot compare more than 10 runs[/red]")
        raise typer.Exit(1)

    asyncio.run(_compare_runs(run_ids))


async def _compare_runs(run_ids: list[str]) -> None:
    async with cli_utils.get_session_context() as session:
        run_repo = evaluation_repository_module.RunRepository(session)
        dataset_repo = evaluation_repository_module.DatasetRepository(session)

        handler = handlers_module.CompareRunsHandler(
            run_repository=run_repo,
            dataset_repository=dataset_repo,
        )

        cmd = command_module.CompareRuns(run_ids=run_ids)

        try:
            comparison = await handler.handle(cmd)
        except exceptions_module.NotFoundError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(1)
        except exceptions_module.ValidationError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(1)

        _print_comparison(comparison)


def _print_comparison(
    comparison: response_module.RunComparisonResponse,
) -> None:
    """Print run comparison results."""
    console.print(
        f"\n[bold]Dataset:[/bold] {comparison.dataset_id}"
        f"  [bold]k:[/bold] {comparison.k}"
        f"  [bold]Runs:[/bold] {comparison.run_count}"
    )

    agg_table = rich.table.Table(title="Aggregate Metrics Comparison")
    agg_table.add_column("Run ID", style="cyan")
    agg_table.add_column("Created", style="dim")
    agg_table.add_column("Type")
    agg_table.add_column("P@k", style="green")
    agg_table.add_column("R@k", style="green")
    agg_table.add_column("Hit@k", style="green")
    agg_table.add_column("MRR", style="green")
    agg_table.add_column("Faith.", style="blue")
    agg_table.add_column("Relev.", style="blue")

    for m in comparison.aggregate_metrics:
        agg_table.add_row(
            m.run_id[:8],
            m.created_at.strftime("%Y-%m-%d %H:%M"),
            m.evaluation_type,
            f"{m.precision_at_k:.4f}",
            f"{m.recall_at_k:.4f}",
            f"{m.hit_rate_at_k:.4f}",
            f"{m.mrr:.4f}",
            f"{m.mean_faithfulness:.4f}" if m.mean_faithfulness else "N/A",
            f"{m.mean_answer_relevancy:.4f}" if m.mean_answer_relevancy else "N/A",
        )

    console.print(agg_table)
    console.print(
        f"\n[bold]Test Cases Compared:[/bold] {len(comparison.test_case_comparisons)}"
    )


def _print_difficulty_breakdown(detail: response_module.RunDetail) -> None:
    """Print per-difficulty metrics table if available."""
    if not detail.metrics_by_difficulty:
        return

    diff_table = rich.table.Table(title="Metrics by Difficulty")
    diff_table.add_column("Difficulty")
    diff_table.add_column("Count")
    diff_table.add_column("Precision@k")
    diff_table.add_column("Recall@k")
    diff_table.add_column("Hit Rate@k")
    diff_table.add_column("MRR")

    for dm in detail.metrics_by_difficulty:
        diff_table.add_row(
            dm.difficulty.upper(),
            str(dm.test_case_count),
            f"{dm.precision_at_k:.4f}",
            f"{dm.recall_at_k:.4f}",
            f"{dm.hit_rate_at_k:.4f}",
            f"{dm.mrr:.4f}",
        )

    console.print(diff_table)
