# API Development Guide

**Version:** 1.0.0
**Audience:** API Developers

---

## API Conventions

### URL Structure

```
/api/{version}/{module}/{resource}/{id?}/{action?}
```

**Examples:**
- `GET /api/v1/inventory/items` - List items
- `GET /api/v1/inventory/items/123` - Get specific item
- `POST /api/v1/inventory/stock/add` - Add stock (action)
- `POST /api/v1/biofloc/batches/grading` - Grading action

### HTTP Methods

- `GET` - Retrieve resources (list or single)
- `POST` - Create new resources
- `PUT` - Update existing resources (full update)
- `PATCH` - Partial update (not commonly used)
- `DELETE` - Delete/deactivate resources

### Status Codes

**Success:**
- `200 OK` - Successful GET, PUT, DELETE
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE (no body)

**Client Errors:**
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing/invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource doesn't exist
- `409 Conflict` - Duplicate resource
- `422 Unprocessable Entity` - Validation errors

**Server Errors:**
- `500 Internal Server Error` - Unhandled exception

---

## Request/Response Patterns

### Standard List Endpoint

```python
@router.get("/items", response_model=ItemListResponse)
async def get_items(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    offset = (page - 1) * limit
    
    # Build query
    query = "SELECT * FROM items WHERE 1=1"
    params = []
    
    if category is not None:
        query += f" AND category = ${len(params) + 1}"
        params.append(category)
    
    if is_active is not None:
        query += f" AND is_active = ${len(params) + 1}"
        params.append(is_active)
    
    # Get total count
    count_query = f"SELECT COUNT(*) FROM items WHERE 1=1 ..."
    total = await db.fetch_val(count_query, *params)
    
    # Add pagination
    query += f" LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
    params.extend([limit, offset])
    
    items = await db.fetch_all(query, *params)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit
    }
```

**Response Schema:**
```python
class ItemListResponse(BaseModel):
    items: List[Item]
    total: int
    page: int
    limit: int
```

### Standard Create Endpoint

```python
@router.post("/items", response_model=Item, status_code=201)
async def create_item(
    request: CreateItemRequest,
    current_user: dict = Depends(get_current_user)
):
    # Validate unique constraints
    existing = await db.fetch_one(
        "SELECT id FROM items WHERE sku = $1",
        request.sku
    )
    if existing:
        raise HTTPException(409, "Item with this SKU already exists")
    
    # Create item
    item = await db.fetch_one(
        """
        INSERT INTO items (item_name, sku, category, created_by)
        VALUES ($1, $2, $3, $4)
        RETURNING *
        """,
        request.item_name, request.sku, request.category, current_user["id"]
    )
    
    return item
```

### Standard Update Endpoint

```python
@router.put("/items/{item_id}", response_model=Item)
async def update_item(
    item_id: int,
    request: UpdateItemRequest,
    current_user: dict = Depends(get_current_user)
):
    # Check if item exists
    item = await db.fetch_one("SELECT * FROM items WHERE id = $1", item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    
    # Update fields
    item = await db.fetch_one(
        """
        UPDATE items
        SET item_name = $1, category = $2, updated_at = NOW()
        WHERE id = $3
        RETURNING *
        """,
        request.item_name, request.category, item_id
    )
    
    return item
```

### Standard Delete Endpoint

```python
@router.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    current_user: dict = Depends(get_current_user)
):
    # Soft delete
    result = await db.execute_query(
        "UPDATE items SET is_active = FALSE WHERE id = $1",
        item_id
    )
    
    if result == "UPDATE 0":
        raise HTTPException(404, "Item not found")
    
    return {"message": "Item deleted successfully"}
```

---

## Pydantic Schema Patterns

### Request Schema

```python
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import date

class CreateItemRequest(BaseModel):
    item_name: str = Field(..., min_length=1, max_length=255)
    sku: str = Field(..., min_length=1, max_length=100)
    category: str
    unit: str = Field(..., max_length=50)
    reorder_threshold: Optional[float] = Field(None, ge=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "item_name": "Fish Feed Pellets 3mm",
                "sku": "FEED-PELLET-3MM",
                "category": "Feed",
                "unit": "kg",
                "reorder_threshold": 500.0
            }
        }
```

### Response Schema

```python
from datetime import datetime

class Item(BaseModel):
    id: int
    item_name: str
    sku: str
    category: str
    unit: str
    current_qty: float
    reorder_threshold: Optional[float]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True  # Allows ORM models
```

---

## Error Handling Patterns

### Service Layer

```python
# backend/app/services/inventory_service.py

async def create_item(request, user_id):
    # Validation
    if await item_exists_by_sku(request.sku):
        raise ValueError(f"Item with SKU {request.sku} already exists")
    
    try:
        # Business logic
        item = await db.fetch_one(...)
        return item
    except Exception as e:
        logger.error(f"Error creating item: {e}", exc_info=True)
        raise
```

### Route Handler

```python
# backend/app/routes/inventory.py

@router.post("/items")
async def create_item(request: CreateItemRequest, current_user: dict = Depends(get_current_user)):
    try:
        item = await inventory_service.create_item(request, current_user["id"])
        return item
    except ValueError as e:
        # Business logic errors
        raise HTTPException(400, str(e))
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(500, "An error occurred")
```

---

## Authentication Patterns

### Public Endpoint

```python
@router.post("/login")
async def login(request: LoginRequest):
    # No authentication required
    ...
```

### Protected Endpoint

```python
@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    # Requires authentication
    return current_user
```

### Admin-Only Endpoint

```python
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin)
):
    # Only admins can access
    ...
```

### Module-Specific Endpoint

```python
@router.get("/inventory/items")
async def get_items(current_user: dict = Depends(require_module_access("inventory"))):
    # Requires inventory module access
    ...
```

---

## Query Building Patterns

### Dynamic WHERE Clauses

```python
def build_where_clause(filters: dict) -> tuple:
    """Build WHERE clause from filters."""
    conditions = []
    params = []
    param_count = 1
    
    for key, value in filters.items():
        if value is not None:
            conditions.append(f"{key} = ${param_count}")
            params.append(value)
            param_count += 1
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    return where_clause, params

# Usage
filters = {"category": "Feed", "is_active": True}
where, params = build_where_clause(filters)
query = f"SELECT * FROM items WHERE {where}"
items = await db.fetch_all(query, *params)
```

### Pagination Helper

```python
def paginate_query(query: str, page: int, limit: int) -> tuple:
    """Add pagination to query."""
    offset = (page - 1) * limit
    paginated_query = f"{query} LIMIT {limit} OFFSET {offset}"
    return paginated_query, limit, offset
```

---

## Testing Patterns

### Test Fixture

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def auth_headers(client):
    # Login and get token
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "TestPass123!"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

### Endpoint Test

```python
@pytest.mark.asyncio
async def test_create_item(client, auth_headers):
    response = await client.post(
        "/api/v1/inventory/items",
        json={
            "item_name": "Test Item",
            "sku": "TEST-001",
            "category": "Test",
            "unit": "kg"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["item_name"] == "Test Item"
    assert data["sku"] == "TEST-001"
```

---

## Best Practices Checklist

### API Design
- [ ] Use RESTful conventions
- [ ] Version your API (/api/v1)
- [ ] Use appropriate HTTP methods
- [ ] Return correct status codes
- [ ] Include pagination on list endpoints
- [ ] Validate all inputs with Pydantic
- [ ] Document with docstrings

### Security
- [ ] Require authentication where needed
- [ ] Use parameterized queries
- [ ] Validate permissions
- [ ] Log sensitive operations
- [ ] Don't expose internal errors to users
- [ ] Rate limit endpoints (future)

### Performance
- [ ] Use async/await everywhere
- [ ] Implement connection pooling
- [ ] Add database indexes
- [ ] Paginate large result sets
- [ ] Cache frequently accessed data (future)

### Error Handling
- [ ] Handle exceptions at service layer
- [ ] Return user-friendly error messages
- [ ] Log errors with context
- [ ] Don't leak sensitive information

### Testing
- [ ] Write tests for all endpoints
- [ ] Test authentication/authorization
- [ ] Test error cases
- [ ] Test edge cases

---

**End of API Guide**
