---
paths:
  - "**/container.py"
  - "**/containers.py"
  - "**/dependency/**/*.py"
---

# Dependency Injection

## Principle (Why)

Dependency injection **reduces coupling and makes testing easier**.

- When classes create dependencies directly, replacement is impossible
- Must receive dependencies via injection to replace with mocks in tests
- Explicit dependency graphs make structure easier to understand
- Centralized lifecycle management (Singleton, Factory)
- Can detect circular dependencies at compile time

## Rules (What)

1. **Use constructor injection** - Receive dependencies in `__init__`
2. **Container hierarchy** - Adapter(infrastructure) → Service(domain) → Handler(application)
3. **Distinguish provider types** - Factory(stateless), Singleton(shared), Dependency(external injection)
4. **No service locator** - Hidden dependencies make testing and understanding difficult
5. **Connect with wiring** - Configure dependency injection per module

## Examples (How)

```python
from dependency_injector import containers, providers

# Container hierarchy
class AdapterContainer(containers.DeclarativeContainer):
    """Infrastructure layer: Repository, external clients"""
    db_session = providers.Dependency()  # Injected externally

    user_repository = providers.Factory(
        UserRepository,
        session=db_session,
    )

class ServiceContainer(containers.DeclarativeContainer):
    """Domain layer: Business logic"""
    adapter = providers.DependenciesContainer()

    user_creator = providers.Factory(
        UserCreator,
        user_repository=adapter.user_repository,
    )

class HandlerContainer(containers.DeclarativeContainer):
    """Application layer: Use case orchestration"""
    service = providers.DependenciesContainer()

    create_user_handler = providers.Factory(
        CreateUserHandler,
        user_creator=service.user_creator,
    )
```

```python
# FastAPI integration
from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/users")
@inject
async def create_user(
    cmd: CreateUserCommand,
    handler: CreateUserHandler = Depends(
        Provide[ApplicationContainer.handler.create_user_handler]
    ),
) -> UserResponse:
    return handler.handle(cmd)
```

```python
# Replace with mock in tests
def test_create_user() -> None:
    container = ApplicationContainer()

    # Replace with mock
    container.adapter.user_repository.override(
        providers.Factory(MockUserRepository)
    )

    handler = container.handler.create_user_handler()
    result = handler.handle(CreateUserCommand(name="Test"))

    assert result.name == "Test"
```

```python
# BAD: Direct instantiation (untestable)
class CreateUserHandler:
    def handle(self, cmd: CreateUserCommand) -> User:
        repo = UserRepository(get_session())  # Direct creation!
        service = UserCreator(repo)           # Direct creation!
        return service.create(cmd)

# GOOD: Constructor injection
class CreateUserHandler:
    def __init__(self, user_creator: UserCreator) -> None:
        self.user_creator = user_creator

    def handle(self, cmd: CreateUserCommand) -> User:
        return self.user_creator.create(cmd)
```

```python
# BAD: Service locator (hidden dependency)
class CreateUserHandler:
    def handle(self, cmd: CreateUserCommand) -> User:
        service = ServiceLocator.get(UserCreator)  # Unclear where it comes from
        return service.create(cmd)
```

## Exceptions

- Container initialization at entry point (main.py)
- Dependencies provided by framework (FastAPI's Request, etc.)
- Static utility functions (pure functions without dependencies)
