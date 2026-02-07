# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Brief description of what this project does.

## Commands

```bash
# Run tests
uv run pytest tests/ -v

# Run linter
uvx ruff check src/
```

## Coding Conventions

This project follows strict coding conventions. Claude Code will automatically apply rules based on file paths.

### Python Rules (\*.py)

| Rule               | Description                                                |
| ------------------ | ---------------------------------------------------------- |
| **Immutability**   | Never mutate objects directly, always return new instances |
| **Function Size**  | Max 50 lines per function, max 5 parameters                |
| **Naming**         | snake_case for functions/variables, PascalCase for classes |
| **Import**         | Use `import module` instead of `from module import X`      |
| **Type Hints**     | Required for all function parameters and return types      |
| **Error Handling** | Use custom exceptions, never catch bare `except:`          |
| **No Hardcoding**  | No hardcoded secrets or magic numbers                      |

### DDD Rules (domain/\*_/_.py)

| Rule             | Description                                                  |
| ---------------- | ------------------------------------------------------------ |
| **Entity**       | Immutable with state transition methods, use factory methods |
| **Value Object** | Immutable, equality by value, self-validating                |
| **Aggregate**    | Single entry point, protect invariants                       |
| **Repository**   | Abstract interface in domain, implementation in adapter      |
| **Service**      | Stateless, orchestrate domain operations                     |
| **DTO/Schema**   | Separate from domain models, use for API boundaries          |

### TypeScript Rules (_.ts, _.tsx)

| Rule               | Description                                   |
| ------------------ | --------------------------------------------- |
| **Immutability**   | Use spread operators, avoid mutating methods  |
| **Type Safety**    | No `any`, use strict TypeScript               |
| **React Patterns** | Functional components, custom hooks for logic |

## Testing

- **Minimum coverage**: 80%
- **TDD workflow**: Write tests first, then implement
- **Test structure**: Arrange-Act-Assert pattern

```python
def test_user_can_be_deactivated() -> None:
    # Arrange
    user = User.active(name="John")

    # Act
    deactivated = user.deactivate()

    # Assert
    assert deactivated.status == UserStatus.INACTIVE
```

## Git Workflow

- **Commit format**: `<type>: <description>` (feat, fix, refactor, docs, test)
- **Branch naming**: `feature/<name>`, `fix/<name>`, `refactor/<name>`

## Environment Variables

```bash
DATABASE_URL=postgresql://localhost:5432/mydb
REDIS_URL=redis://localhost:6379
API_KEY=  # Set in .env (never commit)
```

## Dependencies

Key dependencies and their purposes:

- `fastapi`: Web framework
- `pydantic`: Data validation and settings
- `sqlalchemy`: Database ORM
- `dependency-injector`: Dependency injection container
