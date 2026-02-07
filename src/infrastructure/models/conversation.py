"""Conversation ORM schema."""

import datetime

import sqlalchemy
import sqlalchemy.orm

from src import database as database_module


class ConversationSchema(database_module.Base):
    """SQLAlchemy ORM model for conversations."""

    __tablename__ = "conversations"

    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.String(32), primary_key=True)
    notebook_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32),
        sqlalchemy.ForeignKey("notebooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: sqlalchemy.orm.Mapped[str | None] = sqlalchemy.orm.mapped_column(sqlalchemy.String(255), nullable=True)
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

    messages: sqlalchemy.orm.Mapped[list["MessageSchema"]] = sqlalchemy.orm.relationship(
        "MessageSchema",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class MessageSchema(database_module.Base):
    """SQLAlchemy ORM model for messages."""

    __tablename__ = "messages"

    id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.String(32), primary_key=True)
    conversation_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32),
        sqlalchemy.ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.String(20), nullable=False)
    content: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(sqlalchemy.Text, nullable=False)
    citations: sqlalchemy.orm.Mapped[str | None] = sqlalchemy.orm.mapped_column(sqlalchemy.Text, nullable=True)
    created_at: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )

    conversation: sqlalchemy.orm.Mapped["ConversationSchema"] = sqlalchemy.orm.relationship(
        "ConversationSchema",
        back_populates="messages",
    )
