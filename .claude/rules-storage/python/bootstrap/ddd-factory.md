---
paths:
  - "**/domain/**/*.py"
  - "**/model.py"
  - "**/models/*.py"
---

# DDD Factory

## Principle (Why)

Factory **encapsulates complex object creation logic**.

- Simplifies complex Aggregate creation and ensures consistency
- Guarantees invariants are always satisfied at creation time
- Client code unaffected when object creation logic changes
- Clearly expresses creation intent (state-based, input-based, etc.)
- Easy to create valid objects in tests

## Rules (What)

1. **Factory Method** - Define as class method of Entity class (`@classmethod`)
2. **State-based factory** - Express initial state in method name (`Order.pending()`)
3. **Input-based factory** - Express primary input in name (`User.with_email()`)
4. **Create only valid state** - Validate invariants at creation time

## Examples (How)

```python
import datetime
import uuid
from typing import Self

import pydantic

# Factory Method: State-based factory

class Order(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)

    id: str
    customer_id: str
    items: tuple[OrderItem, ...]
    status: OrderStatus
    created_at: datetime.datetime
    confirmed_at: datetime.datetime | None = None

    # State-based factory: express initial state in name
    @classmethod
    def pending(cls, customer_id: str, items: list[OrderItem]) -> Self:
        """Create new order in pending state"""
        if not items:
            raise ValueError("Order must have at least one item")
        return cls(
            id=uuid.uuid4().hex,
            customer_id=customer_id,
            items=tuple(items),
            status=OrderStatus.PENDING,
            created_at=datetime.datetime.now(datetime.UTC),
        )

    @classmethod
    def draft(cls, customer_id: str) -> Self:
        """Create empty order for draft save"""
        return cls(
            id=uuid.uuid4().hex,
            customer_id=customer_id,
            items=(),
            status=OrderStatus.DRAFT,
            created_at=datetime.datetime.now(datetime.UTC),
        )


class Task(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)

    id: str
    title: str
    status: TaskStatus
    assignee_id: str | None = None

    @classmethod
    def todo(cls, title: str) -> Self:
        """Create in todo state"""
        return cls(id=uuid.uuid4().hex, title=title, status=TaskStatus.TODO)

    @classmethod
    def in_progress(cls, title: str, assignee_id: str) -> Self:
        """Create in progress state (assignee required)"""
        return cls(
            id=uuid.uuid4().hex,
            title=title,
            status=TaskStatus.IN_PROGRESS,
            assignee_id=assignee_id,
        )
```

```python
# Factory Method: Input-based factory

class User(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)

    id: str
    email: Email
    name: str
    auth_provider: AuthProvider
    external_id: str | None = None

    # Input-based factory: express primary input in name
    @classmethod
    def with_email(cls, email: str, name: str) -> Self:
        """Sign up with email"""
        return cls(
            id=uuid.uuid4().hex,
            email=Email(value=email),
            name=name,
            auth_provider=AuthProvider.EMAIL,
        )

    @classmethod
    def with_google(cls, google_id: str, email: str, name: str) -> Self:
        """Sign up with Google OAuth"""
        return cls(
            id=uuid.uuid4().hex,
            email=Email(value=email),
            name=name,
            auth_provider=AuthProvider.GOOGLE,
            external_id=google_id,
        )

    @classmethod
    def with_kakao(cls, kakao_id: str, email: str, name: str) -> Self:
        """Sign up with Kakao OAuth"""
        return cls(
            id=uuid.uuid4().hex,
            email=Email(value=email),
            name=name,
            auth_provider=AuthProvider.KAKAO,
            external_id=kakao_id,
        )
```

```python
# Factory for Aggregate: Complex Aggregate creation

class OrderFactory:
    """Factory for creating complex Order Aggregate"""

    def __init__(self, pricing_service: PricingService) -> None:
        self._pricing_service = pricing_service

    def create_from_cart(self, cart: Cart, customer: Customer) -> Order:
        """Create order from cart"""
        items = [
            OrderItem(
                id=uuid.uuid4().hex,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            for item in cart.items
        ]

        total = self._pricing_service.calculate_total(items, customer)

        return Order(
            id=uuid.uuid4().hex,
            customer_id=customer.id,
            items=tuple(items),
            total=total,
            status=OrderStatus.PENDING,
            created_at=datetime.datetime.now(datetime.UTC),
        )


# BAD: Complex logic in constructor
class Order:
    def __init__(self, cart: Cart, customer: Customer, pricing_service: PricingService):
        # Entity depends on Service - anti-pattern
        ...

# GOOD: Separate into Factory
order = order_factory.create_from_cart(cart, customer)
```

```python
# Test Factory

class OrderTestFactory:
    """Create valid Order objects for testing"""

    @staticmethod
    def create(
        id: str = "test-order-id",
        customer_id: str = "test-customer-id",
        status: OrderStatus = OrderStatus.PENDING,
        items: list[OrderItem] | None = None,
    ) -> Order:
        if items is None:
            items = [OrderItemTestFactory.create()]

        return Order(
            id=id,
            customer_id=customer_id,
            items=tuple(items),
            status=status,
            created_at=datetime.datetime.now(datetime.UTC),
        )

    @staticmethod
    def create_confirmed(customer_id: str = "test-customer-id") -> Order:
        return OrderTestFactory.create(
            customer_id=customer_id,
            status=OrderStatus.CONFIRMED,
        )


# Usage in tests
def test_cancel_pending_order() -> None:
    order = OrderTestFactory.create(status=OrderStatus.PENDING)
    cancelled = order.cancel()
    assert cancelled.status == OrderStatus.CANCELLED
```

## Exceptions

- Simple Entities are fine with `__init__` or `model_validate`
- No Factory needed when creation logic is not complex
- When validation with Pydantic model_validator is sufficient
