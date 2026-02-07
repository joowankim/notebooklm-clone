---
paths:
  - "**/*.py"
---

# Naming Conventions

## Principle (Why)

Good names make **code self-documenting**.

- Names should reveal role and intention at a glance
- Consistent naming makes codebase navigation easier
- Abbreviations are understood only by the author, not others
- Duplicating type information in names causes mismatches during refactoring
- Vague names (`data`, `info`) convey no information

## Rules (What)

1. **Style consistency** - Modules/functions/variables use `snake_case`, classes/types use `PascalCase`, constants use `SCREAMING_SNAKE_CASE`
2. **Use descriptive names** - `user_count` instead of `cnt`, specific purpose instead of `tmp`
3. **Function names start with verbs** - `create_user`, `find_by_id`, `validate_email`
4. **Booleans use is/has/can/should prefix** - `is_active`, `has_permission`
5. **Collections use plural form** - `users`, `order_items`, `user_ids`
6. **Avoid reserved word conflicts** - Use `item_list`, `user_type`, `user_id` instead of `list`, `type`, `id`
7. **Repository query methods** - Single results use `find_` prefix, multiple results use `list_` prefix, grouped dict results use `group_` prefix

## Examples (How)

```python
# Style guide
class UserService:              # Class: PascalCase
    MAX_RETRY_COUNT: ClassVar[int] = 3         # Constant: SCREAMING_SNAKE_CASE

    def create_user(self) -> User:      # Function: snake_case
        user_count = 0                   # Variable: snake_case
        return User()

# Function naming patterns
def create_user() -> User: ...          # Create
def update_order() -> Order: ...        # Update
def delete_product() -> None: ...       # Delete
def find_user_by_id() -> User | None: ... # Query

# Boolean returns
def is_active() -> bool: ...
def has_permission() -> bool: ...
def can_process() -> bool: ...
def should_retry() -> bool: ...

# Conversion functions
def to_dict() -> dict[str, str]: ...
def from_json() -> User: ...
def as_response() -> UserResponse: ...
```

```python
# GOOD: Descriptive names
user_count = len(users)
is_authenticated = token is not None
max_retry_attempts = 3

# BAD: Abbreviations, vague names
cnt = len(users)
auth = token is not None
n = 3
data = fetch()
info = get_info()
```

```python
# GOOD: Avoid reserved word conflicts
item_list: list[Item] = []
user_type = "admin"
user_id = "123"

# BAD: Shadowing built-in functions/types
list = [1, 2, 3]  # Shadows built-in list!
type = "user"     # Shadows built-in type!
id = 123          # Shadows built-in id!
```

```python
# Collection naming
users: list[User] = []              # Plural form
order_items: list[OrderItem] = []
user_ids: set[str] = set()

# Mappings
user_by_id: dict[str, User] = {}    # _by_ pattern
email_to_user: dict[str, User] = {} # _to_ pattern
```

```python
# Repository query method naming
class UserRepository:
    # Single result: find_ prefix (returns: Entity | None)
    async def find_by_id(self, user_id: str) -> User | None:
        ...

    async def find_by_email(self, email: str) -> User | None:
        ...

    async def find_by_phone(self, phone: str) -> User | None:
        ...

    # Multiple results: list_ prefix (returns: list[Entity])
    async def list_by_group_id(self, group_id: str) -> list[User]:
        ...

    async def list_by_status(self, status: UserStatus) -> list[User]:
        ...

    async def list_active(self) -> list[User]:
        ...

    # Grouped results: group_ prefix (returns: dict[key, list[Entity]])
    async def group_by_room_ids(self, room_ids: list[str]) -> dict[str, list[Tag]]:
        ...

    async def group_by_status(self, user_ids: list[str]) -> dict[UserStatus, list[User]]:
        ...

# BAD: Inconsistent naming
async def get_user(user_id: str) -> User | None: ...  # Should be find_by_id
async def fetch_users_by_group(group_id: str) -> list[User]: ...  # Should be list_by_group_id
async def search_by_email(email: str) -> User | None: ...  # Should be find_by_email
async def find_by_room_ids(room_ids: list[str]) -> dict[str, list[Tag]]: ...  # Should be group_by_room_ids
```

## Exceptions

- Conventionally short variables: `i`, `j` (loops), `e`/`exc` (exceptions), `_` (ignored)
- Conventional symbols in mathematical/scientific domains
- Names defined by external APIs or protocols
