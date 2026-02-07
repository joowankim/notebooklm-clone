---
paths:
  - "**/*.py"
---

# Testing

## Principle (Why)

Tests **guarantee code behavior and make changes safe**.

- Refactoring without tests means bugs can go unnoticed
- TDD makes you think about design first, creating better interfaces
- Tests serve as living documentation - showing how code is used
- 80% coverage means core paths have been tested
- Unit/Integration/E2E levels catch different kinds of bugs

## Rules (What)

1. **TDD workflow** - RED(fail) → GREEN(pass) → REFACTOR(improve)
2. **Minimum 80% coverage** - Core business logic should be 100%
3. **Distinguish test levels** - Unit(functions), Integration(API/DB), E2E(user scenarios)
4. **Arrange-Act-Assert pattern** - Clear setup, execution, verification stages
5. **Test isolation** - Each test must be independently executable
6. **Descriptive test names** - `test_create_user_with_duplicate_email_raises_error`
7. **Object-to-object comparison** - Prefer `assert actual == expected` over partial property comparisons

## Examples (How)

```python
import pytest

# Arrange-Act-Assert pattern + object-to-object comparison
class TestUserCreator:
    def test_create_user_with_valid_data_returns_user(self) -> None:
        # Arrange
        repository = MockUserRepository()
        creator = UserCreator(repository)
        expected = User(
            id="generated-id",
            name="John",
            email="john@example.com",
            status=UserStatus.ACTIVE,
        )

        # Act
        actual = creator.create(name="John", email="john@example.com")

        # Assert - object-to-object comparison (GOOD)
        assert actual == expected

    def test_create_user_with_duplicate_email_raises_error(self) -> None:
        # Arrange
        repository = MockUserRepository()
        repository.add(User.create(name="Existing", email="john@example.com"))
        creator = UserCreator(repository)

        # Act & Assert
        with pytest.raises(DuplicateEmailError):
            creator.create(name="John", email="john@example.com")
```

```python
# Using fixtures
@pytest.fixture
def user_repository() -> MockUserRepository:
    return MockUserRepository()

@pytest.fixture
def user_creator(user_repository: MockUserRepository) -> UserCreator:
    return UserCreator(user_repository)

def test_with_fixtures(user_creator: UserCreator) -> None:
    user = user_creator.create(name="Test", email="test@example.com")
    assert user.name == "Test"
```

```python
# Test multiple cases with parametrize
@pytest.mark.parametrize(
    "email,expected_valid",
    [
        ("user@example.com", True),
        ("user@domain.co.kr", True),
        ("invalid-email", False),
        ("@nodomain.com", False),
    ],
)
def test_email_validation(email: str, expected_valid: bool) -> None:
    result = validate_email(email)
    assert result == expected_valid
```

```python
# Integration Test (API)
from fastapi.testclient import TestClient

def test_create_user_api(client: TestClient) -> None:
    response = client.post(
        "/api/v1/users",
        json={"name": "John", "email": "john@example.com"},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "John"

def test_create_user_with_invalid_email_returns_400(client: TestClient) -> None:
    response = client.post(
        "/api/v1/users",
        json={"name": "John", "email": "invalid"},
    )

    assert response.status_code == 400
    assert "email" in response.json()["detail"]
```

```python
# Test isolation
@pytest.fixture(autouse=True)
def reset_database(test_db: Database) -> Generator[None, None, None]:
    yield
    test_db.rollback()
    test_db.clear_all()
```

```python
# Object-to-object comparison (Assert pattern)

# GOOD: Compare entire object - Intent is clear, tests automatically validate when new fields are added
def test_user_creation(self) -> None:
    actual = create_user(name="John", email="john@example.com")
    expected = User(
        id=actual.id,  # Use generated ID
        name="John",
        email="john@example.com",
        status=UserStatus.ACTIVE,
        created_at=actual.created_at,  # Timestamp from actual
    )
    assert actual == expected

# GOOD: DTO/Response object comparison
def test_api_response(self) -> None:
    actual = service.get_user_response(user_id="123")
    expected = UserResponse(
        id="123",
        name="John",
        email="john@example.com",
    )
    assert actual == expected

# BAD: Partial property comparison - Test can miss new fields when added
def test_user_creation_bad(self) -> None:
    user = create_user(name="John", email="john@example.com")
    assert user.name == "John"
    assert user.email == "john@example.com"
    assert user.status == UserStatus.ACTIVE
    # If role field is added, test still passes - potential bug missed

# GOOD: Handling dynamic values (ID, timestamp)
def test_with_dynamic_values(self) -> None:
    actual = create_order(product_id="prod-1", quantity=2)

    # Method 1: Extract dynamic values from actual
    expected = Order(
        id=actual.id,
        product_id="prod-1",
        quantity=2,
        created_at=actual.created_at,
    )
    assert actual == expected

    # Method 2: Verify dynamic values separately then compare rest
    assert actual.id is not None
    assert actual.product_id == "prod-1"
    assert actual.quantity == 2
```

## Exceptions

- Auto-generated code (ORM migrations, etc.)
- Configuration/constant files
- Integration with external systems (actual API calls) - Use mocks
- UI layout tests - Use snapshot tests or visual regression tests
