---
paths:
  - "**/*.py"
---

# Immutability

## Principle (Why)

Immutability creates **predictable code**.

- When objects are mutated, it's hard to track where the changes occurred
- Mutating shared objects causes unintended side effects
- Prevents race conditions in concurrent environments
- Makes testing easier (state isolation)
- When functions don't mutate inputs, results are easier to predict

## Rules (What)

1. **Never mutate objects directly** - Always return new objects
2. **Use dedicated methods for state changes** - Use explicit methods like `mark_as_completed()`
3. **Use Pydantic model_copy** - Leverage `model_copy(update={})` for Entity state transitions
4. **Create new collections** - Use spread operators or create new lists instead of `append`, `pop`
5. **Set frozen=True** - Enforce immutability on Pydantic models

## Examples (How)

```python
from typing import Self
import pydantic

class User(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)

    id: str
    name: str
    status: UserStatus

    # GOOD: Return new instance
    def deactivate(self) -> Self:
        if self.status == UserStatus.INACTIVE:
            raise InvalidStatusError("Already inactive")
        return self.model_copy(update={"status": UserStatus.INACTIVE})

# Usage
user = user.deactivate()  # Assign new instance
```

```python
# GOOD: Create new list
def add_item(items: list[str], new_item: str) -> list[str]:
    return [*items, new_item]

def remove_item(items: list[str], target: str) -> list[str]:
    return [item for item in items if item != target]

# BAD: Mutate existing list
def add_item(items: list[str], new_item: str) -> list[str]:
    items.append(new_item)  # MUTATION!
    return items
```

```python
# GOOD: Create new dictionary
def update_config(config: dict[str, str], key: str, value: str) -> dict[str, str]:
    return {**config, key: value}

# BAD: Mutate existing dictionary
def update_config(config: dict[str, str], key: str, value: str) -> dict[str, str]:
    config[key] = value  # MUTATION!
    return config
```

## Exceptions

- Local variable mutation in performance-critical inner loops (when not exposed externally)
- Caches or buffers explicitly designed as mutable
- Fixture setup in tests
