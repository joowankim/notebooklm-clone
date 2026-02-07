---
paths:
  - "**/*.py"
---

# Type Hints

## Principle (Why)

Type hints **explicitly define code contracts**.

- Can understand what functions receive and return without documentation
- Improves IDE autocomplete and error detection
- Finds type mismatches at compile time during refactoring
- Prevents runtime bugs at development time
- Makes intention easier to grasp during code review

## Rules (What)

1. **Type hints required for all function parameters**
2. **Return type required for all functions** - Even when returning `None`, specify `-> None`
3. **Generic types include type variables** - Use `list[str]` instead of `list`, `dict[str, int]` instead of `dict`
4. **Use Union syntax instead of Optional** - Use `str | None` (Python 3.10+)
5. **Leverage Self type** - Use in method chaining or factory methods
6. **Avoid dict[str, Any]** - Specify data shape with concrete `pydantic.BaseModel` subtypes

## Examples (How)

```python
from typing import Self, TypeVar, Generic, Callable, Generator
from collections.abc import Sequence, Mapping

# Basic type hints
def create_user(name: str, age: int) -> User:
    return User(name=name, age=age)

def find_user(user_id: str) -> User | None:
    return repository.find_by_id(user_id)

# Collection types (type variables required)
def get_names(users: list[User]) -> list[str]:
    return [user.name for user in users]

def get_config() -> dict[str, str]:
    return {"key": "value"}

def process_items(items: Sequence[str]) -> list[str]:
    return list(items)

# Generator type
def iter_users(users: list[User]) -> Generator[User, None, None]:
    for user in users:
        yield user

# Callable type
Handler = Callable[[Request], Response]

def register_handler(path: str, handler: Callable[[Request], Response]) -> None:
    pass

# Self type
class Builder:
    def with_name(self, name: str) -> Self:
        return self.model_copy(update={"name": name})

# Generic class
T = TypeVar("T")

class Repository(Generic[T]):
    def find_by_id(self, id: str) -> T | None:
        pass

    def find_all(self) -> list[T]:
        pass
```

```python
# BAD: Missing type hints
def create_user(name, age):  # No parameter types
    return User(name=name, age=age)  # No return type

# BAD: Missing generic type variables
def get_items() -> list:  # list[???]
    pass

def get_mapping() -> dict:  # dict[???, ???]
    pass
```

```python
import pydantic
from typing import Any

# Avoid dict[str, Any] - Use pydantic.BaseModel

# BAD: dict[str, Any] doesn't reveal data shape
def create_user(data: dict[str, Any]) -> User:
    name = data["name"]  # Possible KeyError, unclear type
    email = data["email"]
    return User(name=name, email=email)

def process_order(order_data: dict[str, Any]) -> None:
    # Can't tell what keys order_data should have
    pass

# GOOD: Specify data shape with pydantic.BaseModel
class CreateUserRequest(pydantic.BaseModel):
    name: str
    email: str
    age: int | None = None

def create_user(request: CreateUserRequest) -> User:
    # Supports IDE autocomplete, type validation, and documentation
    return User(name=request.name, email=request.email)

class ProcessOrderRequest(pydantic.BaseModel):
    order_id: str
    items: list[OrderItem]
    shipping_address: Address

def process_order(request: ProcessOrderRequest) -> None:
    # Required fields and types are clear
    pass

# GOOD: Use concrete types for config or options too
class DatabaseConfig(pydantic.BaseModel):
    host: str
    port: int
    username: str
    password: str
    database: str

def connect_database(config: DatabaseConfig) -> Connection:
    pass

# Exception: When structure is uncontrollable like external API responses
def parse_external_response(response: dict[str, Any]) -> User:
    # External API responses may unavoidably be dict[str, Any]
    # Convert to pydantic model as soon as possible
    validated = ExternalUserResponse.model_validate(response)
    return User.from_external(validated)
```

## Exceptions

- Test functions starting with `test_`
- Dunder methods like `__init__`, `__str__`
- Functions decorated with `@pytest.fixture`
- Dynamic code that cannot express types (should be minimized)
