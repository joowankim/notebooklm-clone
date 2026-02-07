---
paths:
  - "**/domain/**/*.py"
  - "**/model.py"
  - "**/models/*.py"
---

# DDD Domain Service

## Principle (Why)

Domain Service **contains domain logic that doesn't belong to a specific Entity**.

- Logic spanning multiple Aggregates is difficult to put in Entity
- Domain concepts with stateless operations are suitable for Services
- Separates responsibilities without making Entities bloated
- Expresses calculation or policy logic as explicit domain concepts
- Distinct from Application Service: Domain Service has pure domain logic only

## Rules (What)

1. **Stateless** - Results determined by input only, no instance variables
2. **Name with domain terms** - Use business terms, not technical terms
3. **Use when coordinating multiple Aggregates** - When single Entity can't solve it
4. **No infrastructure dependencies** - No direct DB or external API calls
5. **Located in domain layer** - Don't confuse with Application Service
6. **Use specific names** - Avoid `~Service`, `~Handler`, use names that clearly reveal role

## Examples (How)

### Naming: Use specific names

```python
# BAD: Generic suffixes like ~Service, ~Handler
class PricingService: ...      # Unclear what it does
class OrderService: ...        # Too broad scope
class PaymentHandler: ...      # Technical term

# GOOD: Names that clearly reveal role
class PriceCalculator: ...     # Price "calculation"
class DiscountPolicy: ...      # Discount "policy"
class ShippingCostEstimator: ...  # Shipping cost "estimation"
class InventoryAllocator: ...  # Inventory "allocation"
class FundTransfer: ...        # Fund "transfer"
class TaxCalculator: ...       # Tax "calculation"
class StockCounter: ...        # Stock "counting"
class MemberGradeEvaluator: ... # Grade "evaluation"
class CouponValidator: ...     # Coupon "validation"
class OrderTotalizer: ...      # Order "totalization"

# Naming patterns
# ~Calculator: Calculation logic (PriceCalculator, TaxCalculator)
# ~Policy: Business rules/policies (DiscountPolicy, RefundPolicy)
# ~Allocator: Allocation logic (InventoryAllocator, SeatAllocator)
# ~Validator: Validation logic (CouponValidator, OrderValidator)
# ~Evaluator: Evaluation/judgment (MemberGradeEvaluator, RiskEvaluator)
# ~Counter/Totalizer: Aggregation (StockCounter, OrderTotalizer)
# ~Estimator: Estimation/prediction (ShippingCostEstimator, DeliveryTimeEstimator)
# ~Transfer: Movement/transfer (FundTransfer, OwnershipTransfer)
# ~Matcher: Matching (OrderMatcher, RouteMatcher)
# ~Registry: Registration/lookup (ProductRegistry, PromotionRegistry)
```

### Domain Service examples

```python
# Domain Service with specific names

class PriceCalculator:
    """Price calculator - combines multiple domain objects for calculation"""

    def calculate_order_total(
        self,
        items: list[OrderItem],
        customer: Customer,
        coupon: Coupon | None,
    ) -> Money:
        """Calculate order total: items + member grade discount + coupon"""
        subtotal = self._calculate_subtotal(items)
        member_discount = self._apply_member_discount(subtotal, customer.grade)
        coupon_discount = self._apply_coupon(member_discount, coupon)
        return coupon_discount

    def _calculate_subtotal(self, items: list[OrderItem]) -> Money:
        if not items:
            return Money.krw(0)
        result = items[0].subtotal
        for item in items[1:]:
            result = result.add(item.subtotal)
        return result

    def _apply_member_discount(self, amount: Money, grade: MemberGrade) -> Money:
        discount_rate = grade.discount_rate
        discount = amount.amount * discount_rate // 100
        return Money(amount=amount.amount - discount, currency=amount.currency)

    def _apply_coupon(self, amount: Money, coupon: Coupon | None) -> Money:
        if coupon is None or not coupon.is_valid:
            return amount
        return coupon.apply_to(amount)


class FundTransfer:
    """Fund transfer - operations between two Account Aggregates"""

    def execute(
        self,
        source: Account,
        target: Account,
        amount: Money,
    ) -> tuple[Account, Account]:
        """Transfer amount from source to target"""
        if source.currency != target.currency:
            raise InvalidTransferError("Currency mismatch")

        if not source.can_withdraw(amount):
            raise InsufficientBalanceError(f"Insufficient balance: {source.balance}")

        updated_source = source.withdraw(amount)
        updated_target = target.deposit(amount)

        return updated_source, updated_target


class InventoryAllocator:
    """Inventory allocator - coordinates Order and Inventory Aggregates"""

    def allocate(
        self,
        order: Order,
        available_inventory: list[Inventory],
    ) -> list[Allocation]:
        """Allocate inventory to order items"""
        allocations: list[Allocation] = []

        for item in order.items:
            inventory = self._find_available_inventory(
                item.product_id, item.quantity, available_inventory
            )
            if inventory is None:
                raise OutOfStockError(f"Product {item.product_id} out of stock")

            allocation = Allocation(
                order_id=order.id,
                order_item_id=item.id,
                inventory_id=inventory.id,
                quantity=item.quantity,
            )
            allocations.append(allocation)

        return allocations

    def _find_available_inventory(
        self,
        product_id: str,
        quantity: int,
        inventories: list[Inventory],
    ) -> Inventory | None:
        for inventory in inventories:
            if inventory.product_id == product_id and inventory.available >= quantity:
                return inventory
        return None
```

```python
# Domain Service vs Application Service distinction

# Domain Service: Pure domain logic, no infrastructure dependencies
class PriceCalculator:
    def calculate_total(self, items: list[OrderItem], customer: Customer) -> Money:
        # Pure calculation only - no DB queries
        ...

# Application Service (Handler): Use case orchestration, uses Repository
# Note: Handler is appropriate for Application Layer use case orchestration
#       (different from Domain Service)
class CreateOrderHandler:
    def __init__(
        self,
        order_repository: OrderRepository,
        customer_repository: CustomerRepository,
        price_calculator: PriceCalculator,  # Inject Domain Service
    ) -> None:
        self._order_repository = order_repository
        self._customer_repository = customer_repository
        self._price_calculator = price_calculator

    async def handle(self, command: CreateOrderCommand) -> Order:
        # 1. Retrieve data via Repository (infrastructure)
        customer = await self._customer_repository.find_by_id(command.customer_id)

        # 2. Calculate via Domain Service (domain logic)
        total = self._price_calculator.calculate_total(command.items, customer)

        # 3. Create Entity (domain)
        order = Order.create(
            customer_id=customer.id,
            items=command.items,
            total=total,
        )

        # 4. Save via Repository (infrastructure)
        await self._order_repository.save(order)
        return order
```

```python
# BAD: Domain Service directly uses Repository
class PriceCalculator:
    def __init__(self, product_repository: ProductRepository) -> None:
        self._product_repository = product_repository  # Infrastructure dependency!

    def calculate_total(self, items: list[OrderItem]) -> Money:
        total = Money.krw(0)
        for item in items:
            product = self._product_repository.find_by_id(item.product_id)  # DB call!
            ...

# GOOD: Receive needed data as parameters
class PriceCalculator:
    def calculate_total(
        self,
        items: list[OrderItem],
        products: dict[str, Product],  # Receive needed data
    ) -> Money:
        ...

# BAD: Force awkward logic into Entity
class Order:
    def calculate_shipping_cost(
        self,
        customer: Customer,
        shipping_zones: list[ShippingZone],
    ) -> Money:
        # Order needs to know Customer, ShippingZone - increases coupling
        ...

# GOOD: Separate as Domain Service (specific name)
class ShippingCostEstimator:
    def estimate(
        self,
        order: Order,
        customer: Customer,
        shipping_zones: list[ShippingZone],
    ) -> Money:
        ...
```

## Exceptions

- If logic clearly belongs to one Entity, make it an Entity method
- No Domain Service needed for simple CRUD
- Use Infrastructure Service for external system integration
