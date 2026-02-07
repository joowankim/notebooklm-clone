---
paths:
  - "**/*.py"
---

# No Hardcoding

## Principle (Why)

Hardcoding is **the enemy of maintenance and security**.

- Secrets in code remain in git history forever
- Code changes required when different values needed per environment (dev/staging/prod)
- Magic numbers have unclear meaning and cause bugs
- Changing values requires code deployment
- Intent is hard to grasp during code review

## Rules (What)

1. **Never put secrets in code** - API keys, passwords, tokens, etc.
2. **Use environment variables** - `os.environ` or configuration libraries
3. **Magic numbers become constants** - Define constants with meaningful names
4. **Magic strings become Enums** - Use Enums for states, types, etc.
5. **Environment variable validation required** - Check required environment variables at app startup

## Examples (How)

```python
import os

# BAD: Hardcoded secrets
API_KEY = "sk-proj-xxxxx"
DATABASE_URL = "postgresql://user:password@localhost/db"

# GOOD: Use environment variables
API_KEY = os.environ["OPENAI_API_KEY"]
DATABASE_URL = os.environ["DATABASE_URL"]
```

```python
# GOOD: Type-safe environment variables with Pydantic Settings
import pydantic_settings

class Settings(pydantic_settings.BaseSettings):
    api_key: str
    database_url: str
    debug: bool = False
    max_connections: int = 10

    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()  # Validated at startup
```

```python
# BAD: Magic numbers
if user.age >= 18:
    pass
if len(items) > 100:
    pass

# GOOD: Meaningful constants
ADULT_AGE = 18
MAX_ITEMS_PER_PAGE = 100

if user.age >= ADULT_AGE:
    pass
if len(items) > MAX_ITEMS_PER_PAGE:
    pass
```

```python
import enum

# BAD: Magic strings
if user.status == "active":
    pass

# GOOD: Use Enum
class UserStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

if user.status == UserStatus.ACTIVE:
    pass
```

## Exceptions

- Fixture data in test code
- Inside constant definition files (`constants.py`)
- Clear default values (`timeout=30`, `retries=3`)
- Mathematical/physical constants
