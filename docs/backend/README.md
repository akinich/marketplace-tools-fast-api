# Backend Core Architecture

**Framework:** FastAPI 0.104.1
**Python Version:** 3.8+
**Database:** PostgreSQL (via Supabase)
**Status:** Production Ready ✅

## Overview

The Marketplace ERP Tools backend is built on FastAPI, a modern, high-performance Python web framework. It provides a robust, scalable foundation with comprehensive authentication, authorization, database management, and API structure for all farm management modules.

### Key Capabilities

- **JWT Authentication** - Secure token-based authentication with access and refresh tokens
- **Role-Based Access Control** - Admin and User roles with module-level permissions
- **Async Database Operations** - High-performance asyncpg driver with connection pooling
- **Module System** - Extensible architecture for farm management modules
- **Activity Logging** - Complete audit trail of all system actions
- **Background Tasks** - Scheduled jobs for automated operations
- **Password Management** - Bcrypt hashing with strength validation
- **Error Handling** - Comprehensive exception handling with detailed responses
- **CORS Support** - Configurable cross-origin resource sharing
- **API Documentation** - Auto-generated Swagger UI and ReDoc

## Quick Start

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12+ (Supabase instance)
- pip or poetry for package management

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd farm2-app-fast-api/backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations:**
   ```bash
   # Connect to your PostgreSQL database
   psql -h <host> -U <user> -d <database> -f sql_scripts/v1.0.0_initial_schema.sql
   ```

6. **Start the development server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

7. **Access the application:**
   - API: http://localhost:8000
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application setup
│   ├── config.py               # Configuration management
│   ├── database.py             # Database connection and utilities
│   ├── scheduler.py            # Background task scheduler
│   │
│   ├── auth/                   # Authentication system
│   │   ├── jwt.py             # JWT token management
│   │   ├── password.py        # Password hashing and validation
│   │   └── dependencies.py    # Auth dependencies
│   │
│   ├── routes/                 # API route handlers
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── dashboard.py       # Dashboard endpoints
│   │   ├── admin.py           # Admin module routes
│   │   ├── inventory.py       # Inventory module routes
│   │   └── biofloc.py         # Biofloc module routes
│   │
│   ├── schemas/                # Pydantic models
│   │   ├── auth.py            # Auth request/response models
│   │   ├── dashboard.py       # Dashboard models
│   │   ├── admin.py           # Admin models
│   │   ├── inventory.py       # Inventory models
│   │   └── biofloc.py         # Biofloc models
│   │
│   ├── services/               # Business logic layer
│   │   ├── auth_service.py    # Authentication logic
│   │   ├── admin_service.py   # Admin operations
│   │   ├── inventory_service.py
│   │   └── biofloc_service.py
│   │
│   └── helpers/                # Utility functions
│       └── inventory_integration.py
│
├── sql_scripts/                # Database migrations
│   └── v1.0.0_initial_schema.sql
│
├── tests/                      # Test suite
│   ├── test_auth.py
│   └── test_api.py
│
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
└── README.md                  # This file
```

## Core Components

### 1. FastAPI Application

The main application (`main.py`) provides:
- **Lifespan Management:** Startup/shutdown hooks for database and scheduler
- **Middleware:** Request logging with duration tracking
- **CORS:** Configurable cross-origin support
- **Exception Handlers:** Global error handling
- **Health Check:** Database and scheduler status monitoring

**Key Endpoints:**
- `GET /` - Welcome message and system info
- `GET /health` - Health check with component status
- `GET /ping` - Simple uptime check

### 2. Configuration Management

Environment-based configuration using Pydantic Settings:

**Key Settings:**
- Application: Name, environment, debug mode
- Database: Connection URL, pool size
- JWT: Secret keys, token expiration times
- Security: Bcrypt rounds, rate limiting
- Supabase: URL and service key for email
- CORS: Allowed origins

See [Technical Guide](./technical-guide.md) for complete configuration reference.

### 3. Authentication System

**Features:**
- JWT-based authentication with access and refresh tokens
- Password hashing with bcrypt (12 rounds)
- Password strength validation
- Token refresh mechanism
- Password reset flow via email
- Activity logging for security audit

**Token Structure:**
- **Access Token:** 30-minute expiration, includes user info
- **Refresh Token:** 7-day expiration, used to obtain new access tokens

**Endpoints:**
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/forgot-password` - Request password reset
- `POST /api/v1/auth/reset-password` - Reset with token
- `GET /api/v1/auth/me` - Get current user info

### 4. Authorization & Permissions

**Role-Based Access Control (RBAC):**
- **Admin Role:** Full system access
- **User Role:** Access based on granted module permissions

**Module-Level Permissions:**
- Fine-grained access control per module (inventory, biofloc, etc.)
- Admins bypass permission checks
- Users require explicit grants via `user_module_permissions` table

**Dependencies:**
- `get_current_user()` - Authenticates and returns user
- `require_admin()` - Restricts to admin users only
- `require_module_access(module_key)` - Checks module permission

### 5. Database Layer

**Technology:** asyncpg (async PostgreSQL driver)

**Features:**
- Connection pooling (10-50 connections)
- Parameterized queries for SQL injection prevention
- Transaction support with context managers
- Query utilities (fetch_one, fetch_all, execute_query)
- Health check monitoring

**Query Patterns:**
```python
# Fetch single row
user = await db.fetch_one("SELECT * FROM users WHERE id = $1", user_id)

# Fetch multiple rows
items = await db.fetch_all("SELECT * FROM items WHERE category = $1", category)

# Execute with transaction
async with DatabaseTransaction() as conn:
    await conn.execute("INSERT INTO ...")
    await conn.execute("UPDATE ...")
    # Auto-commits if successful, rolls back on error
```

### 6. Background Tasks

**Scheduler:** APScheduler with AsyncIOScheduler

**Scheduled Jobs:**
- `expire_inventory_reservations()` - Every 15 minutes
  - Expires pending stock reservations past their deadline

**Lifecycle:**
- Started at application startup
- Stopped at application shutdown
- Status available via `/health` endpoint

### 7. API Structure

**Base URL:** `/api/v1`

**Route Organization:**
```
/api/v1
├── /auth          # Authentication endpoints
├── /dashboard     # Dashboard summary and modules
├── /admin         # Admin module (user/role/permission management)
├── /inventory     # Inventory module (stock, POs, suppliers)
└── /biofloc       # Biofloc module (aquaculture operations)
```

**Response Patterns:**
- **Success:** HTTP 200/201 with data
- **Client Error:** HTTP 400/401/403/404/422 with `{"detail": "..."}`
- **Server Error:** HTTP 500 with `{"detail": "Internal server error"}`

### 8. Error Handling

**Global Exception Handlers:**
- **ValidationError (422):** Detailed field-level errors
- **HTTPException:** Custom errors with status codes
- **Generic Exception (500):** Logged with traceback

**Common Error Responses:**
- `401 Unauthorized` - Invalid/expired token, missing credentials
- `403 Forbidden` - Insufficient permissions, inactive account
- `404 Not Found` - Resource doesn't exist
- `422 Unprocessable Entity` - Validation errors

## Technology Stack

### Core Framework
- **FastAPI 0.104.1** - Web framework
- **Uvicorn 0.24.0** - ASGI server
- **Pydantic 2.11.7** - Data validation

### Database
- **asyncpg 0.29.0** - PostgreSQL driver
- **PostgreSQL 12+** - Database (via Supabase)

### Authentication & Security
- **python-jose 3.3.0** - JWT tokens
- **bcrypt 4.1.2** - Password hashing
- **supabase 2.24.0** - Email integration

### Background Tasks
- **APScheduler 3.10.4** - Task scheduling

### Data Processing
- **pandas 2.1.3** - Data manipulation
- **xlsxwriter 3.1.9** - Excel export
- **openpyxl 3.1.2** - Excel operations

### Testing
- **pytest 7.4.3** - Test framework
- **pytest-asyncio 0.21.1** - Async test support

## Environment Variables

Create a `.env` file in the backend directory:

```env
# Application
APP_NAME=Marketplace ERP Tools
APP_ENV=development
DEBUG=True
API_VERSION=v1

# Database
DATABASE_URL=postgresql://user:password@host:port/database

# JWT
JWT_SECRET_KEY=your-super-secret-key-here
JWT_REFRESH_SECRET_KEY=your-refresh-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Frontend
FRONTEND_URL=http://localhost:3000
```

## Development

### Running the Development Server

```bash
# Standard mode
uvicorn app.main:app --reload --port 8000

# With custom host and port
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# With log level
uvicorn app.main:app --reload --log-level debug
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

### Code Formatting & Linting

```bash
# Format code with black
black app/

# Lint with ruff
ruff check app/

# Type checking (if using mypy)
mypy app/
```

## API Documentation

### Swagger UI
Access interactive API documentation at:
- http://localhost:8000/docs

Features:
- Try out API endpoints
- View request/response schemas
- Authentication support

### ReDoc
Alternative documentation at:
- http://localhost:8000/redoc

Features:
- Clean, readable documentation
- Detailed schema descriptions
- Code samples

### OpenAPI JSON
Raw OpenAPI specification:
- http://localhost:8000/openapi.json

## Security Considerations

### Authentication Security
- JWT tokens with short expiration (30 min access, 7 day refresh)
- Bcrypt password hashing with 12 rounds
- Password strength validation (8+ chars, uppercase, lowercase, digit, special)
- Token validation on every request

### Authorization Security
- Role-based access control (RBAC)
- Module-level permissions
- Admin-only endpoints protected
- Cannot self-delete (prevents admin lockout)

### Database Security
- Parameterized queries (SQL injection prevention)
- Connection pooling for performance
- Row-level security policies (Supabase)

### API Security
- CORS configuration
- Request rate limiting
- Input validation with Pydantic
- Error messages don't leak sensitive info

### Activity Logging
- All admin actions logged
- User attribution on all operations
- Complete audit trail for compliance

## Performance Optimization

### Database
- Connection pooling (10-50 connections)
- Async queries for concurrency
- Indexed columns for fast lookups
- Query optimization with EXPLAIN ANALYZE

### API
- Async request handlers
- Pagination on list endpoints (default 50/page)
- Selective field queries (only fetch needed data)
- Response caching for read-heavy endpoints

### Background Tasks
- Non-blocking scheduled jobs
- Separate thread for scheduler
- Error handling to prevent job failures

## Monitoring & Health Checks

### Health Check Endpoint
`GET /health`

Returns:
```json
{
  "status": "healthy",
  "database": "connected",
  "scheduler": "running",
  "jobs": 1,
  "timestamp": "2025-11-19T10:00:00"
}
```

### Logging
- Request logging with duration
- Error logging with stack traces
- Configurable log level (DEBUG, INFO, WARNING, ERROR)
- Structured logging for parsing

## Documentation

- **[Technical Guide](./technical-guide.md)** - Detailed architecture, database schema, API reference
- **[API Guide](./api-guide.md)** - API conventions, patterns, and best practices

## Common Operations

### Adding a New Module

1. Create route handler in `routes/`
2. Define Pydantic schemas in `schemas/`
3. Implement business logic in `services/`
4. Register route in `main.py`
5. Add module to database `modules` table
6. Grant permissions to users

### Adding a New Endpoint

1. Define schema models (request/response)
2. Create route handler function
3. Add authentication dependency if needed
4. Implement business logic
5. Test with pytest
6. Document in docstring

### Database Migrations

1. Write SQL migration script in `sql_scripts/`
2. Name with version: `vX.Y.Z_description.sql`
3. Test on development database
4. Apply to production with backup
5. Update version in config

## Troubleshooting

### Cannot Connect to Database
- Verify `DATABASE_URL` in `.env`
- Check database is running
- Verify network connectivity
- Check firewall rules

### 401 Unauthorized Errors
- Verify token is being sent in Authorization header
- Check token hasn't expired
- Ensure user is active
- Verify JWT secret keys match

### Module Access Denied
- Check user has permission for module
- Verify module is active
- Check parent module is enabled (for child modules)

### Background Jobs Not Running
- Check scheduler started in `/health`
- Verify APScheduler installed
- Check logs for scheduler errors
- Ensure no blocking operations in jobs

## Contributing

1. Follow Python PEP 8 style guide
2. Use type hints for all functions
3. Write tests for new features
4. Update documentation
5. Format with black before committing
6. Run tests before submitting PR

## Support

For issues and questions:
- Check documentation in `docs/backend/`
- Review code comments in source files
- Check GitHub issues
- Contact development team

## License

Part of the Marketplace ERP Tools
© 2025 All rights reserved
