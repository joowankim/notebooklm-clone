---
paths:
  - "**/repository/**/*.py"
  - "**/repositories/**/*.py"
  - "**/adapter/**/*.py"
  - "**/infrastructure/**/*.py"
---

# DDD Repository

## Principle (Why)

Repository is **a collection interface that abstracts Aggregate persistence**.

- Isolates domain layer from infrastructure (DB, ORM) dependencies
- Allows treating Aggregates like in-memory collections
- Easy to replace with Mock Repository for testing
- Changes to persistence implementation don't affect domain logic
- Centralizes query logic for consistency

## Rules (What)

1. **One Repository per Aggregate Root** - No separate Repository for internal Entities
2. **Interface in domain layer** - Implementation in infrastructure layer
3. **Query method naming** - Single: `find_`, Multiple: `list_`
4. **Return domain Entity** - Return domain model, not ORM Schema
5. **Convert with Mapper** - Entity ↔ Schema conversion inside Repository
6. **Manage transactions with Unit of Work** - Multiple Repository changes in one transaction

## Examples (How)

```python
import abc
from typing import Protocol

# Domain layer: Repository interface

class OrderRepository(Protocol):
    """Repository interface - located in domain layer"""

    async def find_by_id(self, order_id: str) -> Order | None:
        """Single query: find_ prefix"""
        ...

    async def find_by_customer_and_status(
        self, customer_id: str, status: OrderStatus
    ) -> Order | None:
        ...

    async def list_by_customer_id(self, customer_id: str) -> list[Order]:
        """Multiple query: list_ prefix"""
        ...

    async def list_by_status(self, status: OrderStatus) -> list[Order]:
        ...

    async def list_pending_orders(self) -> list[Order]:
        ...

    async def save(self, order: Order) -> None:
        """Save (insert or update)"""
        ...

    async def delete(self, order: Order) -> None:
        """Delete"""
        ...
```

```python
# Infrastructure layer: Repository implementation

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

class SQLAlchemyOrderRepository:
    """Repository implementation - located in infrastructure layer"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._mapper = OrderMapper()

    async def find_by_id(self, order_id: str) -> Order | None:
        query = (
            sqlalchemy.select(OrderSchema)
            .where(OrderSchema.id == order_id)
            .options(sqlalchemy.orm.selectinload(OrderSchema.items))
        )
        result = await self._session.execute(query)
        record = result.scalar_one_or_none()

        if record is None:
            return None
        return self._mapper.to_entity(record)

    async def list_by_customer_id(self, customer_id: str) -> list[Order]:
        query = (
            sqlalchemy.select(OrderSchema)
            .where(OrderSchema.customer_id == customer_id)
            .options(sqlalchemy.orm.selectinload(OrderSchema.items))
            .order_by(OrderSchema.created_at.desc())
        )
        result = await self._session.execute(query)
        records = result.scalars().all()

        return [self._mapper.to_entity(record) for record in records]

    async def save(self, order: Order) -> None:
        record = self._mapper.to_record(order)
        await self._session.merge(record)
        await self._session.flush()

    async def delete(self, order: Order) -> None:
        query = sqlalchemy.delete(OrderSchema).where(OrderSchema.id == order.id)
        await self._session.execute(query)
```

```python
# Mapper: Entity ↔ Schema conversion

class OrderMapper:
    """Conversion between domain Entity and ORM Schema"""

    def to_entity(self, record: OrderSchema) -> Order:
        items = tuple(
            OrderItem(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=Money(amount=item.unit_price, currency=item.currency),
            )
            for item in record.items
        )
        return Order(
            id=record.id,
            customer_id=record.customer_id,
            items=items,
            status=OrderStatus(record.status),
            created_at=record.created_at,
        )

    def to_record(self, entity: Order) -> OrderSchema:
        return OrderSchema(
            id=entity.id,
            customer_id=entity.customer_id,
            status=entity.status.value,
            created_at=entity.created_at,
            items=[
                OrderItemSchema(
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

```python
# Mock Repository for testing

class MockOrderRepository:
    """In-memory Mock Repository"""

    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}

    async def find_by_id(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    async def list_by_customer_id(self, customer_id: str) -> list[Order]:
        return [
            order for order in self._orders.values()
            if order.customer_id == customer_id
        ]

    async def save(self, order: Order) -> None:
        self._orders[order.id] = order

    async def delete(self, order: Order) -> None:
        self._orders.pop(order.id, None)

    # Test helpers
    def add(self, order: Order) -> None:
        self._orders[order.id] = order

    def clear(self) -> None:
        self._orders.clear()
```

```python
# BAD: Repository returns ORM Schema
class OrderRepository:
    async def find_by_id(self, order_id: str) -> OrderSchema | None:  # Returns Schema
        ...

# GOOD: Repository returns domain Entity
class OrderRepository:
    async def find_by_id(self, order_id: str) -> Order | None:  # Returns Entity
        ...

# BAD: Separate Repository for internal Entity
class OrderItemRepository:  # No Repository for internal Entity in Aggregate
    async def find_by_id(self, item_id: str) -> OrderItem | None:
        ...

# BAD: Inconsistent method naming
class OrderRepository:
    async def get_order(self, order_id: str) -> Order | None: ...  # Should be find_by_id
    async def fetch_by_customer(self, customer_id: str) -> list[Order]: ...  # Should be list_by_customer_id
```

```python
# Unit of Work: Transaction boundary management
from typing import Protocol, Self

class UnitOfWork(Protocol):
    """Interface for managing transaction boundaries - located in domain layer"""

    order_repository: OrderRepository
    customer_repository: CustomerRepository

    async def __aenter__(self) -> Self: ...
    async def __aexit__(self, *args) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...


# SQLAlchemy implementation - Session has built-in change tracking
class SQLAlchemyUnitOfWork:
    """SQLAlchemy-based Unit of Work"""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self.order_repository = SQLAlchemyOrderRepository(self._session)
        self.customer_repository = SQLAlchemyCustomerRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self.rollback()
        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()


# MongoDB implementation - Manual change tracking
class MongoUnitOfWork:
    """MongoDB-based Unit of Work - manually tracks changes"""

    def __init__(self, client: AsyncIOMotorClient) -> None:
        self._client = client
        self._new: list[tuple[str, Entity]] = []      # (collection, entity)
        self._dirty: list[tuple[str, Entity]] = []
        self._removed: list[tuple[str, str]] = []     # (collection, id)

    async def __aenter__(self) -> Self:
        self._session = await self._client.start_session()
        self._new.clear()
        self._dirty.clear()
        self._removed.clear()
        self.order_repository = MongoOrderRepository(self)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self.rollback()
        await self._session.end_session()

    def register_new(self, collection: str, entity: Entity) -> None:
        self._new.append((collection, entity))

    def register_dirty(self, collection: str, entity: Entity) -> None:
        self._dirty.append((collection, entity))

    def register_removed(self, collection: str, entity_id: str) -> None:
        self._removed.append((collection, entity_id))

    async def commit(self) -> None:
        async with self._session.start_transaction():
            db = self._client.get_database()
            for collection, entity in self._new:
                await db[collection].insert_one(entity.model_dump(), session=self._session)
            for collection, entity in self._dirty:
                await db[collection].replace_one(
                    {"_id": entity.id}, entity.model_dump(), session=self._session
                )
            for collection, entity_id in self._removed:
                await db[collection].delete_one({"_id": entity_id}, session=self._session)

    async def rollback(self) -> None:
        self._new.clear()
        self._dirty.clear()
        self._removed.clear()
```

```python
# Unit of Work usage example (in Handler)

class TransferFundsHandler:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def handle(self, command: TransferFundsCommand) -> None:
        async with self._uow_factory() as uow:
            source = await uow.account_repository.find_by_id(command.source_id)
            target = await uow.account_repository.find_by_id(command.target_id)

            # Execute domain logic
            updated_source = source.withdraw(command.amount)
            updated_target = target.deposit(command.amount)

            # Save in same transaction
            await uow.account_repository.save(updated_source)
            await uow.account_repository.save(updated_target)
            await uow.commit()
```

## Exceptions

- In CQRS, Read Model can use separate Query Repository
- Introduce Specification pattern for complex search/filtering
- Add streaming/pagination methods for bulk data processing
