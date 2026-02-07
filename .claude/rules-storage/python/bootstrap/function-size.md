---
paths:
  - "**/*.py"
---

# Function & File Size

## Principle (Why)

Small units are **easier to understand and test**.

- Long functions likely have multiple responsibilities (SRP violation)
- Code that doesn't fit on one screen makes it hard to grasp the overall flow
- Small functions have higher reusability
- Small units are easier to isolate when writing tests
- Deep nesting increases cognitive load

## Rules (What)

1. **Functions: 20 lines recommended, 50 lines max** - Must split if exceeds 50 lines
2. **Files: 200-400 lines recommended, 800 lines max** - Must split module if exceeds 800 lines
3. **Nesting depth: 4 levels max** - Reduce nesting with early returns
4. **Parameters: 3 recommended, 5 max** - Group into objects if exceeding
5. **Classes: 100 lines recommended, 300 lines max**

## Examples (How)

```python
# GOOD: Split into small functions
async def create_order(request: CreateOrderRequest) -> Order:
    validate_request(request)
    order = build_order(request)
    await save_order(order)
    await notify_created(order)
    return order

def validate_request(request: CreateOrderRequest) -> None:
    if not request.items:
        raise ValidationError("Items required")
    if request.total < 0:
        raise ValidationError("Invalid total")

def build_order(request: CreateOrderRequest) -> Order:
    return Order.pending(
        items=request.items,
        total=request.total,
    )
```

```python
# GOOD: Reduce nesting with early returns
def process_user(user: User | None) -> Result[User]:
    if user is None:
        return Result.error("User not found")

    if not user.is_active:
        return Result.error("User inactive")

    if not user.has_permission:
        return Result.error("No permission")

    return Result.success(user.process())

# BAD: Deep nesting
def process_user(user: User | None) -> Result[User]:
    if user is not None:
        if user.is_active:
            if user.has_permission:
                return Result.success(user.process())
            else:
                return Result.error("No permission")
        else:
            return Result.error("User inactive")
    else:
        return Result.error("User not found")
```

```python
# GOOD: Group many parameters into an object
import pydantic


class CreateUserRequest(pydantic.BaseModel):
    name: str
    email: str
    age: int
    address: str
    phone: str

def create_user(request: CreateUserRequest) -> User:
    pass

# BAD: Too many parameters
def create_user(
    name: str,
    email: str,
    age: int,
    address: str,
    phone: str,
    company: str,
) -> User:
    pass
```

## Exceptions

- Inherently complex logic like state machines or parsers
- Configuration files or constant definition files
- Auto-generated code
