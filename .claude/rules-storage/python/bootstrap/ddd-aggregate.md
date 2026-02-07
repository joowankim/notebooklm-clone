---
paths:
  - "**/domain/**/*.py"
  - "**/aggregate/**/*.py"
---

# DDD Aggregate Root

## Principle (Why)

Aggregate is **an Entity cluster that defines consistency boundaries**.

- Groups related Entities into a single unit to guarantee invariants
- Only the Aggregate Root can be directly referenced from outside - internal Entities are accessed only through the Root
- Transactions are performed on a single Aggregate basis - avoid transactions across multiple Aggregates
- Other Aggregates are referenced by ID only - avoid object references
- Aggregate size should be minimized - include only what requires consistency

## Rules (What)

1. **Root Entity has full responsibility** - All creation, modification, deletion of internal Entities through Root
2. **External access only through Root** - Do not directly reference or save internal Entities
3. **Reference other Aggregates by ID** - Hold only ID instead of object reference
4. **One Repository for one Aggregate** - Save/retrieve by Aggregate unit
5. **Invariants guaranteed within Aggregate** - Transaction boundary = Aggregate boundary

## Examples (How)

```python
import datetime
import uuid
from typing import Self

import pydantic

# Order Aggregate
# - Root: Order
# - Internal Entity: OrderItem (accessed only through Order)

class OrderItem(pydantic.BaseModel):
    """Internal Entity - cannot be created/modified directly outside Order Aggregate"""
    model_config = pydantic.ConfigDict(frozen=True)

    id: str
    product_id: str  # Product Aggregate referenced by ID only
    quantity: int
    unit_price: Money

    @property
    def subtotal(self) -> Money:
        return self.unit_price.multiply(self.quantity)


class Order(pydantic.BaseModel):
    """Aggregate Root - the only entry point from outside"""
    model_config = pydantic.ConfigDict(frozen=True)

    id: str
    customer_id: str  # Customer Aggregate referenced by ID only
    items: tuple[OrderItem, ...]  # tuple for enhanced immutability
    status: OrderStatus
    created_at: datetime.datetime

    # Invariant: Order must have at least one item
    @pydantic.model_validator(mode="after")
    def validate_items(self) -> Self:
        if len(self.items) == 0:
            raise ValueError("Order must have at least one item")
        return self

    # Factory method
    @classmethod
    def create(cls, customer_id: str, items: list[OrderItem]) -> Self:
        return cls(
            id=uuid.uuid4().hex,
            customer_id=customer_id,
            items=tuple(items),
            status=OrderStatus.PENDING,
            created_at=datetime.datetime.now(datetime.UTC),
        )

    # Internal Entity manipulation only through Root
    def add_item(self, product_id: str, quantity: int, unit_price: Money) -> Self:
        if not self.status.is_editable:
            raise InvalidStatusError("Cannot add item to non-editable order")

        new_item = OrderItem(
            id=uuid.uuid4().hex,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
        )
        return self.model_copy(update={"items": self.items + (new_item,)})

    def remove_item(self, item_id: str) -> Self:
        if not self.status.is_editable:
            raise InvalidStatusError("Cannot remove item from non-editable order")

        new_items = tuple(item for item in self.items if item.id != item_id)
        if len(new_items) == 0:
            raise ValueError("Cannot remove last item from order")
        return self.model_copy(update={"items": new_items})

    def update_item_quantity(self, item_id: str, quantity: int) -> Self:
        if not self.status.is_editable:
            raise InvalidStatusError("Cannot update item in non-editable order")

        new_items = tuple(
            item.model_copy(update={"quantity": quantity}) if item.id == item_id else item
            for item in self.items
        )
        return self.model_copy(update={"items": new_items})

    @property
    def total(self) -> Money:
        """Calculations within Aggregate handled by Root"""
        if not self.items:
            return Money.krw(0)
        result = self.items[0].subtotal
        for item in self.items[1:]:
            result = result.add(item.subtotal)
        return result

    def confirm(self) -> Self:
        if not self.status.is_editable:
            raise InvalidStatusError(f"Cannot confirm order in {self.status} status")
        return self.model_copy(update={"status": OrderStatus.CONFIRMED})
```

```python
# Reference other Aggregates by ID only

# BAD: Object reference - tight coupling, unclear consistency boundaries
class Order(pydantic.BaseModel):
    customer: Customer  # Direct reference to Customer object
    items: list[OrderItem]

# GOOD: ID reference - loose coupling, clear boundaries
class Order(pydantic.BaseModel):
    customer_id: str  # Hold only ID
    items: tuple[OrderItem, ...]

# Retrieve separately when needed
class OrderService:
    def get_order_with_customer(self, order_id: str) -> OrderWithCustomer:
        order = self.order_repository.find_by_id(order_id)
        customer = self.customer_repository.find_by_id(order.customer_id)
        return OrderWithCustomer(order=order, customer=customer)
```

```python
# Minimize Aggregate size

# BAD: Aggregate too large - unnecessary locking, concurrency issues
class Customer(pydantic.BaseModel):
    id: str
    orders: list[Order]  # Includes all orders
    reviews: list[Review]  # Includes all reviews
    wishlist: list[Product]  # Even wishlist

# GOOD: Small Aggregate - each with independent consistency boundary
class Customer(pydantic.BaseModel):
    id: str
    name: str
    email: Email

class Order(pydantic.BaseModel):
    id: str
    customer_id: str  # Reference by ID only
    items: tuple[OrderItem, ...]

class Review(pydantic.BaseModel):
    id: str
    customer_id: str  # Reference by ID only
    product_id: str
```

```python
# Repository at Aggregate Root level

class OrderRepository:
    """Save/retrieve Aggregate Root only"""

    async def find_by_id(self, order_id: str) -> Order | None:
        # Load Order and OrderItem together
        ...

    async def save(self, order: Order) -> None:
        # Save Order and OrderItem together
        ...

# BAD: Separate Repository for internal Entity
class OrderItemRepository:  # This should not exist
    async def find_by_id(self, item_id: str) -> OrderItem | None:
        ...
```

## Exceptions

- Read-only views can join multiple Aggregates (CQRS Read Model)
- When eventual consistency is allowed in event-based architecture
- When existing structure must be followed for legacy system integration
