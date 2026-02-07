---
paths:
  - "**/schema/**/*.py"
  - "**/schemas/**/*.py"
  - "**/dto/**/*.py"
  - "**/entrypoint/**/*.py"
  - "**/api/**/*.py"
---

# DDD DTO & Schema

## Principle (Why)

DTO (Data Transfer Object) and Schema **handle data transfer and transformation between layers**.

- Separation of concerns with data structures appropriate for each layer
- Maintains encapsulation by not directly exposing Domain Entity to outside
- API changes don't affect domain model (and vice versa)
- Input validation and serialization logic placed in clear locations
- Each layer can evolve independently

## Data Flow

```
[Client]
    ↓ request.CreateOrder
[Presentation Layer]
    ↓ command.CreateOrder
[Application Layer]
    ↓ model.Order (Entity)
[Domain Layer]
    ↓ model.Order (Entity)
[Infrastructure Layer]
    ↓ schema.Order (DBSchema)
[Database]

[Database]
    ↓ schema.Order
[Infrastructure Layer]
    ↓ model.Order (Entity)
[Domain Layer]
    ↓ model.Order (Entity)
[Application Layer]
    ↓ response.Order
[Presentation Layer]
    ↓ response.Order
[Client]
```

## Rules (What)

1. **Command** - State change request (Application Layer)
2. **Query** - Retrieval request (Application Layer)
3. **Request** - API input (Presentation Layer), converted to Command/Query
4. **Response** - API output (Presentation Layer), converted from Entity
5. **Schema** - ORM model (Infrastructure Layer), mapped with Entity
6. **Base class inheritance** - Define Base class for each type for explicit type expression
7. **Module-based naming** - Remove type suffix, keep domain object name (`command.CreateOrder`, `response.Order`)

## Examples (How)

### Base Classes (common module)

```python
# common/dto.py
from typing import Generic, TypeVar

import pydantic

class Command(pydantic.BaseModel):
    """Base class for state change requests"""
    model_config = pydantic.ConfigDict(frozen=True)


class Query(pydantic.BaseModel):
    """Base class for retrieval requests"""
    model_config = pydantic.ConfigDict(frozen=True)


class Request(pydantic.BaseModel):
    """Base class for API input"""
    model_config = pydantic.ConfigDict(extra="forbid")


class Response(pydantic.BaseModel):
    """Base class for API output"""
    pass


T = TypeVar("T")


class ListResponse(pydantic.BaseModel, Generic[T]):
    """Simple list response"""
    items: list[T]
    total: int = pydantic.Field(..., description="Total count")


class Page(pydantic.BaseModel, Generic[T]):
    """Pagination response"""
    items: list[T]
    total: int = pydantic.Field(..., description="Total count")
    page: int = pydantic.Field(..., description="Current page")
    size: int = pydantic.Field(..., description="Page size")
    has_next: bool = pydantic.Field(..., description="Whether next page exists")

    @classmethod
    def of(
        cls,
        items: list[T],
        total: int,
        page: int,
        size: int,
    ) -> "Page[T]":
        """Page object creation factory"""
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            has_next=(page * size) < total,
        )
```

```python
# common/database.py
from sqlalchemy import orm

class Schema(orm.DeclarativeBase):
    """Base class for ORM models"""
    pass
```

### Command (Application Layer)

```python
# order/application/command.py
import pydantic

from src.common import dto

class CreateOrder(dto.Command):
    """Order creation command"""
    workspace_id: str
    customer_id: str
    items: tuple[OrderItemInput, ...]

    @pydantic.field_validator("items")
    @classmethod
    def validate_items(cls, v: tuple) -> tuple:
        if len(v) == 0:
            raise ValueError("At least one item required")
        return v


class ConfirmOrder(dto.Command):
    """Order confirmation command"""
    order_id: str


class CancelOrder(dto.Command):
    """Order cancellation command"""
    order_id: str
    reason: str | None = None


class OrderItemInput(pydantic.BaseModel):
    """Input structure used within Command"""
    model_config = pydantic.ConfigDict(frozen=True)

    product_id: str
    quantity: int
```

### Query (Application Layer)

```python
# order/application/query.py
import pydantic

from src.common import dto
from src.order.domain import model

class GetOrder(dto.Query):
    """Single order retrieval"""
    order_id: str


class ListOrders(dto.Query):
    """Order list retrieval"""
    workspace_id: str
    customer_id: str | None = None
    status: model.Status | None = None
    page: int = 1
    size: int = 20

    @pydantic.field_validator("page")
    @classmethod
    def validate_page(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Page must be >= 1")
        return v

    @pydantic.field_validator("size")
    @classmethod
    def validate_size(cls, v: int) -> int:
        if not 1 <= v <= 100:
            raise ValueError("Size must be 1-100")
        return v
```

### Request (Presentation Layer)

```python
# order/entrypoint/request.py
import pydantic

from src.common import dto

class CreateOrder(dto.Request):
    """Order creation API input"""
    customer_id: str = pydantic.Field(
        ...,
        description="Customer ID",
        example="cust_abc123",
    )
    items: list[OrderItem] = pydantic.Field(
        ...,
        description="Order items list",
        min_length=1,
    )


class OrderItem(dto.Request):
    """Order item input"""
    product_id: str = pydantic.Field(..., description="Product ID")
    quantity: int = pydantic.Field(..., ge=1, description="Quantity")
```

### Response (Presentation Layer)

```python
# order/entrypoint/response.py
import datetime
from typing import Self

import pydantic

from src.common import dto
from src.order.domain import model

class Order(dto.Response):
    """Order detail response"""
    model_config = pydantic.ConfigDict(
        json_schema_extra={
            "example": {
                "id": "order_abc123",
                "customer_id": "cust_xyz789",
                "status": "pending",
                "total": 50000,
                "created_at": "2024-01-15T09:30:00Z",
            }
        }
    )

    id: str = pydantic.Field(..., description="Order ID")
    customer_id: str = pydantic.Field(..., description="Customer ID")
    status: str = pydantic.Field(..., description="Order status")
    total: int = pydantic.Field(..., description="Order total")
    items: list[OrderItem] = pydantic.Field(..., description="Order items")
    created_at: datetime.datetime = pydantic.Field(..., description="Created at")

    @classmethod
    def from_entity(cls, entity: model.Order) -> Self:
        return cls(
            id=entity.id,
            customer_id=entity.customer_id,
            status=entity.status.value,
            total=entity.total.amount,
            items=[OrderItem.from_entity(item) for item in entity.items],
            created_at=entity.created_at,
        )


class OrderItem(dto.Response):
    """Order item response"""
    id: str
    product_id: str
    quantity: int
    unit_price: int
    subtotal: int

    @classmethod
    def from_entity(cls, entity: model.OrderItem) -> Self:
        return cls(
            id=entity.id,
            product_id=entity.product_id,
            quantity=entity.quantity,
            unit_price=entity.unit_price.amount,
            subtotal=entity.subtotal.amount,
        )


class OrderId(dto.Response):
    """Return only order ID"""
    id: str = pydantic.Field(..., description="Order ID")


# Use Generic for list/page responses
# dto.ListResponse[Order]  - Simple list
# dto.Page[Order]          - Pagination
```

### Schema (Infrastructure Layer)

```python
# order/adapter/schema.py
import datetime

import sqlalchemy
from sqlalchemy import orm

from src.common.database import Schema

class Order(Schema):
    """Orders table"""
    __tablename__ = "orders"

    id: orm.Mapped[str] = orm.mapped_column(primary_key=True)
    workspace_id: orm.Mapped[str] = orm.mapped_column(
        sqlalchemy.String(36),
        index=True,
    )
    customer_id: orm.Mapped[str] = orm.mapped_column(
        sqlalchemy.String(36),
        index=True,
    )
    status: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(20))
    total_amount: orm.Mapped[int] = orm.mapped_column(sqlalchemy.Integer)
    total_currency: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(3))
    created_at: orm.Mapped[datetime.datetime] = orm.mapped_column(
        sqlalchemy.DateTime(timezone=True),
    )
    updated_at: orm.Mapped[datetime.datetime] = orm.mapped_column(
        sqlalchemy.DateTime(timezone=True),
        onupdate=datetime.datetime.now(datetime.UTC),
    )

    items: orm.Mapped[list["OrderItem"]] = orm.relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderItem(Schema):
    """Order items table"""
    __tablename__ = "order_items"

    id: orm.Mapped[str] = orm.mapped_column(primary_key=True)
    order_id: orm.Mapped[str] = orm.mapped_column(
        sqlalchemy.ForeignKey("orders.id", ondelete="CASCADE"),
    )
    product_id: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(36))
    quantity: orm.Mapped[int] = orm.mapped_column(sqlalchemy.Integer)
    unit_price: orm.Mapped[int] = orm.mapped_column(sqlalchemy.Integer)
    currency: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(3))

    order: orm.Mapped["Order"] = orm.relationship(back_populates="items")
```

### Mapper (Infrastructure Layer)

```python
# order/adapter/mapper.py
from src.order.adapter import schema
from src.order.domain import model

class OrderMapper:
    """schema.Order ↔ model.Order conversion"""

    @staticmethod
    def to_entity(record: schema.Order) -> model.Order:
        items = tuple(
            model.OrderItem(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=model.Money(amount=item.unit_price, currency=item.currency),
            )
            for item in record.items
        )
        return model.Order(
            id=record.id,
            customer_id=record.customer_id,
            items=items,
            status=model.Status(record.status),
            total=model.Money(amount=record.total_amount, currency=record.total_currency),
            created_at=record.created_at,
        )

    @staticmethod
    def to_record(entity: model.Order) -> schema.Order:
        return schema.Order(
            id=entity.id,
            customer_id=entity.customer_id,
            status=entity.status.value,
            total_amount=entity.total.amount,
            total_currency=entity.total.currency,
            created_at=entity.created_at,
            items=[
                schema.OrderItem(
                    id=item.id,
                    order_id=entity.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    unit_price=item.unit_price.amount,
                    currency=item.unit_price.currency,
                )
                for item in entity.items
            ],
        )
```

### API usage example

```python
# order/entrypoint/api.py
import http

from fastapi import APIRouter, Depends, Header, Query

from src.common import dto
from src.order.application import command, query
from src.order.entrypoint import request, response

router = APIRouter(prefix="/orders", tags=["order"])

@router.post(
    "/",
    response_model=response.OrderId,
    status_code=http.HTTPStatus.CREATED,
)
async def create_order(
    req: request.CreateOrder,
    workspace_id: str = Header(..., alias="X-Workspace-Id"),
    handler: CreateOrderHandler = Depends(...),
) -> response.OrderId:
    # Convert request → command
    cmd = command.CreateOrder(
        workspace_id=workspace_id,
        customer_id=req.customer_id,
        items=tuple(
            command.OrderItemInput(product_id=item.product_id, quantity=item.quantity)
            for item in req.items
        ),
    )
    order = await handler.handle(cmd)
    return response.OrderId(id=order.id)


@router.get(
    "/{order_id}",
    response_model=response.Order,
)
async def get_order(
    order_id: str,
    handler: GetOrderHandler = Depends(...),
) -> response.Order:
    qry = query.GetOrder(order_id=order_id)
    order = await handler.handle(qry)
    # Convert entity → response
    return response.Order.from_entity(order)


@router.get(
    "/",
    response_model=dto.Page[response.Order],
)
async def list_orders(
    workspace_id: str = Header(..., alias="X-Workspace-Id"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    handler: ListOrdersHandler = Depends(...),
) -> dto.Page[response.Order]:
    qry = query.ListOrders(workspace_id=workspace_id, page=page, size=size)
    result = await handler.handle(qry)
    # Use Generic Page
    return dto.Page.of(
        items=[response.Order.from_entity(order) for order in result.items],
        total=result.total,
        page=page,
        size=size,
    )
```

### Type usage in Handler

```python
# order/application/handler.py
from src.common.dto import Command, Query
from src.order.application import command, query
from src.order.domain import model

class CreateOrderHandler:
    async def handle(self, cmd: command.CreateOrder) -> model.Order:
        # cmd is a subtype of Command
        ...


class GetOrderHandler:
    async def handle(self, qry: query.GetOrder) -> model.Order:
        # qry is a subtype of Query
        ...


# Generic dispatcher example
class CommandDispatcher:
    async def dispatch(self, cmd: Command) -> None:
        """Handle all Command types"""
        handler = self._handlers.get(type(cmd))
        await handler.handle(cmd)
```

### Directory structure

```
src/
├── common/
│   ├── dto.py              # Command, Query, Request, Response, ListResponse[T], Page[T]
│   └── database.py         # Schema base class
│
└── order/
    ├── domain/
    │   └── model.py        # Order, OrderItem (Entity)
    │
    ├── application/
    │   ├── command.py      # CreateOrder, ConfirmOrder, CancelOrder
    │   ├── query.py        # GetOrder, ListOrders
    │   └── handler.py      # CreateOrderHandler, GetOrderHandler
    │
    ├── adapter/
    │   ├── schema.py       # Order, OrderItem (DBSchema)
    │   ├── mapper.py       # OrderMapper
    │   └── repository.py   # OrderRepository implementation
    │
    └── entrypoint/
        ├── api.py          # FastAPI Router
        ├── request.py      # CreateOrder, OrderItem
        └── response.py     # Order, OrderItem, OrderId (use dto.Page[T] for lists)
```

### GOOD vs BAD

```python
# BAD: Duplicate suffix
from src.order.application.command import CreateOrderCommand
cmd = CreateOrderCommand(...)

# GOOD: Module-based naming (remove type suffix, keep domain object name)
from src.order.application import command
cmd = command.CreateOrder(...)


# BAD: Generic BaseModel without Base class
class CreateOrder(pydantic.BaseModel):  # Unclear if Command
    ...

# GOOD: Explicit Base class
class CreateOrder(dto.Command):  # Clearly a Command
    ...


# BAD: Directly expose Domain Entity to API
@router.get("/orders/{order_id}")
async def get_order(order_id: str) -> model.Order:
    return await repository.find_by_id(order_id)

# GOOD: Convert to Response
@router.get("/orders/{order_id}")
async def get_order(order_id: str) -> response.Order:
    order = await repository.find_by_id(order_id)
    return response.Order.from_entity(order)
```

## Exceptions

- For simple CRUD APIs, Request/Command distinction can be omitted
- Response schema can be simplified for internal APIs
- In event sourcing, Event should also be defined as separate Base class
