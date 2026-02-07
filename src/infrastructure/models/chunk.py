"""Chunk ORM schema with pgvector support."""

import datetime

import pgvector.sqlalchemy
import sqlalchemy
import sqlalchemy.orm

from src import database as database_module
from src import settings as settings_module


class ChunkSchema(database_module.Base):
    """SQLAlchemy ORM model for document chunks with vector embeddings."""

    __tablename__ = "chunks"

    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.String(32), primary_key=True)
    document_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32),
        sqlalchemy.ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.Text, nullable=False)
    char_start: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(sqlalchemy.Integer, nullable=False)
    char_end: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(sqlalchemy.Integer, nullable=False)
    chunk_index: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(sqlalchemy.Integer, nullable=False)
    token_count: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(sqlalchemy.Integer, nullable=False)
    embedding: sqlalchemy.orm.Mapped[list[float] | None] = sqlalchemy.orm.mapped_column(
        pgvector.sqlalchemy.Vector(settings_module.settings.embedding_dimensions),
        nullable=True,
    )
    created_at: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )

    # Index for vector similarity search
    __table_args__ = (
        sqlalchemy.Index(
            "ix_chunks_embedding_cosine",
            embedding,
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
