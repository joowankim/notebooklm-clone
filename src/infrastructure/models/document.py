"""Document ORM schema."""

import datetime

import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class DocumentSchema(Base):
    """SQLAlchemy ORM model for documents."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(sqlalchemy.String(32), primary_key=True)
    notebook_id: Mapped[str] = mapped_column(
        sqlalchemy.String(32),
        sqlalchemy.ForeignKey("notebooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(sqlalchemy.Text, nullable=False)
    title: Mapped[str | None] = mapped_column(sqlalchemy.String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        sqlalchemy.String(20),
        nullable=False,
        default="pending",
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(sqlalchemy.Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(sqlalchemy.String(64), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
        onupdate=sqlalchemy.func.now(),
    )

    # Ensure unique URL per notebook
    __table_args__ = (
        sqlalchemy.UniqueConstraint("notebook_id", "url", name="uq_document_notebook_url"),
    )
