"""Evaluation REST API router."""

import http

import fastapi
from dependency_injector.wiring import Provide, inject

from src.dependency import container as container_module
from src.evaluation.handler import handlers
from src.evaluation.schema import command, response

router = fastapi.APIRouter(tags=["evaluation"])


@router.post(
    "/notebooks/{notebook_id}/evaluation/datasets",
    response_model=response.DatasetSummary,
    status_code=http.HTTPStatus.CREATED,
    summary="Generate evaluation dataset",
    description="Generate a synthetic evaluation dataset from notebook chunks using LLM.",
    responses={
        http.HTTPStatus.CREATED: {"description": "Dataset generation started"},
        http.HTTPStatus.NOT_FOUND: {"description": "Notebook not found"},
        http.HTTPStatus.BAD_REQUEST: {"description": "No chunks available"},
    },
)
@inject
async def generate_dataset(
    notebook_id: str,
    cmd: command.GenerateDataset,
    handler: handlers.GenerateDatasetHandler = fastapi.Depends(
        Provide[container_module.ApplicationContainer.evaluation.handler.generate_dataset_handler]
    ),
) -> response.DatasetSummary:
    """Generate an evaluation dataset for a notebook."""
    return await handler.handle(notebook_id, cmd)


@router.get(
    "/notebooks/{notebook_id}/evaluation/datasets",
    response_model=list[response.DatasetSummary],
    summary="List evaluation datasets",
    description="List all evaluation datasets for a notebook.",
    responses={
        http.HTTPStatus.OK: {"description": "Dataset list retrieved"},
        http.HTTPStatus.NOT_FOUND: {"description": "Notebook not found"},
    },
)
@inject
async def list_datasets(
    notebook_id: str,
    handler: handlers.ListDatasetsHandler = fastapi.Depends(
        Provide[container_module.ApplicationContainer.evaluation.handler.list_datasets_handler]
    ),
) -> list[response.DatasetSummary]:
    """List evaluation datasets for a notebook."""
    return await handler.handle(notebook_id)


@router.get(
    "/evaluation/datasets/{dataset_id}",
    response_model=response.DatasetDetail,
    summary="Get evaluation dataset",
    description="Get evaluation dataset details including test cases.",
    responses={
        http.HTTPStatus.OK: {"description": "Dataset retrieved"},
        http.HTTPStatus.NOT_FOUND: {"description": "Dataset not found"},
    },
)
@inject
async def get_dataset(
    dataset_id: str,
    handler: handlers.GetDatasetHandler = fastapi.Depends(
        Provide[container_module.ApplicationContainer.evaluation.handler.get_dataset_handler]
    ),
) -> response.DatasetDetail:
    """Get evaluation dataset details."""
    return await handler.handle(dataset_id)


@router.post(
    "/evaluation/datasets/{dataset_id}/runs",
    response_model=response.RunDetail,
    status_code=http.HTTPStatus.CREATED,
    summary="Run evaluation",
    description="Run retrieval evaluation against a dataset.",
    responses={
        http.HTTPStatus.CREATED: {"description": "Evaluation run completed"},
        http.HTTPStatus.NOT_FOUND: {"description": "Dataset not found"},
        http.HTTPStatus.CONFLICT: {"description": "Dataset not ready for evaluation"},
    },
)
@inject
async def run_evaluation(
    dataset_id: str,
    cmd: command.RunEvaluation,
    handler: handlers.RunEvaluationHandler = fastapi.Depends(
        Provide[container_module.ApplicationContainer.evaluation.handler.run_evaluation_handler]
    ),
) -> response.RunDetail:
    """Run evaluation against a dataset."""
    return await handler.handle(dataset_id, cmd)


@router.get(
    "/evaluation/runs/{run_id}",
    response_model=response.RunDetail,
    summary="Get evaluation run",
    description="Get evaluation run details including metrics and per-case results.",
    responses={
        http.HTTPStatus.OK: {"description": "Run retrieved"},
        http.HTTPStatus.NOT_FOUND: {"description": "Run not found"},
    },
)
@inject
async def get_run(
    run_id: str,
    handler: handlers.GetRunHandler = fastapi.Depends(
        Provide[container_module.ApplicationContainer.evaluation.handler.get_run_handler]
    ),
) -> response.RunDetail:
    """Get evaluation run details."""
    return await handler.handle(run_id)


@router.post(
    "/evaluation/compare",
    response_model=response.RunComparisonResponse,
    summary="Compare evaluation runs",
    description="Compare multiple evaluation runs from the same dataset side-by-side.",
    responses={
        http.HTTPStatus.OK: {"description": "Comparison result"},
        http.HTTPStatus.NOT_FOUND: {"description": "Run or dataset not found"},
        http.HTTPStatus.BAD_REQUEST: {"description": "Runs cannot be compared"},
    },
)
@inject
async def compare_runs(
    cmd: command.CompareRuns,
    handler: handlers.CompareRunsHandler = fastapi.Depends(
        Provide[container_module.ApplicationContainer.evaluation.handler.compare_runs_handler]
    ),
) -> response.RunComparisonResponse:
    """Compare multiple evaluation runs."""
    return await handler.handle(cmd)
