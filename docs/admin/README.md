# Admin Module

**Version:** 1.5.0
**Last Updated:** 2025-11-19
**Status:** Production Ready ✅

## Overview

The Admin Module is a comprehensive system administration platform for managing users, roles, permissions, modules, and system activity. It provides centralized control over access management, module configuration, and complete audit logging for all administrative actions.

### Key Capabilities

- **User Management** - Complete CRUD operations for user accounts
- **Role-Based Access Control (RBAC)** - Admin and User role management
- **Module Management** - Enable/disable system modules dynamically
- **Permission Management** - Granular module-level access control
- **Hierarchical Modules** - Parent-child module relationships with cascading controls
- **Activity Logging** - Complete audit trail of all system actions
- **Admin Statistics** - Real-time dashboard metrics and monitoring
- **Soft Delete Protection** - Preserve data integrity with deactivation instead of deletion
- **Security Protocols** - Critical module protection and user impact warnings

## Quick Start

### Prerequisites

- PostgreSQL database (>= 12)
- Python 3.8+ (backend)
- Node.js 16+ (frontend)
- Farm Management System core installed
- Admin user account

### Access Requirements

1. **Login with Admin credentials:**
   - Only users with "Admin" role can access admin module
   - Regular users cannot access admin functionality

2. **Navigate to Admin panel:**
   - Click "Admin" in main navigation menu
   - Dashboard displays at `/admin`

### First-Time Setup

Initial admin user is created during system installation. To create additional admins:

```sql
-- Only via direct database access (security by design)
UPDATE user_profiles
SET role_id = (SELECT id FROM roles WHERE role_name = 'Admin')
WHERE id = 'your-admin-user-uuid';
```

## Module Structure

```
admin/
├── Users              # User account management
├── Module Management  # Enable/disable system modules
└── Activity Logs      # System audit trail
```

## Core Concepts

### Users

A **user** represents a system account with authentication credentials and profile information. Each user has:
- Email (unique identifier)
- Full name
- Role (Admin or User)
- Active/inactive status
- Module access permissions

**User Lifecycle:**
```
Created → Active → (Optional) Deactivated
```

### Roles

**Roles** define the level of system access:

- **Admin:** Full system access, can manage users and modules
- **User:** Limited access based on granted module permissions

**Key Differences:**
- Admins automatically have access to ALL modules
- Users require explicit permission grants per module
- Only Admins can access the admin panel

### Modules

A **module** represents a functional area of the system (e.g., inventory, biofloc, dashboard). Modules can be:
- Enabled/disabled dynamically
- Organized hierarchically (parent-child relationships)
- Protected (critical modules cannot be disabled)

**Hierarchical Structure Example:**
```
Aquaculture (parent)
  ├─ Biofloc (child)
  ├─ Hatchery (child)
  └─ Nursery (child)
```

**Module Status Rules:**
- Disabling a parent automatically disables all children
- Enabling a child requires parent to be enabled first
- Critical modules (dashboard, admin) cannot be disabled

### Permissions

**Permissions** control which modules a user can access:
- Granted at the module level (all-or-nothing per module)
- Admin users: automatic access to all modules
- Regular users: require explicit grants
- Hierarchical: granting parent grants all children

**Permission Workflow:**
```
Admin selects user → Chooses modules → Saves permissions
  ↓
User can access granted modules
```

### Activity Logging

Every administrative action is logged with:
- **Who:** User who performed the action
- **What:** Type of action (create_user, update_permissions, etc.)
- **When:** Timestamp
- **Where:** Module affected (if applicable)
- **How:** Success or failure status
- **Context:** Additional metadata in JSON format

## Documentation

- **[Technical Guide](./technical-guide.md)** - Architecture, database schema, API reference for developers
- **[User Guide](./user-guide.md)** - Features, workflows, and operational procedures for administrators

## Key Features by Component

### User Management
- List all users with filters (role, status)
- Create new users with auto-generated temporary passwords
- Update user details (name, role, status)
- Deactivate users (soft delete)
- Self-deletion prevention
- Paginated user list (default 50/page)

### Role Management
- View available system roles
- Assign roles during user creation/update
- Role-based automatic permissions

### Module Management
- Enable/disable modules dynamically
- View hierarchical module structure
- Display order configuration
- User impact warnings before disabling
- Cascading disable for parent modules
- Critical module protection

### Permission Management
- Grant module access to individual users
- Hierarchical permission grants
- Bulk permission updates
- Visual hierarchy display
- Cannot modify admin user permissions

### Activity Logging
- Filter by user, module, action type, date range
- Configurable time filters (1-90 days)
- Metadata inspection for detailed analysis
- Success/failure tracking
- Paginated logs (default 50/page)

### Admin Statistics
- Total users (active/inactive breakdown)
- Admin vs regular user count
- Recent login activity (24 hours)
- System activity summary (7 days)

## Technology Stack

**Backend:**
- FastAPI (Python)
- PostgreSQL with asyncpg
- Pydantic for validation
- JWT authentication

**Frontend:**
- React with functional components
- Material-UI (MUI) components
- React Query for state management
- React Router for navigation
- Notistack for notifications

## Database Tables

Core tables:
- `roles` - System roles (Admin, User)
- `user_profiles` - User information and status
- `modules` - System module definitions
- `user_module_permissions` - User-module access mapping
- `activity_logs` - Complete audit trail

Key views:
- `user_details` - Combined user information
- `user_accessible_modules` - User-module access view
- `user_module_permissions` - Permission view

## API Endpoints

Base URL: `/api/v1/admin`

**User Operations:**
- `GET /users` - List users (paginated, filterable)
- `POST /users` - Create new user
- `PUT /users/{user_id}` - Update user
- `DELETE /users/{user_id}` - Deactivate user

**Role Operations:**
- `GET /roles` - List all roles

**Module Operations:**
- `GET /modules` - List all modules
- `PUT /modules/{module_id}` - Update module status
- `GET /modules/{module_id}/users-count` - Get impact count

**Permission Operations:**
- `GET /permissions/{user_id}` - Get user permissions
- `PUT /permissions/{user_id}` - Update user permissions

**Activity Logging:**
- `GET /activity-logs` - Get activity logs (filtered)

**Statistics:**
- `GET /statistics` - Get admin statistics

See [Technical Guide](./technical-guide.md) for complete API reference.

## Security Features

### Authentication
- JWT-based authentication required
- Admin role verification on all endpoints
- Token expiry and refresh mechanism

### Authorization
- Role-based access control (RBAC)
- Module-level permissions
- Admin-only access to admin panel
- Cannot modify other admin users' permissions

### Data Protection
- Soft deletes (users deactivated, not deleted)
- Self-deletion prevention
- Critical module protection
- Cascading disable safeguards
- Automatic permission cleanup

### Audit Trail
- All actions logged to activity_logs
- User attribution on all operations
- Success/failure tracking
- Metadata storage for investigation
- Queryable history (1-90 days)

## Security Protocols

### Protocol 1: Critical Module Protection
**Purpose:** Prevent system lockout

- Dashboard module cannot be disabled
- Admin module cannot be disabled
- UI shows disabled toggle for critical modules
- Backend enforces validation

### Protocol 2: Parent-Child Validation
**Purpose:** Maintain module hierarchy integrity

- Cannot enable child if parent is disabled
- Disabling parent automatically disables all children
- Cascading disable with automatic permission cleanup

### Protocol 3: User Impact Warnings
**Purpose:** Inform before disruption

- Before disabling module, show user count affected
- Display list of affected users
- Require explicit confirmation
- Helps prevent accidental access removal

### Protocol 4: Admin Permission Protection
**Purpose:** Prevent permission conflicts

- Cannot modify permissions for admin users via UI
- Admins automatically have all module access
- Prevents accidental admin lockout

## Version History

### v1.5.0 (2025-11-19)
- ✅ Cascading disable for parent modules
- ✅ Parent-child hierarchical module support
- ✅ Enhanced activity logging for cascade operations
- ✅ Improved module management backend logic

### v1.4.0 (2025-11-18)
- ✅ All 4 security protocols implemented
- ✅ User impact warnings before module disable
- ✅ Hierarchical permissions dialog (Phase 3)
- ✅ Temp password display on user creation (Phase 2)
- ✅ Enhanced UI/UX improvements

### v1.3.0 (2025-11-17)
- ✅ Hierarchical module structure
- ✅ Parent-child module relationships
- ✅ Database schema updates

### v1.2.0 (2025-11-16)
- ✅ Activity logging enhancements
- ✅ Advanced filtering
- ✅ Metadata support

### v1.1.0 (2025-11-15)
- ✅ Permission management
- ✅ Module management
- ✅ Basic user CRUD

### v1.0.0 (2025-11-14)
- ✅ Initial release
- ✅ User management
- ✅ Role-based access control
- ✅ Basic activity logging

## Common Administrative Tasks

### Creating a New User
1. Navigate to Admin → Users
2. Click "Add User" button
3. Enter email, full name, select role
4. Click "Create User"
5. Share temporary password securely
6. User logs in and changes password

### Granting Module Access
1. Navigate to Admin → Users
2. Find user in list
3. Click "Manage Permissions" icon
4. Select modules to grant
5. Click "Save"
6. User can now access granted modules

### Disabling a Module
1. Navigate to Admin → Module Management
2. Find module to disable
3. Click toggle switch
4. Review user impact warning
5. Confirm action
6. Module disabled, users lose access

### Viewing System Activity
1. Navigate to Admin → Activity Logs
2. Select time period (1-90 days)
3. Optionally filter by user, module, or action
4. Review activity table
5. Inspect metadata for details

## Best Practices

### User Management
- Use descriptive full names for easy identification
- Regularly review inactive users
- Deactivate instead of delete for audit trail
- Share temporary passwords securely (encrypted channels)
- Prompt users to change passwords immediately

### Permission Management
- Grant minimum necessary permissions
- Use hierarchical grants (parent + children)
- Review permissions quarterly
- Document permission changes in notes
- Audit admin user list regularly

### Module Management
- Test module disable in non-production first
- Review user impact before disabling
- Communicate with affected users before changes
- Document reasons for module status changes
- Monitor activity logs after changes

### Security
- Limit admin user count (principle of least privilege)
- Rotate admin credentials regularly
- Monitor activity logs for suspicious actions
- Review login activity daily
- Keep admin user list up to date

## Support & Contributing

For issues, questions, or contributions:
- Check the documentation in `docs/admin/`
- Review the code comments in source files
- Refer to the database schema in migration files
- Contact system administrator for access issues

## License

Part of the Farm Management System
© 2025 All rights reserved
