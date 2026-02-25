"""Evaluation CLI commands."""

import asyncio

import rich.console
import rich.panel
import rich.table
import typer

from src import settings as settings_module
from src.cli import dependencies as deps
from src.cli import utils as cli_utils
from src.cli.error_handling import handle_domain_errors
from src.evaluation.adapter import judge as judge_module
from src.evaluation.domain import model
from src.evaluation.schema import command as command_module
from src.evaluation.schema import response as response_module

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


@handle_domain_errors
async def _generate_dataset(
    notebook_id: str, name: str, questions: int, max_chunks: int
) -> None:
    async with cli_utils.get_session_context() as session:
        handler = deps.build_generate_dataset_handler(session)
        cmd = command_module.GenerateDataset(
            name=name,
            questions_per_chunk=questions,
            max_chunks_sample=max_chunks,
        )

        console.print("[yellow]Generating dataset...[/yellow]")
        result = await handler.handle(notebook_id, cmd)
        await session.commit()

        console.print(f"[green]Generated {result.test_case_count} test cases[/green]")
        console.print(f"  Dataset ID: {result.id}")


@app.command("list")
def list_datasets(
    notebook_id: str = typer.Argument(..., help="Notebook ID"),
) -> None:
    """List evaluation datasets for a notebook."""
    asyncio.run(_list_datasets(notebook_id))


@handle_domain_errors
async def _list_datasets(notebook_id: str) -> None:
    async with cli_utils.get_session_context() as session:
        handler = deps.build_list_datasets_handler(session)
        datasets = await handler.handle(notebook_id)

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
            }.get(ds.status, "")

            table.add_row(
                ds.id,
                ds.name,
                f"[{status_style}]{ds.status}[/{status_style}]",
                str(ds.test_case_count),
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


@handle_domain_errors
async def _run_evaluation(
    dataset_id: str, k: int, eval_type: model.EvaluationType
) -> None:
    async with cli_utils.get_session_context() as session:
        rag_agent = None
        llm_judge = None
        if eval_type == model.EvaluationType.FULL_RAG:
            rag_agent = deps._build_rag_agent()
            llm_judge = judge_module.LLMJudge(
                eval_model=settings_module.settings.eval_model,
            )

        handler = deps.build_run_evaluation_handler(
            session, rag_agent=rag_agent, llm_judge=llm_judge,
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


@app.command("results")
def show_results(
    run_id: str = typer.Argument(..., help="Run ID"),
) -> None:
    """Show evaluation results."""
    asyncio.run(_show_results(run_id))


@handle_domain_errors
async def _show_results(run_id: str) -> None:
    async with cli_utils.get_session_context() as session:
        handler = deps.build_get_run_handler(session)
        detail = await handler.handle(run_id)

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


@handle_domain_errors
async def _compare_runs(run_ids: list[str]) -> None:
    async with cli_utils.get_session_context() as session:
        handler = deps.build_compare_runs_handler(session)
        cmd = command_module.CompareRuns(run_ids=run_ids)
        comparison = await handler.handle(cmd)
        _print_comparison(comparison)


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
