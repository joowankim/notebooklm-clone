"""Conversation ORM schema."""

import datetime

import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class ConversationSchema(Base):
    """SQLAlchemy ORM model for conversations."""

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(sqlalchemy.String(32), primary_key=True)
    notebook_id: Mapped[str] = mapped_column(
        sqlalchemy.String(32),
        sqlalchemy.ForeignKey("notebooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(sqlalchemy.String(255), nullable=True)
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

    messages: Mapped[list["MessageSchema"]] = relationship(
        "MessageSchema",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class MessageSchema(Base):
    """SQLAlchemy ORM model for messages."""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(sqlalchemy.String(32), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        sqlalchemy.String(32),
        sqlalchemy.ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(sqlalchemy.String(20), nullable=False)
    content: Mapped[str] = mapped_column(sqlalchemy.Text, nullable=False)
    citations: Mapped[str | None] = mapped_column(sqlalchemy.Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )

    conversation: Mapped["ConversationSchema"] = relationship(
        "ConversationSchema",
        back_populates="messages",
    )
