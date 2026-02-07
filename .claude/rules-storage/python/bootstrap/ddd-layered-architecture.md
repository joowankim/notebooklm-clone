---
paths:
  - "**/*.py"
---

# DDD Layered Architecture

## Principle (Why)

Layered Architecture **separates concerns so each layer can evolve independently**.

- Each layer has clear responsibilities
- Dependencies always flow downward (upper → lower)
- Domain layer doesn't depend on infrastructure, making testing easier
- Technology changes (DB, framework) don't affect business logic
- Enables role division and parallel development among team members

## Rules (What)

1. **4 layer separation** - Presentation → Application → Domain → Infrastructure
2. **Dependency direction** - Upper layers depend on lower layers only (no reverse)
3. **Domain is pure** - No external dependencies, no framework imports
4. **Dependency inversion with interfaces** - Domain defines Infrastructure interfaces
5. **Directory structure by layer** - Clear package separation
6. **API endpoint documentation** - Specify summary, description, responses in FastAPI router

## Examples (How)

```
# Directory structure

src/
├── order/                      # Domain module
│   ├── __init__.py
│   ├── domain/                 # Domain Layer
│   │   ├── __init__.py
│   │   ├── model.py           # Entity, Value Object
│   │   ├── service.py         # Domain Service
│   │   ├── repository.py      # Repository interface (Protocol)
│   │   └── event.py           # Domain Event
│   │
│   ├── application/           # Application Layer
│   │   ├── __init__.py
│   │   ├── handler.py         # Command/Query Handler
│   │   └── dto.py             # Application DTO
│   │
│   ├── adapter/               # Infrastructure Layer (connects to external systems)
│   │   ├── __init__.py
│   │   ├── repository.py      # Repository implementation (DB persistence)
│   │   ├── schema.py          # ORM Schema
│   │   ├── mapper.py          # Entity ↔ Schema mapping
│   │   ├── message_publisher.py   # Message Queue (RabbitMQ, Kafka, SQS)
│   │   ├── message_consumer.py    # Message Queue consumer
│   │   ├── storage.py         # Object Storage (S3, GCS, Azure Blob)
│   │   ├── cache.py           # Cache (Redis, Memcached)
│   │   ├── search.py          # Search Engine (Elasticsearch, OpenSearch)
│   │   └── external_api.py    # External HTTP API clients
│   │
│   └── entrypoint/            # Presentation Layer
│       ├── __init__.py
│       ├── api.py             # REST API (FastAPI Router)
│       └── schema.py          # Request/Response Schema
│
├── common/                    # Shared modules
│   ├── repository.py          # Base Repository
│   └── pagination.py          # Common utilities
│
└── dependency/                # DI Container
    └── container.py
```

```python
# 1. Domain Layer - Pure business logic, no external dependencies

# domain/model.py
import datetime
from typing import Self
import pydantic

class Order(pydantic.BaseModel):
    """Domain Entity - pure Python, no framework dependencies"""
    model_config = pydantic.ConfigDict(frozen=True)

    id: str
    customer_id: str
    items: tuple[OrderItem, ...]
    status: OrderStatus

    @classmethod
    def pending(cls, customer_id: str, items: list[OrderItem]) -> Self:
        ...

    def confirm(self) -> Self:
        ...

# domain/repository.py
from typing import Protocol

class OrderRepository(Protocol):
    """Repository interface - defined in Domain Layer"""

    async def find_by_id(self, order_id: str) -> Order | None:
        ...

    async def save(self, order: Order) -> None:
        ...

# domain/service.py
class PricingService:
    """Domain Service - pure business logic"""

    def calculate_total(self, items: list[OrderItem], customer: Customer) -> Money:
        ...
```

```python
# 2. Application Layer - Use case orchestration

# application/handler.py
class ConfirmOrderHandler:
    """Application Service (Handler) - use case orchestration"""

    def __init__(
        self,
        order_repository: OrderRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._order_repository = order_repository
        self._event_publisher = event_publisher

    async def handle(self, command: ConfirmOrderCommand) -> Order:
        # 1. Retrieve
        order = await self._order_repository.find_by_id(command.order_id)
        if order is None:
            raise NotFoundError(f"Order not found: {command.order_id}")

        # 2. Execute domain logic
        confirmed = order.confirm()

        # 3. Save
        await self._order_repository.save(confirmed)

        # 4. Publish event
        await self._event_publisher.publish(
            OrderConfirmedEvent(order_id=confirmed.id)
        )

        return confirmed

# application/dto.py
class ConfirmOrderCommand(pydantic.BaseModel):
    """Command DTO"""
    order_id: str
```

```python
# 3. Infrastructure Layer - Technical implementation

# adapter/schema.py
import sqlalchemy

class OrderSchema(Base):
    """ORM Schema - exists only in Infrastructure"""
    __tablename__ = "orders"
    id = Column(String, primary_key=True)
    customer_id = Column(String, nullable=False)
    status = Column(String, nullable=False)

# adapter/repository.py
class SQLAlchemyOrderRepository:
    """Repository implementation - Infrastructure Layer"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, order_id: str) -> Order | None:
        query = sqlalchemy.select(OrderSchema).where(OrderSchema.id == order_id)
        result = await self._session.execute(query)
        record = result.scalar_one_or_none()
        return OrderMapper.to_entity(record) if record else None

    async def save(self, order: Order) -> None:
        record = OrderMapper.to_record(order)
        await self._session.merge(record)

# adapter/mapper.py
class OrderMapper:
    """Entity ↔ Schema conversion"""

    @staticmethod
    def to_entity(record: OrderSchema) -> Order:
        ...

    @staticmethod
    def to_record(entity: Order) -> OrderSchema:
        ...
```

```python
# 4. Presentation Layer - External interface

# entrypoint/api.py
import http

from fastapi import APIRouter, Depends, HTTPException, Path
from dependency_injector.wiring import inject, Provide

router = APIRouter(prefix="/orders", tags=["order"])


# FastAPI router decorator: specify description, dependencies, responses beyond URL and response
# Use http.HTTPStatus constants instead of raw numbers for status codes
@router.post(
    "/{order_id}/confirm",
    response_model=OrderResponse,
    status_code=http.HTTPStatus.OK,
    summary="Confirm order",
    description="Change pending order to confirmed state. Cannot confirm already confirmed or cancelled orders.",
    responses={
        http.HTTPStatus.OK: {"description": "Order confirmation successful"},
        http.HTTPStatus.NOT_FOUND: {"description": "Order not found", "model": ErrorResponse},
        http.HTTPStatus.CONFLICT: {"description": "Order state cannot be confirmed", "model": ErrorResponse},
    },
)
@inject
async def confirm_order(
    order_id: str = Path(..., description="Order ID to confirm", example="order_abc123"),
    handler: ConfirmOrderHandler = Depends(
        Provide[Container.order.handler.confirm_order_handler]
    ),
) -> OrderResponse:
    command = ConfirmOrderCommand(order_id=order_id)
    order = await handler.handle(command)
    return OrderResponse.from_entity(order)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order",
    description="Retrieve order details by order ID.",
    responses={
        http.HTTPStatus.OK: {"description": "Order retrieval successful"},
        http.HTTPStatus.NOT_FOUND: {"description": "Order not found", "model": ErrorResponse},
    },
)
@inject
async def get_order(
    order_id: str = Path(..., description="Order ID to retrieve"),
    handler: GetOrderHandler = Depends(
        Provide[Container.order.handler.get_order_handler]
    ),
) -> OrderResponse:
    query = GetOrderQuery(order_id=order_id)
    order = await handler.handle(query)
    if order is None:
        raise HTTPException(
            status_code=http.HTTPStatus.NOT_FOUND,
            detail=f"Order not found: {order_id}",
        )
    return OrderResponse.from_entity(order)


@router.post(
    "/",
    response_model=OrderIdResponse,
    status_code=http.HTTPStatus.CREATED,
    summary="Create order",
    description="Create new order. Requires at least one product.",
    responses={
        http.HTTPStatus.CREATED: {"description": "Order creation successful"},
        http.HTTPStatus.BAD_REQUEST: {"description": "Invalid request", "model": ErrorResponse},
        http.HTTPStatus.UNPROCESSABLE_ENTITY: {"description": "Validation failed", "model": ValidationErrorResponse},
    },
)
@inject
async def create_order(
    request: CreateOrderRequest,
    workspace_id: str = Header(..., alias="X-Workspace-Id", description="Workspace ID"),
    handler: CreateOrderHandler = Depends(
        Provide[Container.order.handler.create_order_handler]
    ),
) -> OrderIdResponse:
    command = CreateOrderCommand(
        workspace_id=workspace_id,
        customer_id=request.customer_id,
        items=request.items,
    )
    order = await handler.handle(command)
    return OrderIdResponse(id=order.id)


# entrypoint/schema.py
class OrderResponse(pydantic.BaseModel):
    """API Response Schema"""
    id: str = pydantic.Field(..., description="Order ID", example="order_abc123")
    status: str = pydantic.Field(..., description="Order status", example="confirmed")
    total: int = pydantic.Field(..., description="Order total (KRW)", example=50000)

    model_config = pydantic.ConfigDict(
        json_schema_extra={
            "example": {
                "id": "order_abc123",
                "status": "confirmed",
                "total": 50000,
            }
        }
    )

    @classmethod
    def from_entity(cls, order: Order) -> Self:
        return cls(id=order.id, status=order.status.value, total=order.total.amount)


class ErrorResponse(pydantic.BaseModel):
    """Error response schema"""
    detail: str = pydantic.Field(..., description="Error message")
    code: str = pydantic.Field(..., description="Error code")
```

```python
# Dependency direction (allowed/forbidden)

# ✅ Allowed: upper → lower
# entrypoint/api.py
from src.order.application import handler  # Presentation → Application
from src.order.domain import model          # Presentation → Domain

# application/handler.py
from src.order.domain import model, repository  # Application → Domain

# ❌ Forbidden: lower → upper
# domain/model.py
from src.order.adapter import schema  # Domain → Infrastructure (forbidden!)
from src.order.entrypoint import api  # Domain → Presentation (forbidden!)

# ❌ Forbidden: Domain depends on framework
# domain/model.py
from fastapi import HTTPException  # Forbidden!
from sqlalchemy import Column      # Forbidden!
```

```python
# Data flow between layers

# Request → Presentation → Application → Domain → Infrastructure
#                                                       ↓
# Response ← Presentation ← Application ← Domain ← Infrastructure

# 1. API Request (Presentation)
@router.post("/orders")
async def create_order(request: CreateOrderRequest) -> OrderResponse:
    # 2. Convert Command (Presentation → Application)
    command = CreateOrderCommand(
        customer_id=request.customer_id,
        items=request.items,
    )

    # 3. Execute Handler (Application)
    order = await handler.handle(command)

    # 4. Convert Response (Application → Presentation)
    return OrderResponse.from_entity(order)
```

## Exceptions

- In microservices, layers can be simplified when modules are small
- In CQRS, Read Model can have relaxed layer separation
- In prototype/MVP, prioritize rapid development
