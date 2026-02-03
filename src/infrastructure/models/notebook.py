"""Notebook ORM schema."""

import datetime

import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class NotebookSchema(Base):
    """SQLAlchemy ORM model for notebooks."""

    __tablename__ = "notebooks"

    id: Mapped[str] = mapped_column(sqlalchemy.String(32), primary_key=True)
    name: Mapped[str] = mapped_column(sqlalchemy.String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(sqlalchemy.Text, nullable=True)
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
