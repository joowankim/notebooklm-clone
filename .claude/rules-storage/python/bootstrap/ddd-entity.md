---
paths:
  - "**/domain/**/*.py"
  - "**/model.py"
  - "**/models/*.py"
---

# DDD Entity Patterns

## Principle (Why)

DDD Entity pattern **encapsulates business logic within domain objects**.

- When business rules are scattered across Handlers or Services, duplication and inconsistency occur
- When Entities are responsible for their own state transitions, invariants can be guaranteed
- Separating domain models from persistence models allows each to evolve independently
- Factory methods ensure only objects with valid state are created
- Adding behavior to Enums centralizes state-related logic

## Rules (What)

1. **Entities are immutable** - Set `frozen=True`, state changes return new instances
2. **State transitions via Entity methods** - `mark_as_completed()`, `deactivate()`, etc.
3. **Create via factory methods** - State-based factories like `Order.pending()`, `User.create()`
4. **Add properties to Enums** - State-related logic like `is_terminal`, `is_editable`
5. **Separate Model and Record** - Connect domain Entity and ORM Schema via Mapper
6. **Business logic inside Entity** - Handlers only orchestrate, domain objects contain logic

## Examples (How)

```python
import datetime
import uuid
import enum
from typing import Self

import pydantic

class OrderStatus(enum.StrEnum):
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"

    @property
    def is_editable(self) -> bool:
        return self in (OrderStatus.DRAFT, OrderStatus.PENDING)

    @property
    def is_terminal(self) -> bool:
        return self in (OrderStatus.SHIPPED, OrderStatus.CANCELLED)

    @property
    def can_cancel(self) -> bool:
        return not self.is_terminal


class Order(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(frozen=True)

    id: str
    items: list[OrderItem]
    status: OrderStatus
    created_at: datetime.datetime

    # Factory method: state-based creation
    @classmethod
    def pending(cls, items: list[OrderItem]) -> Self:
        return cls(
            id=uuid.uuid4().hex,
            items=items,
            status=OrderStatus.PENDING,
            created_at=datetime.datetime.now(datetime.UTC),
        )

    # State transition: includes business rules
    def confirm(self) -> Self:
        if not self.status.is_editable:
            raise InvalidStatusError(f"Cannot confirm order in {self.status} status")
        return self.model_copy(update={"status": OrderStatus.CONFIRMED})

    def cancel(self) -> Self:
        if not self.status.can_cancel:
            raise InvalidStatusError(f"Cannot cancel order in {self.status} status")
        return self.model_copy(update={"status": OrderStatus.CANCELLED})
```

```python
# Model vs Record separation (Mapper pattern)

# domain/model.py - Pure domain Entity (no ORM dependencies)
class Document(pydantic.BaseModel):
    id: str
    title: str
    status: DocumentStatus

# adapter/schema.py - ORM Schema
class DocumentSchema(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True)
    title = Column(String)
    status = Column(String)

# domain/mapper.py - Handles conversion
class DocumentMapper:
    @staticmethod
    def to_record(entity: Document) -> DocumentSchema:
        return DocumentSchema(
            id=entity.id,
            title=entity.title,
            status=entity.status.value,
        )

    @staticmethod
    def to_entity(record: DocumentSchema) -> Document:
        return Document(
            id=record.id,
            title=record.title,
            status=DocumentStatus(record.status),
        )
```

```python
# BAD: Business logic in Handler
class ConfirmOrderHandler:
    def handle(self, order: Order) -> Order:
        if order.status not in ("draft", "pending"):  # Logic outside entity!
            raise InvalidStatusError()
        order.status = "confirmed"  # Direct mutation!
        return order

# GOOD: Business logic inside Entity
class ConfirmOrderHandler:
    def handle(self, order_id: str) -> Order:
        order = self.repository.find_by_id(order_id)
        confirmed = order.confirm()  # Entity applies rules
        self.repository.save(confirmed)
        return confirmed
```

## Exceptions

- Domains with simple CRUD only (Anemic Domain Model may be appropriate)
- When integrating with legacy systems where existing structure must be followed
- In prototypes or MVPs where rapid development is prioritized
