# Admin Module - Technical Guide

**Version:** 1.5.0
**Audience:** Developers, System Architects, Database Administrators

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Database Schema](#database-schema)
3. [API Reference](#api-reference)
4. [Service Layer Logic](#service-layer-logic)
5. [Frontend Architecture](#frontend-architecture)
6. [Security & Permissions](#security--permissions)
7. [Performance Considerations](#performance-considerations)
8. [Integration Points](#integration-points)

---

## System Architecture

### Three-Tier Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (React)                │
│  - Material-UI Components               │
│  - React Query for State                │
│  - Form Validation                      │
│  - Notistack Notifications              │
└──────────────┬──────────────────────────┘
               │ REST API (HTTP/JSON)
┌──────────────▼──────────────────────────┐
│         Backend (FastAPI)               │
│  - Route Handlers                       │
│  - Service Layer                        │
│  - Pydantic Validation                  │
│  - RBAC Enforcement                     │
│  - Activity Logging                     │
└──────────────┬──────────────────────────┘
               │ asyncpg (async)
┌──────────────▼──────────────────────────┐
│       Database (PostgreSQL)             │
│  - Relational Data                      │
│  - Views for Permissions                │
│  - Indexes for Performance              │
│  - RLS (Row-Level Security)             │
└─────────────────────────────────────────┘
```

### Module Structure

**Backend:**
```
backend/app/
├── routes/admin.py          # API endpoints (279 lines)
├── schemas/admin.py         # Pydantic models (309 lines)
├── services/admin_service.py # Business logic (879 lines)
├── auth/
│   └── dependencies.py      # Auth/authz (290 lines)
└── main.py                  # FastAPI app setup
```

**Frontend:**
```
frontend/src/
├── pages/
│   └── AdminPanel.jsx       # All admin pages (988 lines, v1.4.0)
├── api/
│   └── index.js            # API client with adminAPI
└── App.jsx                 # Routing configuration
```

---

## Database Schema

### Entity Relationship Overview

```
roles ──< user_profiles >──┬── user_module_permissions >── modules
                           │
                           └── activity_logs
```

### Core Tables

#### 1. `roles`

Defines available system roles.

```sql
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Initial data
INSERT INTO roles (role_name, description) VALUES
    ('Admin', 'Full system access'),
    ('User', 'Limited access based on permissions');
```

**Fields:**
- `id` - Auto-incrementing identifier
- `role_name` - "Admin" or "User"
- `description` - Human-readable explanation
- `created_at` - When role was created

**Key Constraints:**
- Unique role_name (prevents duplicates)
- Cannot delete roles if users assigned

---

#### 2. `user_profiles`

Stores user information and status.

```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES roles(id) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Fields:**
- `id` - UUID from Supabase auth.users (one-to-one)
- `full_name` - User's display name
- `role_id` - FK to roles table
- `is_active` - Soft delete flag (TRUE = active, FALSE = deactivated)
- `created_at` - Account creation timestamp
- `updated_at` - Last modification timestamp

**Relationships:**
- References `auth.users(id)` - Supabase authentication
- References `roles(id)` - User's role

**Key Indexes:**
- `idx_user_profiles_role` - Fast role filtering
- `idx_user_profiles_active` - Active user queries

**Triggers:**
```sql
-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_user_profiles_updated_at
BEFORE UPDATE ON user_profiles
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

---

#### 3. `modules`

Defines system modules with hierarchical structure.

```sql
CREATE TABLE modules (
    id SERIAL PRIMARY KEY,
    module_key VARCHAR(50) UNIQUE NOT NULL,
    module_name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    parent_module_id INTEGER REFERENCES modules(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Fields:**
- `id` - Auto-incrementing identifier
- `module_key` - Unique programmatic key (e.g., "inventory", "biofloc")
- `module_name` - Display name (e.g., "Inventory Management")
- `description` - Detailed explanation
- `icon` - Icon name or emoji for UI
- `display_order` - Sort order in UI (ascending)
- `is_active` - Module enabled/disabled status
- `parent_module_id` - FK to self for hierarchy
- `created_at` - When module was created

**Hierarchical Structure:**
```
Aquaculture (parent_module_id = NULL)
  ├─ Biofloc (parent_module_id = Aquaculture.id)
  ├─ Hatchery (parent_module_id = Aquaculture.id)
  └─ Nursery (parent_module_id = Aquaculture.id)
```

**Key Constraints:**
- Unique module_key
- Self-referencing FK for parent-child
- Cannot delete parent if children exist

**Key Indexes:**
- `idx_modules_key` - Fast key lookup
- `idx_modules_active` - Active module queries
- `idx_modules_parent` - Hierarchy traversal

---

#### 4. `user_module_permissions`

Maps users to modules they can access.

```sql
CREATE TABLE user_module_permissions (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE NOT NULL,
    module_id INTEGER REFERENCES modules(id) ON DELETE CASCADE NOT NULL,
    can_access BOOLEAN DEFAULT TRUE,
    granted_by UUID REFERENCES user_profiles(id),
    granted_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, module_id)
);
```

**Fields:**
- `id` - Auto-incrementing identifier
- `user_id` - FK to user_profiles
- `module_id` - FK to modules
- `can_access` - Permission flag (always TRUE in practice)
- `granted_by` - Admin who granted permission
- `granted_at` - When permission was granted

**Key Constraints:**
- Unique (user_id, module_id) - prevents duplicate grants
- CASCADE delete - removes permissions when user/module deleted

**Key Indexes:**
- `idx_user_module_permissions_user` - User permission queries
- `idx_user_module_permissions_module` - Module impact queries

---

#### 5. `activity_logs`

Complete audit trail of all administrative actions.

```sql
CREATE TABLE activity_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES user_profiles(id),
    user_email VARCHAR(255),
    user_role VARCHAR(50),
    action_type VARCHAR(100) NOT NULL,
    module_key VARCHAR(50),
    description TEXT NOT NULL,
    metadata JSONB,
    success BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Fields:**
- `id` - Auto-incrementing identifier
- `user_id` - FK to user_profiles (who performed action)
- `user_email` - Denormalized email for easier querying
- `user_role` - Denormalized role at time of action
- `action_type` - Type of action performed
- `module_key` - Affected module (if applicable)
- `description` - Human-readable description
- `metadata` - Additional context in JSON format
- `success` - TRUE if action succeeded, FALSE if failed
- `created_at` - Timestamp of action

**Action Types:**
```
- login
- logout
- create_user
- update_user
- delete_user
- update_permissions
- enable_module
- disable_module
- view_activity_logs
- view_statistics
```

**Metadata Examples:**
```json
// User creation
{
  "user_id": "uuid",
  "email": "user@example.com",
  "role": "User"
}

// Permission update
{
  "user_id": "uuid",
  "modules_granted": ["inventory", "biofloc"],
  "modules_count": 2
}

// Module disable
{
  "module_id": 5,
  "module_key": "biofloc",
  "children_disabled": ["biofloc_feeding", "biofloc_sampling"],
  "users_affected": 12
}
```

**Key Indexes:**
- `idx_activity_logs_user` - User activity queries
- `idx_activity_logs_module` - Module activity queries
- `idx_activity_logs_action` - Action type filtering
- `idx_activity_logs_created_at` - Date range queries

**Performance Optimization:**
```sql
CREATE INDEX idx_activity_logs_user ON activity_logs(user_id, created_at DESC);
CREATE INDEX idx_activity_logs_module ON activity_logs(module_key, created_at DESC);
CREATE INDEX idx_activity_logs_action ON activity_logs(action_type, created_at DESC);
```

---

### Database Views

#### 1. `user_details`

Combines user, profile, and role information.

```sql
CREATE VIEW user_details AS
SELECT
    u.id,
    u.email,
    u.created_at as auth_created_at,
    u.last_sign_in_at,
    up.full_name,
    up.is_active,
    up.created_at as profile_created_at,
    up.updated_at,
    r.id as role_id,
    r.role_name,
    r.description as role_description
FROM auth.users u
LEFT JOIN user_profiles up ON u.id = up.id
LEFT JOIN roles r ON up.role_id = r.id;
```

**Purpose:**
- Simplifies user queries
- Single source for user information
- Includes authentication metadata

**Usage:**
```sql
SELECT * FROM user_details
WHERE is_active = TRUE
ORDER BY full_name;
```

---

#### 2. `user_accessible_modules`

Shows modules accessible to each user (respects RBAC).

```sql
CREATE VIEW user_accessible_modules AS
SELECT DISTINCT
    up.id as user_id,
    up.full_name,
    r.role_name,
    m.id as module_id,
    m.module_key,
    m.module_name,
    m.parent_module_id,
    m.is_active as module_is_active,
    CASE
        WHEN r.role_name = 'Admin' THEN TRUE
        WHEN ump.can_access IS NOT NULL THEN ump.can_access
        ELSE FALSE
    END as can_access
FROM user_profiles up
CROSS JOIN modules m
LEFT JOIN roles r ON up.role_id = r.id
LEFT JOIN user_module_permissions ump
    ON up.id = ump.user_id AND m.id = ump.module_id
WHERE up.is_active = TRUE
  AND m.is_active = TRUE;
```

**Purpose:**
- Determines user access per module
- Enforces RBAC: admins get all, users get granted
- Filters inactive users and modules

**Logic:**
- Admin users: can_access = TRUE for ALL modules
- Regular users: can_access based on user_module_permissions
- Only shows active users and active modules

---

### Database Triggers & Functions

#### 1. Auto-update `updated_at`

Automatically sets `updated_at` timestamp on record updates.

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_user_profiles_updated_at
BEFORE UPDATE ON user_profiles
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

---

#### 2. Cascade Disable Modules

When parent module is disabled, automatically disable children.

```sql
CREATE OR REPLACE FUNCTION cascade_disable_child_modules()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_active = FALSE AND OLD.is_active = TRUE THEN
        -- Disable all child modules
        UPDATE modules
        SET is_active = FALSE
        WHERE parent_module_id = NEW.id AND is_active = TRUE;

        -- Remove permissions for disabled modules
        DELETE FROM user_module_permissions
        WHERE module_id IN (
            SELECT id FROM modules
            WHERE parent_module_id = NEW.id OR id = NEW.id
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_cascade_disable_modules
AFTER UPDATE ON modules
FOR EACH ROW
WHEN (OLD.is_active IS DISTINCT FROM NEW.is_active)
EXECUTE FUNCTION cascade_disable_child_modules();
```

**Purpose:**
- Maintains hierarchy integrity
- Prevents orphaned child modules
- Automatic permission cleanup

---

## API Reference

### Base URL
```
/api/v1/admin
```

### Authentication
All endpoints require:
- Valid JWT token in `Authorization: Bearer <token>` header
- User must have "Admin" role
- Enforced by `require_admin` dependency

---

### User Management Endpoints

#### `GET /users`
Get list of users with optional filters.

**Query Parameters:**
- `is_active` (optional): boolean - Filter by active status
- `role` (optional): string - Filter by role name
- `page` (default: 1): integer - Page number
- `limit` (default: 50, max: 100): integer - Items per page

**Response:**
```json
{
  "users": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "John Doe",
      "role_id": 2,
      "role_name": "User",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00",
      "last_sign_in_at": "2025-11-19T08:30:00"
    }
  ],
  "total": 25,
  "page": 1,
  "limit": 50
}
```

**Backend Implementation:**
```python
@router.get("/users", response_model=UserListResponse)
async def get_users(
    is_active: bool = None,
    role: str = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_admin)
):
    return await admin_service.get_users(is_active, role, page, limit)
```

---

#### `POST /users`
Create new user account.

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "full_name": "Jane Smith",
  "role_id": 2
}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "newuser@example.com",
  "full_name": "Jane Smith",
  "role_id": 2,
  "role_name": "User",
  "is_active": true,
  "temporary_password": "TempPass123!",
  "created_at": "2025-11-19T10:00:00"
}
```

**Backend Logic:**
1. Validate email uniqueness
2. Validate role exists
3. Generate temporary password (format: `TempPassXXX!`)
4. Hash password using bcrypt
5. Create auth.users entry
6. Create user_profiles entry
7. Log activity
8. Return user + temp password

**Password Generation:**
```python
def generate_temp_password() -> str:
    """Generate random temporary password."""
    import random
    import string

    chars = string.ascii_letters + string.digits
    password = ''.join(random.choices(chars, k=8))
    return f"TempPass{password}!"
```

---

#### `PUT /users/{user_id}`
Update existing user.

**Path Parameters:**
- `user_id`: UUID - User to update

**Request Body:**
```json
{
  "full_name": "John Smith Jr.",
  "role_id": 1,
  "is_active": false
}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Smith Jr.",
  "role_id": 1,
  "role_name": "Admin",
  "is_active": false,
  "updated_at": "2025-11-19T10:30:00"
}
```

**Validations:**
- User must exist
- Email cannot be changed
- All fields optional

---

#### `DELETE /users/{user_id}`
Deactivate user (soft delete).

**Path Parameters:**
- `user_id`: UUID - User to deactivate

**Response:**
```json
{
  "message": "User deactivated successfully"
}
```

**Backend Logic:**
1. Validate user exists
2. Prevent self-deletion (current_user.id != user_id)
3. Set `is_active = FALSE` (soft delete)
4. Log activity
5. Return success message

**Security:**
- Cannot delete self (prevents admin lockout)
- Preserves audit trail
- Permissions automatically hidden (view filters inactive users)

---

### Role Management Endpoints

#### `GET /roles`
Get list of all available roles.

**Response:**
```json
{
  "roles": [
    {
      "id": 1,
      "role_name": "Admin",
      "description": "Full system access",
      "created_at": "2025-01-01T00:00:00"
    },
    {
      "id": 2,
      "role_name": "User",
      "description": "Limited access based on permissions",
      "created_at": "2025-01-01T00:00:00"
    }
  ]
}
```

---

### Module Management Endpoints

#### `GET /modules`
Get list of all modules with hierarchical structure.

**Response:**
```json
{
  "modules": [
    {
      "id": 1,
      "module_key": "dashboard",
      "module_name": "Dashboard",
      "description": "System dashboard and overview",
      "icon": "dashboard",
      "display_order": 1,
      "is_active": true,
      "parent_module_id": null,
      "created_at": "2025-01-01T00:00:00"
    },
    {
      "id": 5,
      "module_key": "biofloc",
      "module_name": "Biofloc Management",
      "description": "Biofloc aquaculture operations",
      "icon": "water",
      "display_order": 10,
      "is_active": true,
      "parent_module_id": 4,
      "created_at": "2025-01-01T00:00:00"
    }
  ]
}
```

**Note:** Frontend organizes into parent-child tree structure.

---

#### `PUT /modules/{module_id}`
Update module status or display order.

**Path Parameters:**
- `module_id`: integer - Module to update

**Request Body:**
```json
{
  "is_active": false,
  "display_order": 20
}
```

**Response:**
```json
{
  "id": 5,
  "module_key": "biofloc",
  "module_name": "Biofloc Management",
  "is_active": false,
  "display_order": 20,
  "parent_module_id": 4
}
```

**Backend Validations:**
1. **Critical Module Protection:**
   - Cannot disable dashboard (module_key = "dashboard")
   - Cannot disable admin (module_key = "admin")
   - Returns 400 error if attempted

2. **Parent-Child Validation:**
   - If enabling child, check parent is enabled
   - If disabling parent, auto-disable children (via trigger)

3. **Cascading Disable:**
   - When parent disabled, all children disabled
   - All permissions for parent + children removed

**Example Error:**
```json
{
  "detail": "Cannot disable critical module: dashboard"
}
```

---

#### `GET /modules/{module_id}/users-count`
Get count of users affected by module disable.

**Path Parameters:**
- `module_id`: integer - Module to check

**Response:**
```json
{
  "module_id": 5,
  "module_name": "Biofloc Management",
  "module_key": "biofloc",
  "users_count": 12,
  "users": [
    {
      "id": "uuid",
      "email": "user1@example.com",
      "full_name": "User One"
    }
  ]
}
```

**Purpose:**
- Used by frontend for impact warnings
- Shows who will lose access if module disabled
- Helps prevent accidental disruption

---

### Permission Management Endpoints

#### `GET /permissions/{user_id}`
Get user's module permissions.

**Path Parameters:**
- `user_id`: UUID - User to query

**Response:**
```json
{
  "user_id": "uuid",
  "permissions": [
    {
      "module_id": 3,
      "module_key": "inventory",
      "module_name": "Inventory Management",
      "can_access": true,
      "granted_at": "2025-11-01T10:00:00"
    },
    {
      "module_id": 5,
      "module_key": "biofloc",
      "module_name": "Biofloc Management",
      "can_access": false,
      "granted_at": null
    }
  ]
}
```

**Note:** Returns ALL modules with can_access flag (true/false).

---

#### `PUT /permissions/{user_id}`
Update user's module permissions (bulk replace).

**Path Parameters:**
- `user_id`: UUID - User to update

**Request Body:**
```json
{
  "module_ids": [3, 5, 7]
}
```

**Response:**
```json
{
  "user_id": "uuid",
  "granted_modules": ["inventory", "biofloc", "reports"]
}
```

**Backend Logic:**
1. **Validation:**
   - User exists and is active
   - User is NOT admin (cannot modify admin permissions via API)
   - All module IDs exist and are active

2. **Atomic Transaction:**
   - Delete all existing permissions for user
   - Insert new permissions for each module_id
   - Log activity with module list

3. **Error Handling:**
   - If user is admin: 403 Forbidden
   - If any module invalid: 400 Bad Request
   - Transaction rollback on any error

**Example:**
```python
@router.put("/permissions/{user_id}")
async def update_permissions(
    user_id: str,
    request: UpdatePermissionsRequest,
    current_user: dict = Depends(require_admin)
):
    return await admin_service.update_user_permissions(
        user_id, request.module_ids, current_user["id"]
    )
```

---

### Activity Logging Endpoints

#### `GET /activity-logs`
Get activity logs with filters.

**Query Parameters:**
- `days` (default: 7, range: 1-90): integer - Lookback period
- `user_id` (optional): UUID - Filter by user
- `module_key` (optional): string - Filter by module
- `action_type` (optional): string - Filter by action
- `page` (default: 1): integer - Page number
- `limit` (default: 50, max: 500): integer - Items per page

**Response:**
```json
{
  "logs": [
    {
      "id": 12345,
      "user_id": "uuid",
      "user_email": "admin@example.com",
      "user_role": "Admin",
      "action_type": "update_permissions",
      "module_key": null,
      "description": "Updated permissions for user user@example.com",
      "metadata": {
        "user_id": "target-uuid",
        "modules_granted": ["inventory", "biofloc"],
        "modules_count": 2
      },
      "success": true,
      "created_at": "2025-11-19T10:00:00"
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 50
}
```

**Backend Query:**
```sql
SELECT * FROM activity_logs
WHERE created_at >= NOW() - INTERVAL '7 days'
  AND ($1::uuid IS NULL OR user_id = $1)
  AND ($2::text IS NULL OR module_key = $2)
  AND ($3::text IS NULL OR action_type = $3)
ORDER BY created_at DESC
LIMIT 50 OFFSET 0;
```

---

### Statistics Endpoints

#### `GET /statistics`
Get admin dashboard statistics.

**Response:**
```json
{
  "total_users": 50,
  "active_users": 45,
  "inactive_users": 5,
  "total_admin": 3,
  "total_regular_users": 47,
  "recent_logins_24h": 12,
  "total_activities_7d": 234
}
```

**Backend Queries:**
```python
async def get_statistics():
    # Total users
    total_users = await db.fetch_val(
        "SELECT COUNT(*) FROM user_profiles"
    )

    # Active/inactive
    active_users = await db.fetch_val(
        "SELECT COUNT(*) FROM user_profiles WHERE is_active = TRUE"
    )

    # Admin count
    total_admin = await db.fetch_val(
        "SELECT COUNT(*) FROM user_profiles up "
        "JOIN roles r ON up.role_id = r.id "
        "WHERE r.role_name = 'Admin'"
    )

    # Recent logins (24h)
    recent_logins = await db.fetch_val(
        "SELECT COUNT(*) FROM auth.users "
        "WHERE last_sign_in_at >= NOW() - INTERVAL '24 hours'"
    )

    # Activity count (7d)
    activities_7d = await db.fetch_val(
        "SELECT COUNT(*) FROM activity_logs "
        "WHERE created_at >= NOW() - INTERVAL '7 days'"
    )

    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "total_admin": total_admin,
        "total_regular_users": total_users - total_admin,
        "recent_logins_24h": recent_logins,
        "total_activities_7d": activities_7d
    }
```

---

## Service Layer Logic

### Key Service Functions

#### `create_user(request, admin_id)`

**Purpose:** Create new user account with temporary password.

**Algorithm:**
1. Validate email uniqueness
2. Validate role exists
3. Generate temporary password
4. Hash password using bcrypt
5. Begin transaction:
   - Create auth.users entry (Supabase)
   - Create user_profiles entry
   - Log activity
6. Return user + temporary_password

**Error Handling:**
- Email exists: 400 Bad Request
- Invalid role: 404 Not Found
- Database error: 500 Internal Server Error

---

#### `update_user_permissions(user_id, module_ids, admin_id)`

**Purpose:** Bulk replace user's module permissions.

**Algorithm:**
1. Fetch user and validate:
   - User exists and is active
   - User is NOT admin (security check)
2. Validate all module_ids exist and are active
3. Begin atomic transaction:
   - `DELETE FROM user_module_permissions WHERE user_id = ?`
   - For each module_id:
     - `INSERT INTO user_module_permissions (user_id, module_id, granted_by)`
4. Log activity with metadata (module list)
5. Return granted module keys

**Security:**
- Prevents modifying admin permissions
- Atomic transaction (all-or-nothing)
- Audit logging

---

#### `disable_module(module_id, admin_id)`

**Purpose:** Disable module with cascading to children.

**Algorithm:**
1. Fetch module and validate:
   - Module exists
   - Module is NOT critical (dashboard/admin)
2. Update module `is_active = FALSE`
3. Database trigger automatically:
   - Disables all child modules
   - Removes all permissions for module + children
4. Log activity with cascade info in metadata
5. Return updated module

**Cascading Logic (via trigger):**
```sql
-- Find all children
WITH RECURSIVE children AS (
    SELECT id FROM modules WHERE parent_module_id = $module_id
    UNION ALL
    SELECT m.id FROM modules m
    JOIN children c ON m.parent_module_id = c.id
)
-- Disable all
UPDATE modules SET is_active = FALSE
WHERE id IN (SELECT id FROM children);

-- Remove permissions
DELETE FROM user_module_permissions
WHERE module_id IN (SELECT id FROM children OR id = $module_id);
```

---

## Frontend Architecture

### State Management

**React Query** handles all server state:
- Automatic caching with 5-minute stale time
- Background refetching on window focus
- Optimistic updates for instant UI feedback
- Query invalidation on mutations

**Example:**
```javascript
const { data: users, isLoading } = useQuery(
  ['adminUsers', filters],
  () => adminAPI.getUsers(filters),
  { staleTime: 5 * 60 * 1000 }
);

const updatePermissionsMutation = useMutation(
  ({ userId, moduleIds }) => adminAPI.updateUserPermissions(userId, moduleIds),
  {
    onSuccess: () => {
      queryClient.invalidateQueries(['adminUsers']);
      queryClient.invalidateQueries(['userPermissions']);
      enqueueSnackbar('Permissions updated successfully', { variant: 'success' });
    }
  }
);
```

---

### Component Structure

**AdminPanel.jsx** (988 lines, v1.4.0)

```jsx
AdminPanel
├── UserManagementPage
│   ├── UsersTable
│   ├── CreateUserDialog
│   └── PermissionsDialog (hierarchical)
├── ModuleManagementPage
│   ├── ModuleCards (grouped by parent)
│   └── ConfirmModuleToggleDialog
└── ActivityLogsPage
    ├── FilterControls
    └── LogsTable
```

---

### Key Components

#### 1. **CreateUserDialog**

**Purpose:** Create new user with validation.

**Features:**
- Email validation (format + uniqueness checked server-side)
- Full name input
- Role selection dropdown
- Shows temporary password after creation
- Auto-refreshes user list

**State Management:**
```javascript
const [formData, setFormData] = useState({
  email: '',
  full_name: '',
  role_id: 2 // Default to User
});
const [tempPassword, setTempPassword] = useState(null);
```

**Validation:**
- Email required, valid format
- Full name required, min 2 chars
- Role required

**Flow:**
```
1. User fills form
2. Clicks "Create User"
3. API call to POST /users
4. Response includes temporary_password
5. Dialog shows password (one-time display)
6. Admin copies and shares securely
7. User list refreshes
```

---

#### 2. **PermissionsDialog (Hierarchical)**

**Purpose:** Grant module permissions with parent-child grouping.

**Features (v1.3.0+):**
- Hierarchical display (parent modules with collapsible children)
- "Grant All" button per parent (grants parent + all children)
- Individual checkboxes per module
- Indented display for visual hierarchy
- Bulk save with single API call

**State Management:**
```javascript
const [selectedModules, setSelectedModules] = useState([]);
const { data: permissions } = useQuery(
  ['userPermissions', userId],
  () => adminAPI.getUserPermissions(userId)
);
```

**UI Structure:**
```
□ Aquaculture Operations
  ↳ □ Biofloc Management
  ↳ □ Hatchery Operations
  ↳ □ Nursery Management
[Grant All] button
```

**Logic:**
```javascript
const handleGrantAll = (parentId, childIds) => {
  setSelectedModules(prev => [
    ...prev.filter(id => ![parentId, ...childIds].includes(id)),
    parentId,
    ...childIds
  ]);
};
```

---

#### 3. **ConfirmModuleToggleDialog**

**Purpose:** Show impact warning before disabling module.

**Features (v1.4.0 - Protocol 3):**
- Fetches affected user count via GET /modules/{id}/users-count
- Shows list of affected users
- Requires explicit confirmation
- Displays warning message

**Flow:**
```
1. Admin toggles module switch
2. Frontend intercepts if disabling
3. Opens confirmation dialog
4. Fetches user impact count
5. Shows: "12 users will be affected"
6. Lists affected users
7. Admin confirms
8. API call to PUT /modules/{id}
9. Module disabled, dialog closes
```

**UI:**
```jsx
<Dialog>
  <DialogTitle>Confirm Module Disable</DialogTitle>
  <DialogContent>
    <Alert severity="warning">
      Disabling "{moduleName}" will affect {usersCount} users.
    </Alert>
    <Typography>Affected users:</Typography>
    <List>
      {users.map(u => <ListItem>{u.full_name} ({u.email})</ListItem>)}
    </List>
  </DialogContent>
  <DialogActions>
    <Button onClick={onCancel}>Cancel</Button>
    <Button onClick={onConfirm} color="error">Disable Module</Button>
  </DialogActions>
</Dialog>
```

---

### Security Protocols Implementation

#### **Protocol 1: Critical Module Protection**

**Frontend:**
```javascript
const isCritical = ['dashboard', 'admin'].includes(module.module_key);

<Switch
  checked={module.is_active}
  disabled={isCritical}
  onChange={() => handleToggle(module)}
/>

{isCritical && (
  <Chip label="Critical" color="error" size="small" />
)}
```

**Backend:**
```python
if module_key in ["dashboard", "admin"] and not is_active:
    raise HTTPException(
        status_code=400,
        detail=f"Cannot disable critical module: {module_key}"
    )
```

---

#### **Protocol 2: Parent-Child Validation**

**Frontend:**
```javascript
const isParentDisabled = module.parent_module_id
  ? !modules.find(m => m.id === module.parent_module_id)?.is_active
  : false;

<Switch
  checked={module.is_active}
  disabled={isCritical || isParentDisabled}
/>

{isParentDisabled && (
  <Tooltip title="Parent module is disabled">
    <InfoIcon color="disabled" />
  </Tooltip>
)}
```

**Backend:**
```python
if enabling_child and parent_disabled:
    raise HTTPException(
        status_code=400,
        detail="Cannot enable child module while parent is disabled"
    )
```

---

## Security & Permissions

### Authentication Flow

```
1. User logs in → Supabase Auth
2. JWT token issued with user_id
3. Token included in Authorization header
4. Backend validates token via Supabase
5. Extracts user_id from token
6. Fetches user_profiles to get role
7. Enforces admin check via require_admin
```

**require_admin Dependency:**
```python
async def require_admin(
    authorization: str = Header(None),
    db: Database = Depends(get_db)
):
    # Validate token
    user = await validate_jwt_token(authorization)

    # Fetch role
    role = await db.fetch_val(
        """
        SELECT r.role_name
        FROM user_profiles up
        JOIN roles r ON up.role_id = r.id
        WHERE up.id = $1
        """,
        user["id"]
    )

    # Enforce admin
    if role != "Admin":
        raise HTTPException(403, "Admin access required")

    return user
```

---

### Authorization Levels

**Level 1: Authentication**
- Valid JWT token required
- Token not expired
- User exists in database

**Level 2: Module Access**
- User has permission for specific module
- Checked via `require_module_access("admin")`

**Level 3: Admin Role**
- User role is "Admin"
- Checked via `require_admin` dependency
- Required for all admin panel endpoints

**Level 4: Action Authorization**
- Cannot delete self
- Cannot modify admin user permissions
- Cannot disable critical modules

---

### Data Protection

**Soft Deletes:**
- Users marked `is_active = FALSE`
- Data preserved for audit trail
- Foreign key relationships intact

**Cascading Controls:**
- Module disable cascades to children
- Permissions auto-cleaned
- Prevents orphaned data

**Audit Logging:**
- All actions logged to activity_logs
- Immutable log records (no updates/deletes)
- Metadata for investigation

---

## Performance Considerations

### Database Optimization

**Indexes:**
```sql
-- User queries
CREATE INDEX idx_user_profiles_role ON user_profiles(role_id);
CREATE INDEX idx_user_profiles_active ON user_profiles(is_active);

-- Permission queries
CREATE INDEX idx_user_module_permissions_user ON user_module_permissions(user_id);
CREATE INDEX idx_user_module_permissions_module ON user_module_permissions(module_id);

-- Activity log queries
CREATE INDEX idx_activity_logs_user ON activity_logs(user_id, created_at DESC);
CREATE INDEX idx_activity_logs_created_at ON activity_logs(created_at DESC);
```

**Query Optimization:**
- Views for complex joins (user_details, user_accessible_modules)
- Pagination on all list endpoints
- Filtered queries with WHERE clauses
- Limit on date ranges (max 90 days for logs)

---

### Frontend Optimization

**React Query Caching:**
- 5-minute stale time for user list
- Automatic background refetching
- Optimistic updates for instant feedback

**Component Optimization:**
- Memoized callbacks with useCallback
- Memoized computed values with useMemo
- Debounced search inputs

**Code Splitting:**
- Lazy load admin panel
- Separate chunk for admin code

---

## Integration Points

### Supabase Authentication

**Integration:**
- Uses Supabase `auth.users` table
- user_profiles.id references auth.users(id)
- JWT tokens validated via Supabase

**User Creation Flow:**
```
1. Admin creates user via POST /users
2. Backend calls Supabase signUp API
3. Supabase creates auth.users entry
4. Backend creates user_profiles entry
5. Temporary password returned to admin
6. User logs in with temp password
7. User prompted to change password
```

---

### Module Access Control

**Integration with Other Modules:**

Every module checks access via:
```python
@router.get("/inventory/items")
async def get_items(
    current_user: dict = Depends(require_module_access("inventory"))
):
    # User has inventory access
    pass
```

**Logic:**
```python
def require_module_access(module_key: str):
    async def dependency(current_user: dict = Depends(get_current_user)):
        # Admin: always allowed
        if current_user["role"] == "Admin":
            return current_user

        # Check permission
        has_access = await db.fetch_val(
            """
            SELECT EXISTS(
                SELECT 1 FROM user_module_permissions ump
                JOIN modules m ON ump.module_id = m.id
                WHERE ump.user_id = $1
                  AND m.module_key = $2
                  AND m.is_active = TRUE
            )
            """,
            current_user["id"], module_key
        )

        if not has_access:
            raise HTTPException(403, "Access denied")

        return current_user

    return dependency
```

---

### Activity Logging Integration

**Automatic Logging:**

Every admin action calls:
```python
await log_activity(
    user_id=current_user["id"],
    action_type="update_permissions",
    description=f"Updated permissions for user {target_email}",
    metadata={
        "user_id": str(target_user_id),
        "modules_granted": module_keys,
        "modules_count": len(module_ids)
    }
)
```

**Log Function:**
```python
async def log_activity(
    user_id: str,
    action_type: str,
    description: str,
    module_key: str = None,
    metadata: dict = None,
    success: bool = True
):
    user = await fetch_user_details(user_id)

    await db.execute(
        """
        INSERT INTO activity_logs
        (user_id, user_email, user_role, action_type, module_key,
         description, metadata, success)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
        user_id, user["email"], user["role"], action_type,
        module_key, description, json.dumps(metadata), success
    )
```

---

## Appendix: Common Queries

### Get all active users with permissions count
```sql
SELECT
    up.id,
    up.full_name,
    up.email,
    r.role_name,
    COUNT(ump.id) as permissions_count
FROM user_profiles up
LEFT JOIN roles r ON up.role_id = r.id
LEFT JOIN user_module_permissions ump ON up.id = ump.user_id
WHERE up.is_active = TRUE
GROUP BY up.id, up.full_name, up.email, r.role_name
ORDER BY up.full_name;
```

### Get module hierarchy
```sql
WITH RECURSIVE module_tree AS (
    -- Root modules
    SELECT id, module_key, module_name, parent_module_id, 0 as level
    FROM modules
    WHERE parent_module_id IS NULL

    UNION ALL

    -- Child modules
    SELECT m.id, m.module_key, m.module_name, m.parent_module_id, mt.level + 1
    FROM modules m
    JOIN module_tree mt ON m.parent_module_id = mt.id
)
SELECT * FROM module_tree
ORDER BY level, display_order;
```

### Get user activity summary
```sql
SELECT
    user_email,
    action_type,
    COUNT(*) as action_count,
    MAX(created_at) as last_action
FROM activity_logs
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY user_email, action_type
ORDER BY user_email, action_count DESC;
```

---

**End of Technical Guide**

For operational procedures and user workflows, see [User Guide](./user-guide.md).
