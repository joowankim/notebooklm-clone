"""Document ORM schema."""

import datetime

import sqlalchemy
import sqlalchemy.orm

from src import database as database_module


class DocumentSchema(database_module.Base):
    """SQLAlchemy ORM model for documents."""

    __tablename__ = "documents"

    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.String(32), primary_key=True)
    notebook_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32),
        sqlalchemy.ForeignKey("notebooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.Text, nullable=False)
    title: sqlalchemy.orm.Mapped[str | None] = sqlalchemy.orm.mapped_column(sqlalchemy.String(500), nullable=True)
    status: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(20),
        nullable=False,
        default="pending",
        index=True,
    )
    error_message: sqlalchemy.orm.Mapped[str | None] = sqlalchemy.orm.mapped_column(sqlalchemy.Text, nullable=True)
    content_hash: sqlalchemy.orm.Mapped[str | None] = sqlalchemy.orm.mapped_column(sqlalchemy.String(64), nullable=True)
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

    # Ensure unique URL per notebook
    __table_args__ = (
        sqlalchemy.UniqueConstraint("notebook_id", "url", name="uq_document_notebook_url"),
    )
