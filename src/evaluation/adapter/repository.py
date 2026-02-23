"""Evaluation repository implementations."""

import sqlalchemy
import sqlalchemy.ext.asyncio

from src.evaluation.domain import mapper as evaluation_mapper_module
from src.evaluation.domain import model
from src.infrastructure.models import evaluation as evaluation_schema


class DatasetRepository:
    """Repository for EvaluationDataset persistence."""

    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        self._session = session
        self._mapper = evaluation_mapper_module.DatasetMapper()

    async def find_by_id(self, dataset_id: str) -> model.EvaluationDataset | None:
        """Find dataset by ID."""
        stmt = sqlalchemy.select(evaluation_schema.EvaluationDatasetSchema).where(
            evaluation_schema.EvaluationDatasetSchema.id == dataset_id
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return self._mapper.to_entity(record)

    async def save(self, entity: model.EvaluationDataset) -> model.EvaluationDataset:
        """Save dataset (insert or update)."""
        record = self._mapper.to_record(entity)
        merged = await self._session.merge(record)
        await self._session.flush()
        return self._mapper.to_entity(merged)

    async def save_with_test_cases(
        self, entity: model.EvaluationDataset
    ) -> model.EvaluationDataset:
        """Save dataset with all test cases."""
        record = self._mapper.to_record(entity)
        await self._session.merge(record)
        await self._session.flush()

        for test_case in entity.test_cases:
            tc_record = self._mapper.test_case_to_record(test_case, entity.id)
            await self._session.merge(tc_record)
        await self._session.flush()

        # Re-fetch to get the full entity with test cases
        return await self.find_by_id(entity.id)  # type: ignore[return-value]

    async def list_by_notebook(
        self, notebook_id: str
    ) -> list[model.EvaluationDataset]:
        """List datasets for a notebook."""
        stmt = (
            sqlalchemy.select(evaluation_schema.EvaluationDatasetSchema)
            .where(evaluation_schema.EvaluationDatasetSchema.notebook_id == notebook_id)
            .order_by(evaluation_schema.EvaluationDatasetSchema.created_at.desc())
        )
        result = await self._session.execute(stmt)
        records = result.scalars().all()
        return [self._mapper.to_entity(record) for record in records]

    async def delete(self, dataset_id: str) -> bool:
        """Delete dataset by ID."""
        stmt = sqlalchemy.delete(evaluation_schema.EvaluationDatasetSchema).where(
            evaluation_schema.EvaluationDatasetSchema.id == dataset_id
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0


class RunRepository:
    """Repository for EvaluationRun persistence."""

    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        self._session = session
        self._mapper = evaluation_mapper_module.RunMapper()

    async def find_by_id(self, run_id: str) -> model.EvaluationRun | None:
        """Find run by ID."""
        stmt = sqlalchemy.select(evaluation_schema.EvaluationRunSchema).where(
            evaluation_schema.EvaluationRunSchema.id == run_id
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return self._mapper.to_entity(record)

    async def save(self, entity: model.EvaluationRun) -> model.EvaluationRun:
        """Save run (insert or update)."""
        record = self._mapper.to_record(entity)
        merged = await self._session.merge(record)
        await self._session.flush()
        return self._mapper.to_entity(merged)

    async def save_with_results(
        self, entity: model.EvaluationRun
    ) -> model.EvaluationRun:
        """Save run with all test case results."""
        record = self._mapper.to_record(entity)
        await self._session.merge(record)
        await self._session.flush()

        for result in entity.results:
            r_record = self._mapper.result_to_record(result, entity.id)
            await self._session.merge(r_record)
        await self._session.flush()

        # Re-fetch to get the full entity with results
        return await self.find_by_id(entity.id)  # type: ignore[return-value]

    async def list_by_dataset(
        self, dataset_id: str
    ) -> list[model.EvaluationRun]:
        """List runs for a dataset."""
        stmt = (
            sqlalchemy.select(evaluation_schema.EvaluationRunSchema)
            .where(evaluation_schema.EvaluationRunSchema.dataset_id == dataset_id)
            .order_by(evaluation_schema.EvaluationRunSchema.created_at.desc())
        )
        result = await self._session.execute(stmt)
        records = result.scalars().all()
        return [self._mapper.to_entity(record) for record in records]

    async def list_by_ids(
        self, run_ids: list[str]
    ) -> list[model.EvaluationRun]:
        """Find multiple runs by their IDs."""
        if not run_ids:
            return []
        stmt = (
            sqlalchemy.select(evaluation_schema.EvaluationRunSchema)
            .where(evaluation_schema.EvaluationRunSchema.id.in_(run_ids))
            .order_by(evaluation_schema.EvaluationRunSchema.created_at.asc())
        )
        result = await self._session.execute(stmt)
        records = result.scalars().all()
        return [self._mapper.to_entity(record) for record in records]
