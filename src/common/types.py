"""Common type definitions."""

import datetime
from typing import Annotated

import pydantic

# DateTime type with UTC timezone awareness
DateTime = Annotated[
    datetime.datetime,
    pydantic.BeforeValidator(lambda v: v if v.tzinfo else v.replace(tzinfo=datetime.timezone.utc)),
]


def utc_now() -> datetime.datetime:
    """Get current UTC datetime."""
    return datetime.datetime.now(datetime.timezone.utc)
