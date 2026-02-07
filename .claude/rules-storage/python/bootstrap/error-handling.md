---
paths:
  - "**/*.py"
---

# Error Handling

## Principle (Why)

Good error handling **reveals problems clearly rather than hiding them**.

- Broad exception handling swallows bugs
- Must preserve error causes to enable debugging
- Users need friendly messages, developers need detailed information
- Early returns separate normal flow from error flow
- Sensitive information in error messages creates security risks

## Rules (What)

1. **Use specific exceptions** - Avoid `except Exception`, catch specific exceptions
2. **Define custom exception hierarchy** - Create exception classes matching the domain
3. **Use exception chaining** - Preserve causes with `raise ... from exc`
4. **Early return pattern** - Handle error cases first and return
5. **Never expose sensitive information** - Don't include passwords, tokens in error messages
6. **Actionable messages** - Specify what went wrong and what to do

## Examples (How)

```python
# Domain exception hierarchy
class DomainError(Exception):
    """Base domain error."""
    pass

class NotFoundError(DomainError):
    """Resource not found."""
    pass

class ValidationError(DomainError):
    """Validation failed."""
    pass

class UserNotFoundError(NotFoundError):
    def __init__(self, user_id: str) -> None:
        super().__init__(f"User not found: {user_id}")
        self.user_id = user_id
```

```python
import json

# GOOD: Preserve cause with exception chaining
try:
    data = json.loads(raw_data)
except json.JSONDecodeError as exc:
    raise ValidationError(f"Invalid JSON format: {exc}") from exc

# BAD: Lost cause exception
try:
    data = json.loads(raw_data)
except json.JSONDecodeError:
    raise ValidationError("Invalid JSON format")  # Unknown cause
```

```python
# GOOD: Specific exception handling
try:
    user = repository.find_by_id(user_id)
except UserNotFoundError:
    return None
except DatabaseConnectionError as exc:
    logger.error("Database error", exc_info=exc)
    raise ServiceError("Failed to fetch user") from exc

# BAD: Swallow all exceptions
try:
    user = repository.find_by_id(user_id)
except Exception:
    return None  # Can't tell what error occurred
```

```python
# GOOD: Actionable error message
raise ValidationError(
    f"Invalid email format: '{email}'. Expected format: user@domain.com"
)

# BAD: Vague message
raise ValidationError("Invalid input")
```

```python
# BAD: Exposing sensitive information
raise AuthError(f"Invalid password for {email}: {password}")

# GOOD: Exclude sensitive information
raise AuthError(f"Invalid credentials for {email}")
```

## Exceptions

- Top-level handlers that truly must handle all exceptions (log then re-raise)
- When external libraries don't provide specific exceptions
