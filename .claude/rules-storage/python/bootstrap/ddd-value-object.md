---
paths:
  - "**/domain/**/*.py"
  - "**/model.py"
  - "**/models/*.py"
---

# DDD Value Object

## Principle (Why)

Value Object is **an object whose equality is determined solely by its values, without an identifier**.

- Entities are distinguished by ID, but Value Objects are distinguished by attribute values
- Immutability enables safe sharing without side effects
- Domain concepts are expressed with explicit types instead of primitives (str, int)
- Validation logic is encapsulated within the Value Object
- Identical values are always interchangeable (substitutability)

## Rules (What)

1. **Immutable** - Set `frozen=True`, cannot be changed after creation
2. **Value-based equality** - No ID, objects with same attributes are identical
3. **Self-validating** - Raises exception if invalid at creation time
4. **Can include behavior** - Contains calculation or transformation methods related to the value
5. **Replace primitives** - Use `Email` instead of `str`, `Money` instead of `int`, etc.
6. **Choose implementation approach** - Single values use primitive inheritance/Annotated, composite values use BaseModel

## Implementation Approach Selection Guide

| Approach | When to Use | Examples |
|----------|-------------|----------|
| Annotated + Field | Simple constraints (range, length), no behavior | `Age`, `Username` |
| Annotated + Validator | Validation/normalization needed, no behavior | `NormalizedEmail`, `Phone` |
| Primitive inheritance | Single value + primitive operations + custom behavior | `Email(str)`, `Percentage(int)` |
| BaseModel | Composite values (multiple fields) | `Money`, `Address`, `DateRange` |

## Examples (How)

### 1. Annotated-based (simple constraints, no behavior)

```python
from typing import Annotated

import pydantic
from pydantic import AfterValidator, Field

# Simple constraints: Annotated + Field
Age = Annotated[int, Field(ge=0, le=150)]
Username = Annotated[str, Field(min_length=3, max_length=20, pattern=r"^[a-z0-9_]+$")]
Quantity = Annotated[int, Field(gt=0)]

# Validation + normalization: Annotated + AfterValidator
def normalize_phone(value: str) -> str:
    import re
    cleaned = re.sub(r"[^0-9]", "", value)
    if not re.match(r"^01[0-9]{8,9}$", cleaned):
        raise ValueError("Invalid phone number")
    return cleaned

Phone = Annotated[str, AfterValidator(normalize_phone)]

# Usage
class Customer(pydantic.BaseModel):
    name: Username
    age: Age
    phone: Phone

customer = Customer(name="john_doe", age=25, phone="010-1234-5678")
assert customer.phone == "01012345678"  # Normalized
```

### 2. Primitive type inheritance (single value + behavior)

```python
from typing import Any, Self

import pydantic
import pydantic_core
from pydantic import GetCoreSchemaHandler

# str inheritance: string operations + custom behavior
class Email(str):
    """Email Value Object"""

    def __new__(cls, value: str) -> Self:
        if "@" not in value:
            raise ValueError(f"Invalid email: {value}")
        return super().__new__(cls, value.lower().strip())

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> pydantic_core.CoreSchema:
        return pydantic_core.core_schema.no_info_after_validator_function(
            cls, handler(str)
        )

    @property
    def domain(self) -> str:
        return self.split("@")[1]

    @property
    def local_part(self) -> str:
        return self.split("@")[0]


# int inheritance: arithmetic operations + custom behavior
class Percentage(int):
    """Percentage Value Object (0-100)"""

    def __new__(cls, value: int) -> Self:
        if not 0 <= value <= 100:
            raise ValueError(f"Percentage must be 0-100: {value}")
        return super().__new__(cls, value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> pydantic_core.CoreSchema:
        return pydantic_core.core_schema.no_info_after_validator_function(
            cls, handler(int)
        )

    def of(self, value: int) -> int:
        """Calculate value at this percentage"""
        return value * self // 100

    def as_decimal(self) -> float:
        return self / 100


# str inheritance: ID prefix validation + generation method
class UserId(str):
    """User ID Value Object"""

    def __new__(cls, value: str) -> Self:
        if not value.startswith("user_"):
            raise ValueError("UserId must start with 'user_'")
        return super().__new__(cls, value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> pydantic_core.CoreSchema:
        return pydantic_core.core_schema.no_info_after_validator_function(
            cls, handler(str)
        )

    @classmethod
    def generate(cls) -> Self:
        import uuid
        return cls(f"user_{uuid.uuid4().hex}")


# Usage examples
email = Email("USER@EXAMPLE.COM")
assert email == "user@example.com"  # str comparison
assert email.domain == "example.com"  # custom property
assert len(email) == 16  # str method

discount = Percentage(20)
assert discount.of(10000) == 2000  # custom method
assert discount + 10 == 30  # int operation

user_id = UserId.generate()
assert user_id.startswith("user_")  # str method
```

### 3. BaseModel-based (composite values)

```python
import datetime
from typing import Self

import pydantic

# Composite value: multiple fields
class Money(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)

    amount: int
    currency: str

    @pydantic.field_validator("amount")
    @classmethod
    def validate_amount(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Amount cannot be negative")
        return v

    def add(self, other: Self) -> Self:
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def multiply(self, factor: int) -> Self:
        return Money(amount=self.amount * factor, currency=self.currency)

    @classmethod
    def krw(cls, amount: int) -> Self:
        return cls(amount=amount, currency="KRW")


class Address(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)

    street: str
    city: str
    postal_code: str
    country: str

    @property
    def full_address(self) -> str:
        return f"{self.street}, {self.city}, {self.postal_code}, {self.country}"

    def with_street(self, street: str) -> Self:
        return self.model_copy(update={"street": street})


class DateRange(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)

    start: datetime.date
    end: datetime.date

    @pydantic.model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.start > self.end:
            raise ValueError("Start date must be before end date")
        return self

    def contains(self, date: datetime.date) -> bool:
        return self.start <= date <= self.end

    @property
    def days(self) -> int:
        return (self.end - self.start).days


# Usage examples
price = Money.krw(10000)
total = price.multiply(3)
assert total.amount == 30000

addr = Address(street="123 Main St", city="Seoul", postal_code="12345", country="KR")
new_addr = addr.with_street("456 New St")  # Maintain immutability
assert addr.street == "123 Main St"  # Original unchanged
```

### 4. Primitive inheritance vs BaseModel comparison

```python
# Primitive inheritance advantage: natural serialization, primitive operations support
class User(pydantic.BaseModel):
    email: Email  # Using Email(str)

user = User(email="test@example.com")
print(user.model_dump_json())
# {"email": "test@example.com"}  ← Clean JSON

# BaseModel case: serialized as nested object
class EmailModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)
    value: str

class UserWithModel(pydantic.BaseModel):
    email: EmailModel

user2 = UserWithModel(email=EmailModel(value="test@example.com"))
print(user2.model_dump_json())
# {"email": {"value": "test@example.com"}}  ← Nested structure
```

```python
# BAD: Direct use of primitives
class Order(pydantic.BaseModel):
    customer_email: str  # No validation
    total_amount: int    # Can be negative, no currency info
    discount_rate: int   # No range validation

# GOOD: Using Value Objects
class Order(pydantic.BaseModel):
    customer_email: Email      # Always valid email
    total_amount: Money        # Cannot be negative, includes currency
    discount_rate: Percentage  # Guaranteed 0-100 range
```

## Exceptions

- DTOs that only need simple data transfer
- When performance is critical and object creation cost is burdensome
- When primitive types are needed for compatibility with external systems
