"""Chunk ORM schema with pgvector support."""

import datetime

import sqlalchemy
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.settings import settings


class ChunkSchema(Base):
    """SQLAlchemy ORM model for document chunks with vector embeddings."""

    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(sqlalchemy.String(32), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        sqlalchemy.String(32),
        sqlalchemy.ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(sqlalchemy.Text, nullable=False)
    char_start: Mapped[int] = mapped_column(sqlalchemy.Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(sqlalchemy.Integer, nullable=False)
    chunk_index: Mapped[int] = mapped_column(sqlalchemy.Integer, nullable=False)
    token_count: Mapped[int] = mapped_column(sqlalchemy.Integer, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.embedding_dimensions),
        nullable=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
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
