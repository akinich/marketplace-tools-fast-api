# Backend Technical Guide

**Version:** 1.0.0
**Audience:** Backend Developers, System Architects

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Configuration Management](#configuration-management)
3. [Database Layer](#database-layer)
4. [Authentication System](#authentication-system)
5. [Authorization & Permissions](#authorization--permissions)
6. [API Structure](#api-structure)
7. [Error Handling](#error-handling)
8. [Background Tasks](#background-tasks)
9. [Testing](#testing)

---

## Architecture Overview

### Three-Layer Architecture

```
┌─────────────────────────────────────┐
│      Route Handlers (routes/)       │
│  - Request validation               │
│  - Response serialization           │
│  - Dependency injection             │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Business Logic (services/)     │
│  - Domain logic                     │
│  - Transaction management           │
│  - Error handling                   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Database Layer (database.py)   │
│  - Query execution                  │
│  - Connection pooling               │
│  - Transaction support              │
└─────────────────────────────────────┘
```

### Key Design Principles

- **Async First:** All I/O operations are asynchronous
- **Dependency Injection:** FastAPI's Depends() for clean architecture
- **Type Safety:** Pydantic schemas for validation and serialization
- **Single Responsibility:** Each module has a clear purpose
- **Transaction Consistency:** Use DatabaseTransaction for atomic operations

---

## Configuration Management

### Settings Class

Location: `backend/app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Farm Management System"
    APP_ENV: str = "development"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_MIN: int = 10
    DATABASE_POOL_MAX: int = 50
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**Usage:**
```python
from app.config import settings

# Access configuration
database_url = settings.DATABASE_URL
debug_mode = settings.DEBUG
```

---

## Database Layer

### Connection Management

**Pool Creation:**
```python
import asyncpg

db_pool: asyncpg.Pool = None

async def connect_db():
    global db_pool
    db_pool = await asyncpg.create_pool(
        dsn=settings.DATABASE_URL,
        min_size=settings.DATABASE_POOL_MIN,
        max_size=settings.DATABASE_POOL_MAX,
        statement_cache_size=0  # For Supabase pgbouncer
    )
```

### Query Functions

#### fetch_one(query, *values)

Fetch single row as dictionary.

```python
user = await db.fetch_one(
    "SELECT * FROM user_profiles WHERE id = $1",
    user_id
)
# Returns: {"id": "...", "full_name": "...", ...} or None
```

#### fetch_all(query, *values)

Fetch multiple rows as list of dictionaries.

```python
items = await db.fetch_all(
    "SELECT * FROM items WHERE category = $1",
    "Feed"
)
# Returns: [{"id": 1, "name": "..."}, {...}]
```

#### execute_query(query, *values)

Execute INSERT/UPDATE/DELETE.

```python
# With RETURNING clause
result = await db.execute_query(
    """
    INSERT INTO items (name, sku)
    VALUES ($1, $2)
    RETURNING id
    """,
    "Fish Feed", "FEED-001"
)
# Returns: 123 (single value if one column) or {"id": 123, ...} (dict if multiple)

# Without RETURNING
result = await db.execute_query(
    "UPDATE items SET is_active = $1 WHERE id = $2",
    False, 1
)
# Returns: "UPDATE 1"
```

### Transaction Management

**DatabaseTransaction Context Manager:**

```python
from app.database import DatabaseTransaction

async def create_purchase_order(data):
    async with DatabaseTransaction() as conn:
        # All operations use same connection
        po = await conn.fetch_one(
            "INSERT INTO purchase_orders (...) VALUES (...) RETURNING *",
            ...
        )
        
        for item in data.items:
            await conn.execute(
                "INSERT INTO purchase_order_items (...) VALUES (...)",
                po['id'], item.item_id, item.quantity
            )
        
        # Auto-commits if successful
        # Auto-rollback if exception
        return po
```

**Key Features:**
- Automatic commit on success
- Automatic rollback on exception
- Nested transaction support
- Connection cleanup

---

## Authentication System

### JWT Token Management

Location: `backend/app/auth/jwt.py`

#### create_access_token()

```python
from app.auth.jwt import create_access_token

token = create_access_token(
    user_id="uuid-123",
    email="user@example.com",
    full_name="John Doe",
    role="User"
)
# Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Token Payload:**
```json
{
  "sub": "uuid-123",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "User",
  "type": "access",
  "exp": 1700000000,
  "iat": 1699998200
}
```

#### decode_token() & verify_access_token()

```python
from app.auth.jwt import verify_access_token

payload = verify_access_token(token)
# Returns payload dict or raises HTTPException(401)
```

### Password Management

Location: `backend/app/auth/password.py`

#### hash_password() & verify_password()

```python
from app.auth.password import hash_password, verify_password

# Hash password (12 bcrypt rounds)
hashed = hash_password("SecurePass123!")

# Verify password
is_valid = verify_password("SecurePass123!", hashed)
# Returns: True
```

#### validate_password_strength()

```python
from app.auth.password import validate_password_strength

is_valid, message = validate_password_strength("weak")
# Returns: (False, "Password must be at least 8 characters")

is_valid, message = validate_password_strength("SecurePass123!")
# Returns: (True, "Password is strong")
```

**Requirements:**
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit
- At least 1 special character (!@#$%^&*(),.?":{}|<>)

---

## Authorization & Permissions

### Authentication Dependencies

Location: `backend/app/auth/dependencies.py`

#### get_current_user()

Standard authentication dependency.

```python
from fastapi import Depends
from app.auth.dependencies import get_current_user

@router.get("/protected")
async def protected_endpoint(
    current_user: dict = Depends(get_current_user)
):
    # current_user = {
    #     "id": "uuid",
    #     "email": "...",
    #     "full_name": "...",
    #     "role": "Admin|User",
    #     "role_id": 1,
    #     "is_active": True
    # }
    return {"message": f"Hello {current_user['full_name']}"}
```

**Process:**
1. Extract token from Authorization header
2. Verify and decode token
3. Fetch user from database
4. Check if user is active
5. Return CurrentUser object

**Exceptions:**
- `401` - Missing/invalid/expired token
- `403` - User is inactive

#### require_admin()

Admin-only endpoints.

```python
from app.auth.dependencies import require_admin

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin)
):
    # Only admin users can access this endpoint
    pass
```

**Process:**
1. Calls `get_current_user()`
2. Checks `role == "Admin"`
3. Raises 403 if not admin

#### require_module_access()

Module-specific access control.

```python
from app.auth.dependencies import require_module_access

@router.get("/inventory/items")
async def get_items(
    current_user: dict = Depends(require_module_access("inventory"))
):
    # User must have access to inventory module
    pass
```

**Process:**
1. Calls `get_current_user()`
2. If admin: grants access automatically
3. If user: checks `user_module_permissions` table
4. Raises 403 if no access

---

## API Structure

### Route Organization

Each module has its own route file:

```python
# backend/app/routes/auth.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/login")
async def login(request: LoginRequest):
    ...

@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    ...
```

### Route Registration

In `main.py`:

```python
from app.routes import auth, dashboard, admin, inventory, biofloc

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["Inventory"])
app.include_router(biofloc.router, prefix="/api/v1/biofloc", tags=["Biofloc"])
```

### Request/Response Pattern

**Standard Pattern:**

```python
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.module import CreateRequest, Response
from app.services import module_service
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.post("/items", response_model=Response, status_code=201)
async def create_item(
    request: CreateRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        item = await module_service.create_item(request, current_user["id"])
        return item
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Key Elements:**
- `response_model` - Pydantic schema for response
- `status_code` - HTTP status code for success
- `Depends()` - Dependency injection
- Exception handling with HTTPException

---

## Error Handling

### Global Exception Handlers

**Request Validation Errors (422):**

```python
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": errors}
    )
```

**Generic Exceptions (500):**

```python
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

### Custom Exceptions

**Usage Pattern:**

```python
from fastapi import HTTPException

# 400 Bad Request
raise HTTPException(status_code=400, detail="Invalid input")

# 401 Unauthorized
raise HTTPException(status_code=401, detail="Invalid credentials")

# 403 Forbidden
raise HTTPException(status_code=403, detail="Access denied")

# 404 Not Found
raise HTTPException(status_code=404, detail="Item not found")

# 409 Conflict
raise HTTPException(status_code=409, detail="Item already exists")
```

---

## Background Tasks

### Scheduler Setup

Location: `backend/app/scheduler.py`

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

def start_scheduler():
    """Start background task scheduler."""
    scheduler.add_job(
        expire_inventory_reservations,
        'interval',
        minutes=15,
        id='expire_reservations',
        replace_existing=True
    )
    scheduler.start()

def stop_scheduler():
    """Stop scheduler."""
    if scheduler.running:
        scheduler.shutdown()
```

### Scheduled Jobs

**Expire Inventory Reservations:**

```python
async def expire_inventory_reservations():
    """Expire old inventory reservations every 15 minutes."""
    try:
        result = await db.execute_query(
            "SELECT expire_old_reservations()"
        )
        logger.info(f"Expired {result} reservations")
    except Exception as e:
        logger.error(f"Error expiring reservations: {e}")
```

**Adding New Jobs:**

```python
# In start_scheduler()
scheduler.add_job(
    your_async_function,
    'interval',  # or 'cron', 'date'
    hours=1,  # Run every hour
    id='your_job_id',
    replace_existing=True
)
```

---

## Testing

### Test Structure

```
tests/
├── conftest.py           # Fixtures
├── test_auth.py          # Authentication tests
├── test_database.py      # Database layer tests
└── test_api.py           # API endpoint tests
```

### Example Test

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_login():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "TestPass123!"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
```

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_auth.py

# With coverage
pytest --cov=app tests/

# Verbose
pytest -v
```

---

## Best Practices

### 1. Always Use Parameterized Queries

```python
# Good
result = await db.fetch_one(
    "SELECT * FROM users WHERE email = $1",
    email
)

# Bad (SQL injection risk)
result = await db.fetch_one(
    f"SELECT * FROM users WHERE email = '{email}'"
)
```

### 2. Use Transactions for Multi-Step Operations

```python
async with DatabaseTransaction() as conn:
    # Multiple related operations
    await conn.execute(...)
    await conn.execute(...)
```

### 3. Validate Input with Pydantic

```python
from pydantic import BaseModel, EmailStr, Field

class CreateUserRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    role_id: int = Field(..., gt=0)
```

### 4. Use Dependency Injection

```python
# Reusable dependencies
async def get_item_or_404(item_id: int):
    item = await db.fetch_one("SELECT * FROM items WHERE id = $1", item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    return item

@router.get("/items/{item_id}")
async def get_item(item: dict = Depends(get_item_or_404)):
    return item
```

### 5. Log Errors Properly

```python
import logging

logger = logging.getLogger(__name__)

try:
    result = await operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise HTTPException(500, "Operation failed")
```

---

## Performance Tips

### 1. Use Connection Pooling

Already configured via asyncpg pool (10-50 connections).

### 2. Optimize Queries

```python
# Use SELECT only needed columns
await db.fetch_all("SELECT id, name FROM items")  # Good
await db.fetch_all("SELECT * FROM items")  # Less efficient
```

### 3. Add Pagination

```python
@router.get("/items")
async def get_items(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100)
):
    offset = (page - 1) * limit
    items = await db.fetch_all(
        "SELECT * FROM items LIMIT $1 OFFSET $2",
        limit, offset
    )
    return items
```

### 4. Use Async Everywhere

```python
# Good - concurrent
results = await asyncio.gather(
    db.fetch_one(...),
    db.fetch_all(...),
    external_api_call()
)

# Bad - sequential
result1 = await db.fetch_one(...)
result2 = await db.fetch_all(...)
result3 = await external_api_call()
```

---

**End of Technical Guide**

For API conventions and patterns, see [API Guide](./api-guide.md).
