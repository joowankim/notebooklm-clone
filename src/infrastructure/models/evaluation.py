"""Evaluation ORM schemas."""

import datetime

import sqlalchemy
import sqlalchemy.orm

from src import database as database_module


class EvaluationDatasetSchema(database_module.Base):
    """SQLAlchemy ORM model for evaluation datasets."""

    __tablename__ = "evaluation_datasets"

    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32), primary_key=True
    )
    notebook_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32),
        sqlalchemy.ForeignKey("notebooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(255), nullable=False
    )
    status: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(20), nullable=False, default="pending", index=True
    )
    questions_per_chunk: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer, nullable=False, default=2
    )
    max_chunks_sample: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer, nullable=False, default=50
    )
    error_message: sqlalchemy.orm.Mapped[str | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Text, nullable=True
    )
    created_at: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )
    updated_at: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
        onupdate=sqlalchemy.func.now(),
    )

    test_cases: sqlalchemy.orm.Mapped[list["EvaluationTestCaseSchema"]] = sqlalchemy.orm.relationship(
        "EvaluationTestCaseSchema",
        back_populates="dataset",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class EvaluationTestCaseSchema(database_module.Base):
    """SQLAlchemy ORM model for evaluation test cases."""

    __tablename__ = "evaluation_test_cases"

    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32), primary_key=True
    )
    dataset_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32),
        sqlalchemy.ForeignKey("evaluation_datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Text, nullable=False
    )
    ground_truth_chunk_ids: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Text, nullable=False
    )
    source_chunk_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32), nullable=False
    )
    created_at: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )

    dataset: sqlalchemy.orm.Mapped["EvaluationDatasetSchema"] = sqlalchemy.orm.relationship(
        "EvaluationDatasetSchema",
        back_populates="test_cases",
    )


class EvaluationRunSchema(database_module.Base):
    """SQLAlchemy ORM model for evaluation runs."""

    __tablename__ = "evaluation_runs"

    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32), primary_key=True
    )
    dataset_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32),
        sqlalchemy.ForeignKey("evaluation_datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(20), nullable=False, default="pending"
    )
    k: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer, nullable=False, default=5
    )
    precision_at_k: sqlalchemy.orm.Mapped[float | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Float, nullable=True
    )
    recall_at_k: sqlalchemy.orm.Mapped[float | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Float, nullable=True
    )
    hit_rate_at_k: sqlalchemy.orm.Mapped[float | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Float, nullable=True
    )
    mrr: sqlalchemy.orm.Mapped[float | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Float, nullable=True
    )
    error_message: sqlalchemy.orm.Mapped[str | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Text, nullable=True
    )
    created_at: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )
    updated_at: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
        onupdate=sqlalchemy.func.now(),
    )

    results: sqlalchemy.orm.Mapped[list["EvaluationTestCaseResultSchema"]] = sqlalchemy.orm.relationship(
        "EvaluationTestCaseResultSchema",
        back_populates="run",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class EvaluationTestCaseResultSchema(database_module.Base):
    """SQLAlchemy ORM model for evaluation test case results."""

    __tablename__ = "evaluation_test_case_results"

    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32), primary_key=True
    )
    run_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32),
        sqlalchemy.ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_case_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32), nullable=False
    )
    retrieved_chunk_ids: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Text, nullable=False
    )
    retrieved_scores: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Text, nullable=False
    )
    precision: sqlalchemy.orm.Mapped[float] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Float, nullable=False
    )
    recall: sqlalchemy.orm.Mapped[float] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Float, nullable=False
    )
    hit: sqlalchemy.orm.Mapped[bool] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Boolean, nullable=False
    )
    reciprocal_rank: sqlalchemy.orm.Mapped[float] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Float, nullable=False
    )

    run: sqlalchemy.orm.Mapped["EvaluationRunSchema"] = sqlalchemy.orm.relationship(
        "EvaluationRunSchema",
        back_populates="results",
    )
