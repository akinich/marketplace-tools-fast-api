# Marketplace ERP - Backend API

**Version: 1.0.0** | **Last Updated: 2025-11-17**

FastAPI backend with JWT authentication, admin panel, and inventory management.

## Tech Stack

- **FastAPI 0.104+** - Modern async web framework
- **Python 3.11+** - Programming language
- **asyncpg** - Async PostgreSQL driver
- **Pydantic v2** - Data validation
- **python-jose** - JWT token handling
- **bcrypt** - Password hashing
- **uvicorn** - ASGI server

## Features

### Authentication System
- JWT-based authentication with access + refresh tokens
- Password hashing with bcrypt (12 rounds)
- Auto token refresh
- Password reset flow
- Role-based access control (RBAC)

### Admin Panel APIs
- User management (CRUD)
- Permission management
- Activity logs with filtering
- Statistics dashboard
- **19 endpoints total**

### Inventory Module APIs
- Item master management
- Stock operations with FIFO cost tracking
- Purchase order management
- Supplier and category management
- Low stock alerts
- Expiry alerts
- Transaction history
- **23 endpoints total**

### Dashboard APIs
- Farm-wide KPI summary
- User accessible modules
- Real-time statistics

## API Endpoints

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/login` | Login with email/password | No |
| POST | `/logout` | Logout current user | Yes |
| POST | `/refresh` | Refresh access token | No |
| POST | `/request-password-reset` | Request password reset email | No |
| POST | `/verify-reset-token` | Verify reset token validity | No |
| POST | `/reset-password` | Reset password with token | No |

### Dashboard (`/api/v1/dashboard`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/summary` | Farm-wide KPIs and metrics | Yes |
| GET | `/modules` | User accessible modules | Yes |

### Admin Panel (`/api/v1/admin`)

#### Users
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/users` | List all users | Admin |
| POST | `/users` | Create new user | Admin |
| PUT | `/users/{user_id}` | Update user | Admin |
| DELETE | `/users/{user_id}` | Delete user | Admin |
| GET | `/users/{user_id}` | Get user details | Admin |

#### Permissions
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/permissions/{user_id}` | Get user permissions | Admin |
| PUT | `/permissions/{user_id}` | Update user permissions | Admin |
| GET | `/modules` | List all modules | Admin |
| GET | `/roles` | List all roles | Admin |

#### Activity Logs
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/activity-logs` | Get activity logs with filters | Admin |

#### Statistics
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/statistics` | Admin dashboard statistics | Admin |

### Inventory (`/api/v1/inventory`)

#### Items
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/items` | List inventory items | Inventory |
| POST | `/items` | Create new item | Inventory |
| PUT | `/items/{item_id}` | Update item | Inventory |
| DELETE | `/items/{item_id}` | Delete item | Inventory |

#### Stock Operations
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/stock/add` | Add stock to item | Inventory |
| POST | `/stock/use` | Use stock (FIFO deduction) | Inventory |
| GET | `/stock/batches/{item_id}` | Get item batches | Inventory |

#### Purchase Orders
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/purchase-orders` | List POs with filters | Inventory |
| POST | `/purchase-orders` | Create new PO | Inventory |
| GET | `/purchase-orders/{po_id}` | Get PO details | Inventory |
| PUT | `/purchase-orders/{po_id}` | Update PO | Inventory |
| DELETE | `/purchase-orders/{po_id}` | Delete PO | Inventory |
| PUT | `/purchase-orders/{po_id}/status` | Update PO status | Inventory |

#### Suppliers & Categories
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/suppliers` | List suppliers | Inventory |
| POST | `/suppliers` | Create supplier | Inventory |
| GET | `/categories` | List categories | Inventory |
| POST | `/categories` | Create category | Inventory |

#### Alerts
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/alerts/low-stock` | Items below reorder threshold | Inventory |
| GET | `/alerts/expiry` | Items expiring soon | Inventory |

#### Transactions
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/transactions` | Transaction history with filters | Inventory |

## Project Structure

```
backend/
├── app/
│   ├── auth/                    # Authentication module
│   │   ├── dependencies.py      # Route protection decorators
│   │   ├── jwt.py              # JWT token creation/verification
│   │   └── password.py         # Password hashing
│   ├── routes/                  # API route handlers
│   │   ├── auth.py             # Auth endpoints
│   │   ├── dashboard.py        # Dashboard endpoints
│   │   ├── admin.py            # Admin panel endpoints
│   │   └── inventory.py        # Inventory endpoints
│   ├── services/                # Business logic layer
│   │   ├── auth_service.py     # Auth logic
│   │   ├── admin_service.py    # Admin panel logic
│   │   └── inventory_service.py # Inventory logic
│   ├── schemas/                 # Pydantic models
│   │   ├── auth.py             # Auth request/response models
│   │   ├── dashboard.py        # Dashboard models
│   │   ├── admin.py            # Admin panel models
│   │   └── inventory.py        # Inventory models
│   ├── config.py               # Configuration management
│   ├── database.py             # Database connection & helpers
│   └── main.py                 # FastAPI app & startup
├── requirements.txt             # Python dependencies
└── .env.example                # Environment template
```

## Configuration

### Environment Variables

Required variables in `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-min-32-characters
JWT_REFRESH_SECRET_KEY=your-refresh-secret-key-min-32-characters
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend.com

# Email (for password reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@farm-system.com
```

### Generate Secret Keys

```bash
# Generate JWT secret keys
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Installation

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Setup Database

Run the schema script from `sql_scripts/v1.0.0_initial_schema.sql` on your PostgreSQL database.

### 5. Run Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

Server will start at http://localhost:8000

## API Documentation

When server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Authentication Flow

### Login Process

1. Client sends POST to `/api/v1/auth/login` with email/password
2. Backend validates credentials
3. Backend generates access token (30 min) and refresh token (7 days)
4. Backend logs activity
5. Returns tokens + user info

### Token Refresh

1. Client sends POST to `/api/v1/auth/refresh` with refresh token
2. Backend validates refresh token
3. Backend generates new access token
4. Returns new access token

### Protected Routes

```python
from app.auth.dependencies import get_current_user, require_admin, require_module_access

# Require any authenticated user
@router.get("/profile")
async def get_profile(current_user: CurrentUser = Depends(get_current_user)):
    return current_user

# Require admin role
@router.get("/admin/users")
async def list_users(current_user: CurrentUser = Depends(require_admin)):
    return await admin_service.get_all_users()

# Require specific module access
@router.get("/inventory/items")
async def list_items(
    current_user: CurrentUser = Depends(require_module_access("inventory"))
):
    return await inventory_service.get_items()
```

## Business Logic Highlights

### FIFO Stock Deduction

When using stock, the system automatically:
1. Fetches available batches ordered by purchase date (oldest first)
2. Deducts from oldest batches first
3. Calculates weighted average cost
4. Updates batch quantities
5. Logs transactions
6. Returns cost breakdown

**Example:**
```python
# Use 100 units of item
result = await inventory_service.use_stock_fifo(
    UseStockRequest(
        item_master_id=1,
        quantity=100,
        transaction_type="Usage",
        remarks="Production use"
    ),
    user_id="user-123",
    username="John Doe"
)

# Returns:
{
    "success": True,
    "quantity_used": 100,
    "batches_used": [
        {"batch_number": "B001", "qty_used": 60, "cost": 300},
        {"batch_number": "B002", "qty_used": 40, "cost": 220}
    ],
    "total_cost": 520,
    "weighted_avg_cost": 5.20,
    "new_balance": 450
}
```

### Auto-Update Triggers

Database triggers automatically:
- Update `item_master.current_qty` when batches change
- Calculate `purchase_orders.total_cost` when PO items change
- Maintain data integrity

### Activity Logging

All sensitive operations are logged:
- User login/logout
- User creation/update/deletion
- Permission changes
- Stock operations
- PO creation/updates

## Database Helpers

The `database.py` module provides async helpers:

```python
from app.database import fetch_one, fetch_all, execute_query

# Fetch single row
user = await fetch_one(
    "SELECT * FROM user_profiles WHERE id = $1",
    user_id
)

# Fetch multiple rows
users = await fetch_all(
    "SELECT * FROM user_profiles WHERE is_active = $1",
    True
)

# Execute query (INSERT/UPDATE/DELETE)
await execute_query(
    "UPDATE user_profiles SET full_name = $1 WHERE id = $2",
    new_name,
    user_id
)
```

## Error Handling

All endpoints use consistent error responses:

```json
{
  "detail": "Error message here"
}
```

HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad request / validation error
- `401` - Unauthorized (invalid/expired token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not found
- `500` - Internal server error

## Performance Optimization

### Purchase Orders List
- Optimized with JOINs to avoid N+1 queries
- Single query execution (<200ms target)
- Pagination ready (limit/offset)

### Database Indexes
- Created on foreign keys
- Created on frequently queried columns
- Created on date/timestamp columns

### Connection Pooling
- asyncpg connection pool (10-20 connections)
- Automatic connection management
- Graceful shutdown

## Security Features

1. **Password Hashing**: bcrypt with 12 rounds
2. **JWT Tokens**: Signed with HS256, short expiry
3. **CORS**: Whitelist-based origin validation
4. **SQL Injection**: Parameterized queries only
5. **Input Validation**: Pydantic models validate all inputs
6. **Role-Based Access**: Module permissions per user
7. **Activity Logging**: Audit trail for sensitive operations

## Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

## Deployment

### Production Checklist

- [ ] Set strong JWT secret keys (32+ characters)
- [ ] Use production DATABASE_URL
- [ ] Set ALLOWED_ORIGINS to frontend URL only
- [ ] Enable HTTPS only
- [ ] Set up email SMTP for password reset
- [ ] Configure proper logging
- [ ] Set up monitoring (e.g., Sentry)
- [ ] Use gunicorn with multiple workers:
  ```bash
  gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
  ```

### Render Deployment

See main [README.md](../README.md) for detailed Render deployment instructions.

Quick command for Render:
```bash
# Build Command
pip install -r requirements.txt

# Start Command
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Troubleshooting

### Database Connection Issues
- Check DATABASE_URL format: `postgresql+asyncpg://user:pass@host:port/db`
- For Supabase: Use "Transaction" pooler for better performance
- Verify network access (firewall, security groups)

### CORS Errors
- Add frontend URL to ALLOWED_ORIGINS in .env
- Ensure no trailing slashes in origins
- Restart backend after changing ALLOWED_ORIGINS

### 500 Internal Server Error
- Check server logs for detailed error
- Verify database schema is up to date
- Check all environment variables are set

### Token Issues
- Verify JWT_SECRET_KEY is set and consistent
- Check token expiry settings
- Ensure clock sync between client/server

## Future Enhancements

- [ ] Biofloc module APIs
- [ ] WebSocket support for real-time notifications
- [ ] File upload for item images
- [ ] Export to Excel endpoints
- [ ] Advanced filtering with query builder
- [ ] Rate limiting
- [ ] API versioning
- [ ] GraphQL support

## Changelog

### v1.0.0 (2025-11-17)
- Initial FastAPI backend implementation
- JWT authentication with refresh tokens
- Admin panel APIs (19 endpoints)
- Inventory module APIs (23 endpoints)
- Dashboard APIs
- FIFO stock deduction logic
- Activity logging system
- Role-based access control

## License

Proprietary - Farm Management System v1.0.0
