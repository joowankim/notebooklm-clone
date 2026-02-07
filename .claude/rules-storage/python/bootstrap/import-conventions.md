---
paths:
  - "**/*.py"
---

# Import Conventions

## Principle (Why)

Import rules **clarify code origins** and make **dependencies traceable**.

- `BaseModel` alone doesn't show where it came from → `pydantic.BaseModel` has clear origin
- Prevents namespace conflicts (same names can exist in multiple libraries)
- Makes IDE autocomplete and refactoring tools work better
- Makes external dependencies easier to identify during code review

## Rules (What)

1. **External libraries use module import** - `import pydantic` then use `pydantic.BaseModel`
2. **Internal packages use package import** - `from src.user.domain import model` then use `model.User`
3. **Follow import order** - Standard library → External → Internal common → Internal domain
4. **Use absolute paths** - Relative paths (`..`) break easily during refactoring
5. **Top-level import only** - No import statements inside functions/methods (prevents circular dependencies between modules/domains)
6. **Allowed exceptions** - `typing`, `__future__`, `collections.abc`, internal packages allow `from import`

## Examples (How)

```python
# 1. Standard library
import datetime
import uuid
from typing import Self, ClassVar, Generator

# 2. External libraries (module import)
import pydantic
import sqlalchemy
from dependency_injector import containers, providers

# 3. Internal common modules
from src import common
from src import exceptions

# 4. Internal domain modules
from src.user.domain import model, service
from src.order.adapter import repository
```

```python
# GOOD: Clear origin
query = sqlalchemy.select(UserSchema)
user = pydantic.BaseModel()
now = datetime.datetime.now(datetime.UTC)

# BAD: Unclear origin
from sqlalchemy import select
from pydantic import BaseModel

query = select(UserSchema)  # sqlalchemy? Another ORM?
```

```python
# BAD: Nested import inside function (hides dependencies, enables circular imports)
def get_user(user_id: str) -> User:
    from src.user.domain import model  # Forbidden!
    return model.User(id=user_id)

def send_notification(user: User) -> None:
    import smtplib  # Forbidden! Even standard library
    ...

# GOOD: All imports at module top level
from src.user.domain import model
import smtplib

def get_user(user_id: str) -> User:
    return model.User(id=user_id)

def send_notification(user: User) -> None:
    ...
```

## Exceptions

- `typing` module: Type annotations are frequently used, so `from typing import` is allowed
- `__future__` module: Allowed for Python version compatibility
- `collections.abc`: Abstract base classes are allowed
- Test code `pytest` fixture-related imports
