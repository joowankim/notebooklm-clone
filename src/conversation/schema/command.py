"""Conversation command schemas."""

import pydantic


class CreateConversation(pydantic.BaseModel):
    """Command to create a new conversation."""

    title: str | None = None

    model_config = pydantic.ConfigDict(extra="forbid")


class SendMessage(pydantic.BaseModel):
    """Command to send a message in a conversation."""

    content: str

    model_config = pydantic.ConfigDict(extra="forbid")

    @pydantic.field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message content cannot be empty")
        return v.strip()
