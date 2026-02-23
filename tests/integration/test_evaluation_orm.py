"""Integration tests for evaluation ORM v2 field round-trips."""

import pytest
import pytest_asyncio
import sqlalchemy
import sqlalchemy.ext.asyncio
import sqlalchemy.orm

from src.evaluation.domain import mapper, model
from src.infrastructure.models import evaluation as eval_schema
from src.infrastructure.models import notebook as notebook_schema

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest_asyncio.fixture(loop_scope="session")
async def notebook(
    integration_session: sqlalchemy.ext.asyncio.AsyncSession,
) -> notebook_schema.NotebookSchema:
    """Create a test notebook for FK constraints."""
    nb = notebook_schema.NotebookSchema(id="nb-001", name="Test Notebook")
    integration_session.add(nb)
    await integration_session.flush()
    return nb


async def _load_dataset(
    session: sqlalchemy.ext.asyncio.AsyncSession,
    dataset_id: str,
) -> eval_schema.EvaluationDatasetSchema | None:
    """Load dataset with eager-loaded test_cases (async-safe)."""
    stmt = (
        sqlalchemy.select(eval_schema.EvaluationDatasetSchema)
        .where(eval_schema.EvaluationDatasetSchema.id == dataset_id)
        .options(sqlalchemy.orm.selectinload(eval_schema.EvaluationDatasetSchema.test_cases))
        .execution_options(populate_existing=True)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _load_run(
    session: sqlalchemy.ext.asyncio.AsyncSession,
    run_id: str,
) -> eval_schema.EvaluationRunSchema | None:
    """Load run with eager-loaded results (async-safe)."""
    stmt = (
        sqlalchemy.select(eval_schema.EvaluationRunSchema)
        .where(eval_schema.EvaluationRunSchema.id == run_id)
        .options(sqlalchemy.orm.selectinload(eval_schema.EvaluationRunSchema.results))
        .execution_options(populate_existing=True)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def _make_dataset_entity(
    *,
    expand_ground_truth: bool = False,
    similarity_threshold: float | None = 0.85,
) -> model.EvaluationDataset:
    """Build a dataset domain entity with v2 fields."""
    now = model.datetime.datetime.now(model.datetime.timezone.utc)
    return model.EvaluationDataset(
        id="ds-001",
        notebook_id="nb-001",
        name="Test Dataset",
        status=model.DatasetStatus.COMPLETED,
        questions_per_chunk=2,
        max_chunks_sample=50,
        expand_ground_truth=expand_ground_truth,
        similarity_threshold=similarity_threshold,
        created_at=now,
        updated_at=now,
    )


def _make_run_entity(
    *,
    ndcg_at_k: float | None = None,
    map_at_k: float | None = None,
    generation_model: str | None = None,
    mean_citation_precision: float | None = None,
    mean_citation_recall: float | None = None,
    mean_hallucination_rate: float | None = None,
    mean_answer_completeness: float | None = None,
    total_input_tokens: int | None = None,
    total_output_tokens: int | None = None,
    estimated_cost_usd: float | None = None,
) -> model.EvaluationRun:
    """Build a run domain entity with v2 fields."""
    now = model.datetime.datetime.now(model.datetime.timezone.utc)
    return model.EvaluationRun(
        id="run-001",
        dataset_id="ds-001",
        status=model.RunStatus.COMPLETED,
        k=5,
        evaluation_type=model.EvaluationType.FULL_RAG,
        precision_at_k=0.8,
        recall_at_k=0.7,
        hit_rate_at_k=0.9,
        mrr=0.75,
        ndcg_at_k=ndcg_at_k,
        map_at_k=map_at_k,
        generation_model=generation_model,
        mean_faithfulness=0.85,
        mean_answer_relevancy=0.9,
        mean_citation_precision=mean_citation_precision,
        mean_citation_recall=mean_citation_recall,
        mean_hallucination_rate=mean_hallucination_rate,
        mean_answer_completeness=mean_answer_completeness,
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
        estimated_cost_usd=estimated_cost_usd,
        created_at=now,
        updated_at=now,
    )


def _make_result_entity(
    *,
    ndcg: float = 0.0,
    map_score: float = 0.0,
    citation_precision: float | None = None,
    citation_recall: float | None = None,
    phantom_citation_count: int | None = None,
    citation_support_score: float | None = None,
    hallucination_rate: float | None = None,
    contradiction_count: int | None = None,
    fabrication_count: int | None = None,
    total_claims: int | None = None,
    answer_completeness: float | None = None,
) -> model.TestCaseResult:
    """Build a result domain entity with v2 fields."""
    return model.TestCaseResult(
        id="res-001",
        test_case_id="tc-001",
        retrieved_chunk_ids=("chunk-1", "chunk-2"),
        retrieved_scores=(0.95, 0.80),
        precision=0.5,
        recall=0.5,
        hit=True,
        reciprocal_rank=1.0,
        ndcg=ndcg,
        map_score=map_score,
        generated_answer="Test answer",
        faithfulness=0.9,
        answer_relevancy=0.85,
        citation_precision=citation_precision,
        citation_recall=citation_recall,
        phantom_citation_count=phantom_citation_count,
        citation_support_score=citation_support_score,
        hallucination_rate=hallucination_rate,
        contradiction_count=contradiction_count,
        fabrication_count=fabrication_count,
        total_claims=total_claims,
        answer_completeness=answer_completeness,
    )


async def _insert_dataset_record(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> eval_schema.EvaluationDatasetSchema:
    """Insert a minimal dataset record for FK dependencies."""
    ds = eval_schema.EvaluationDatasetSchema(
        id="ds-001",
        notebook_id="nb-001",
        name="Test",
        status="completed",
        questions_per_chunk=2,
        max_chunks_sample=50,
    )
    session.add(ds)
    await session.flush()
    return ds


async def _insert_run_record(
    session: sqlalchemy.ext.asyncio.AsyncSession,
) -> eval_schema.EvaluationRunSchema:
    """Insert a minimal run record for FK dependencies."""
    run = eval_schema.EvaluationRunSchema(
        id="run-001",
        dataset_id="ds-001",
        status="completed",
        k=5,
        evaluation_type="full_rag",
        precision_at_k=0.8,
        recall_at_k=0.7,
        hit_rate_at_k=0.9,
        mrr=0.75,
        mean_faithfulness=0.85,
        mean_answer_relevancy=0.9,
    )
    session.add(run)
    await session.flush()
    return run


class TestDatasetV2RoundTrip:
    """Test dataset v2 fields persist and map correctly."""

    async def test_expand_ground_truth_persisted(
        self,
        integration_session: sqlalchemy.ext.asyncio.AsyncSession,
        notebook: notebook_schema.NotebookSchema,
    ) -> None:
        """Round-trip expand_ground_truth=True through DB."""
        # Arrange
        entity = _make_dataset_entity(expand_ground_truth=True)
        record = mapper.DatasetMapper.to_record(entity)

        # Act
        integration_session.add(record)
        await integration_session.flush()
        loaded = await _load_dataset(integration_session, "ds-001")
        assert loaded is not None
        result = mapper.DatasetMapper.to_entity(loaded)

        # Assert
        assert result.expand_ground_truth is True

    async def test_similarity_threshold_persisted(
        self,
        integration_session: sqlalchemy.ext.asyncio.AsyncSession,
        notebook: notebook_schema.NotebookSchema,
    ) -> None:
        """Round-trip similarity_threshold=0.92 through DB."""
        # Arrange
        entity = _make_dataset_entity(similarity_threshold=0.92)
        record = mapper.DatasetMapper.to_record(entity)

        # Act
        integration_session.add(record)
        await integration_session.flush()
        loaded = await _load_dataset(integration_session, "ds-001")
        assert loaded is not None
        result = mapper.DatasetMapper.to_entity(loaded)

        # Assert
        assert result.similarity_threshold == pytest.approx(0.92)

    async def test_default_expand_ground_truth_is_false(
        self,
        integration_session: sqlalchemy.ext.asyncio.AsyncSession,
        notebook: notebook_schema.NotebookSchema,
    ) -> None:
        """Insert record without setting expand_ground_truth; verify default is False."""
        # Arrange
        ds = eval_schema.EvaluationDatasetSchema(
            id="ds-002",
            notebook_id="nb-001",
            name="Default Test",
            status="completed",
            questions_per_chunk=2,
            max_chunks_sample=50,
        )

        # Act
        integration_session.add(ds)
        await integration_session.flush()
        loaded = await _load_dataset(integration_session, "ds-002")
        assert loaded is not None
        result = mapper.DatasetMapper.to_entity(loaded)

        # Assert
        assert result.expand_ground_truth is False

    async def test_default_similarity_threshold(
        self,
        integration_session: sqlalchemy.ext.asyncio.AsyncSession,
        notebook: notebook_schema.NotebookSchema,
    ) -> None:
        """Insert record without setting similarity_threshold; verify default is 0.85."""
        # Arrange
        ds = eval_schema.EvaluationDatasetSchema(
            id="ds-003",
            notebook_id="nb-001",
            name="Default Threshold Test",
            status="completed",
            questions_per_chunk=2,
            max_chunks_sample=50,
        )

        # Act
        integration_session.add(ds)
        await integration_session.flush()
        loaded = await _load_dataset(integration_session, "ds-003")
        assert loaded is not None
        result = mapper.DatasetMapper.to_entity(loaded)

        # Assert
        assert result.similarity_threshold == pytest.approx(0.85)


class TestRunV2RoundTrip:
    """Test run v2 fields persist and map correctly."""

    async def test_ndcg_map_fields_persisted(
        self,
        integration_session: sqlalchemy.ext.asyncio.AsyncSession,
        notebook: notebook_schema.NotebookSchema,
    ) -> None:
        """Round-trip ndcg_at_k and map_at_k through DB."""
        # Arrange
        await _insert_dataset_record(integration_session)
        entity = _make_run_entity(ndcg_at_k=0.82, map_at_k=0.78)
        record = mapper.RunMapper.to_record(entity)

        # Act
        integration_session.add(record)
        await integration_session.flush()
        loaded = await _load_run(integration_session, "run-001")
        assert loaded is not None
        result = mapper.RunMapper.to_entity(loaded)

        # Assert
        assert result.ndcg_at_k == pytest.approx(0.82)
        assert result.map_at_k == pytest.approx(0.78)

    async def test_generation_model_persisted(
        self,
        integration_session: sqlalchemy.ext.asyncio.AsyncSession,
        notebook: notebook_schema.NotebookSchema,
    ) -> None:
        """Round-trip generation_model through DB."""
        # Arrange
        await _insert_dataset_record(integration_session)
        entity = _make_run_entity(generation_model="gpt-4o-mini")
        record = mapper.RunMapper.to_record(entity)

        # Act
        integration_session.add(record)
        await integration_session.flush()
        loaded = await _load_run(integration_session, "run-001")
        assert loaded is not None
        result = mapper.RunMapper.to_entity(loaded)

        # Assert
        assert result.generation_model == "gpt-4o-mini"

    async def test_citation_metrics_persisted(
        self,
        integration_session: sqlalchemy.ext.asyncio.AsyncSession,
        notebook: notebook_schema.NotebookSchema,
    ) -> None:
        """Round-trip citation metrics through DB."""
        # Arrange
        await _insert_dataset_record(integration_session)
        entity = _make_run_entity(
            mean_citation_precision=0.91,
            mean_citation_recall=0.87,
        )
        record = mapper.RunMapper.to_record(entity)

        # Act
        integration_session.add(record)
        await integration_session.flush()
        loaded = await _load_run(integration_session, "run-001")
        assert loaded is not None
        result = mapper.RunMapper.to_entity(loaded)

        # Assert
        assert result.mean_citation_precision == pytest.approx(0.91)
        assert result.mean_citation_recall == pytest.approx(0.87)

    async def test_hallucination_metrics_persisted(
        self,
        integration_session: sqlalchemy.ext.asyncio.AsyncSession,
        notebook: notebook_schema.NotebookSchema,
    ) -> None:
        """Round-trip mean_hallucination_rate and mean_answer_completeness through DB."""
        # Arrange
        await _insert_dataset_record(integration_session)
        entity = _make_run_entity(
            mean_hallucination_rate=0.05,
            mean_answer_completeness=0.93,
        )
        record = mapper.RunMapper.to_record(entity)

        # Act
        integration_session.add(record)
        await integration_session.flush()
        loaded = await _load_run(integration_session, "run-001")
        assert loaded is not None
        result = mapper.RunMapper.to_entity(loaded)

        # Assert
        assert result.mean_hallucination_rate == pytest.approx(0.05)
        assert result.mean_answer_completeness == pytest.approx(0.93)

    async def test_cost_metrics_persisted(
        self,
        integration_session: sqlalchemy.ext.asyncio.AsyncSession,
        notebook: notebook_schema.NotebookSchema,
    ) -> None:
        """Round-trip cost/token metrics through DB."""
        # Arrange
        await _insert_dataset_record(integration_session)
        entity = _make_run_entity(
            total_input_tokens=15000,
            total_output_tokens=3200,
            estimated_cost_usd=0.0425,
        )
        record = mapper.RunMapper.to_record(entity)

        # Act
        integration_session.add(record)
        await integration_session.flush()
        loaded = await _load_run(integration_session, "run-001")
        assert loaded is not None
        result = mapper.RunMapper.to_entity(loaded)

        # Assert
        assert result.total_input_tokens == 15000
        assert result.total_output_tokens == 3200
        assert result.estimated_cost_usd == pytest.approx(0.0425)

    async def test_nullable_fields_default_to_none(
        self,
        integration_session: sqlalchemy.ext.asyncio.AsyncSession,
        notebook: notebook_schema.NotebookSchema,
    ) -> None:
        """Create run without v2 fields; verify they are None after round-trip."""
        # Arrange
        await _insert_dataset_record(integration_session)
        entity = _make_run_entity()
        record = mapper.RunMapper.to_record(entity)

        # Act
        integration_session.add(record)
        await integration_session.flush()
        loaded = await _load_run(integration_session, "run-001")
        assert loaded is not None
        result = mapper.RunMapper.to_entity(loaded)

        # Assert
        assert result.ndcg_at_k is None
        assert result.map_at_k is None
        assert result.generation_model is None
        assert result.mean_citation_precision is None
        assert result.mean_citation_recall is None
        assert result.mean_hallucination_rate is None
        assert result.mean_answer_completeness is None
        assert result.total_input_tokens is None
        assert result.total_output_tokens is None
        assert result.estimated_cost_usd is None


class TestResultV2RoundTrip:
    """Test result v2 fields persist and map correctly."""

    async def test_ndcg_map_score_persisted(
        self,
        integration_session: sqlalchemy.ext.asyncio.AsyncSession,
        notebook: notebook_schema.NotebookSchema,
    ) -> None:
        """Round-trip ndcg and map_score through DB."""
        # Arrange
        await _insert_dataset_record(integration_session)
        await _insert_run_record(integration_session)
        entity = _make_result_entity(ndcg=0.88, map_score=0.76)
        record = mapper.RunMapper.result_to_record(entity, run_id="run-001")

        # Act
        integration_session.add(record)
        await integration_session.flush()
        loaded = await _load_run(integration_session, "run-001")
        assert loaded is not None
        run_entity = mapper.RunMapper.to_entity(loaded)
        result = run_entity.results[0]

        # Assert
        assert result.ndcg == pytest.approx(0.88)
        assert result.map_score == pytest.approx(0.76)

    async def test_citation_fields_persisted(
        self,
        integration_session: sqlalchemy.ext.asyncio.AsyncSession,
        notebook: notebook_schema.NotebookSchema,
    ) -> None:
        """Round-trip citation fields through DB."""
        # Arrange
        await _insert_dataset_record(integration_session)
        await _insert_run_record(integration_session)
        entity = _make_result_entity(
            citation_precision=0.95,
            citation_recall=0.88,
            phantom_citation_count=2,
            citation_support_score=0.91,
        )
        record = mapper.RunMapper.result_to_record(entity, run_id="run-001")

        # Act
        integration_session.add(record)
        await integration_session.flush()
        loaded = await _load_run(integration_session, "run-001")
        assert loaded is not None
        run_entity = mapper.RunMapper.to_entity(loaded)
        result = run_entity.results[0]

        # Assert
        assert result.citation_precision == pytest.approx(0.95)
        assert result.citation_recall == pytest.approx(0.88)
        assert result.phantom_citation_count == 2
        assert result.citation_support_score == pytest.approx(0.91)

    async def test_hallucination_fields_persisted(
        self,
        integration_session: sqlalchemy.ext.asyncio.AsyncSession,
        notebook: notebook_schema.NotebookSchema,
    ) -> None:
        """Round-trip hallucination fields through DB."""
        # Arrange
        await _insert_dataset_record(integration_session)
        await _insert_run_record(integration_session)
        entity = _make_result_entity(
            hallucination_rate=0.08,
            contradiction_count=1,
            fabrication_count=3,
            total_claims=25,
        )
        record = mapper.RunMapper.result_to_record(entity, run_id="run-001")

        # Act
        integration_session.add(record)
        await integration_session.flush()
        loaded = await _load_run(integration_session, "run-001")
        assert loaded is not None
        run_entity = mapper.RunMapper.to_entity(loaded)
        result = run_entity.results[0]

        # Assert
        assert result.hallucination_rate == pytest.approx(0.08)
        assert result.contradiction_count == 1
        assert result.fabrication_count == 3
        assert result.total_claims == 25

    async def test_answer_completeness_persisted(
        self,
        integration_session: sqlalchemy.ext.asyncio.AsyncSession,
        notebook: notebook_schema.NotebookSchema,
    ) -> None:
        """Round-trip answer_completeness through DB."""
        # Arrange
        await _insert_dataset_record(integration_session)
        await _insert_run_record(integration_session)
        entity = _make_result_entity(answer_completeness=0.94)
        record = mapper.RunMapper.result_to_record(entity, run_id="run-001")

        # Act
        integration_session.add(record)
        await integration_session.flush()
        loaded = await _load_run(integration_session, "run-001")
        assert loaded is not None
        run_entity = mapper.RunMapper.to_entity(loaded)
        result = run_entity.results[0]

        # Assert
        assert result.answer_completeness == pytest.approx(0.94)

    async def test_default_ndcg_map_score_zero(
        self,
        integration_session: sqlalchemy.ext.asyncio.AsyncSession,
        notebook: notebook_schema.NotebookSchema,
    ) -> None:
        """Result without ndcg/map_score should default to 0.0."""
        # Arrange
        await _insert_dataset_record(integration_session)
        await _insert_run_record(integration_session)
        entity = _make_result_entity()  # defaults: ndcg=0.0, map_score=0.0
        record = mapper.RunMapper.result_to_record(entity, run_id="run-001")

        # Act
        integration_session.add(record)
        await integration_session.flush()
        loaded = await _load_run(integration_session, "run-001")
        assert loaded is not None
        run_entity = mapper.RunMapper.to_entity(loaded)
        result = run_entity.results[0]

        # Assert
        assert result.ndcg == pytest.approx(0.0)
        assert result.map_score == pytest.approx(0.0)

    async def test_nullable_citation_fields_default_to_none(
        self,
        integration_session: sqlalchemy.ext.asyncio.AsyncSession,
        notebook: notebook_schema.NotebookSchema,
    ) -> None:
        """Result without citation fields should have None values."""
        # Arrange
        await _insert_dataset_record(integration_session)
        await _insert_run_record(integration_session)
        entity = _make_result_entity()  # all citation fields default to None
        record = mapper.RunMapper.result_to_record(entity, run_id="run-001")

        # Act
        integration_session.add(record)
        await integration_session.flush()
        loaded = await _load_run(integration_session, "run-001")
        assert loaded is not None
        run_entity = mapper.RunMapper.to_entity(loaded)
        result = run_entity.results[0]

        # Assert
        assert result.citation_precision is None
        assert result.citation_recall is None
        assert result.phantom_citation_count is None
        assert result.citation_support_score is None
        assert result.hallucination_rate is None
        assert result.contradiction_count is None
        assert result.fabrication_count is None
        assert result.total_claims is None
        assert result.answer_completeness is None
