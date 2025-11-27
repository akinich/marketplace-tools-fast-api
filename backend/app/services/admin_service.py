"""
================================================================================
Farm Management System - Admin Service Layer
================================================================================
Version: 1.7.0
Last Updated: 2025-11-19

Changelog:
----------
v1.7.0 (2025-11-19):
  - Added hard delete functionality for users
  - delete_user() now supports hard_delete parameter
  - Hard delete permanently removes user from Supabase auth (cascades to user_profiles)
  - Improved create_user() validation to detect soft-deleted users
  - Better error messages when trying to create user with deactivated email

v1.6.0 (2025-11-19):
  - CRITICAL FIX: User creation now uses Supabase Admin API
  - Ensures emails are marked as confirmed for password reset functionality
  - Fixes issue where new users couldn't receive password reset emails
  - Previous version directly inserted into users without email confirmation

v1.5.0 (2025-11-17):
  - Added cascading disable for parent modules
  - When parent module disabled, all sub-modules automatically disabled
  - Disabling sub-modules does not affect parent module
  - Enhanced logging for cascade operations

v1.4.0 (2025-11-17):
  - Added parent_module_id to get_user_accessible_modules()
  - Fixed hierarchical navigation in frontend
  - Now properly returns parent_module_id for nested modules

v1.3.0 (2025-11-17):
  - Implemented create_user() with password_hash support
  - Added hierarchical module support in get_modules_list()
  - Now returns parent_module_id in module queries
  - User creation now works directly from Admin Panel
  - Email uniqueness validation added
  - Role validation added before user creation

v1.2.0 (2025-11-17):
  - Added UUID to string conversion in get_users_list()
  - Added UUID to string conversion in update_user()
  - Added dict conversion in get_user_permissions() for consistency
  - Fixed JSON serialization issue with UUID objects from asyncpg

v1.1.0 (2025-11-17):
  - Fixed all execute() calls to use execute_query()
  - Removed get_supabase() import dependencies
  - Modified create_user() to return 501 with instructions
  - Database-only operations (no Supabase client)

v1.0.0 (2025-11-17):
  - Initial admin service implementation
  - User CRUD operations
  - Permission management
  - Activity log queries
  - Module management
  - Admin statistics

================================================================================
"""

from typing import Optional, List, Dict
from fastapi import HTTPException, status
import logging
import math
import uuid
from uuid import UUID

from app.database import get_db, fetch_one, fetch_all, execute_query
from app.auth.password import hash_password
from app.services.auth_service import log_activity
from app.schemas.admin import (
    CreateUserRequest,
    UpdateUserRequest,
    UpdatePermissionsRequest,
    UpdateModuleRequest,
)

logger = logging.getLogger(__name__)


# ============================================================================
# USER MANAGEMENT
# ============================================================================


async def get_users_list(
    is_active: Optional[bool] = None,
    role: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> Dict:
    """
    Get paginated list of users.

    Args:
        is_active: Filter by active status
        role: Filter by role name
        page: Page number (1-indexed)
        limit: Items per page

    Returns:
        Dict with users, total, page, limit, total_pages
    """
    # Build WHERE clause
    where_conditions = []
    params = []
    param_count = 1

    if is_active is not None:
        where_conditions.append(f"up.is_active = ${param_count}")
        params.append(is_active)
        param_count += 1

    if role:
        where_conditions.append(f"r.role_name = ${param_count}")
        params.append(role)
        param_count += 1

    where_clause = (
        f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
    )

    # Get total count
    count_query = f"""
        SELECT COUNT(*) as total
        FROM user_profiles up
        LEFT JOIN roles r ON r.id = up.role_id
        {where_clause}
    """
    count_result = await fetch_one(count_query, *params)
    total = count_result["total"] if count_result else 0

    # Get paginated users
    offset = (page - 1) * limit
    users_query = f"""
        SELECT
            up.id,
            au.email,
            up.full_name,
            up.role_id,
            r.role_name,
            up.is_active,
            up.must_change_password,
            up.created_at
        FROM user_profiles up
        JOIN auth.users au ON au.id = up.id
        LEFT JOIN roles r ON r.id = up.role_id
        {where_clause}
        ORDER BY up.created_at DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    params.extend([limit, offset])
    users_raw = await fetch_all(users_query, *params)

    # Convert UUID objects to strings for JSON serialization
    users = []
    for user in users_raw:
        user_dict = dict(user)
        user_dict['id'] = str(user_dict['id'])  # Convert UUID to string
        users.append(user_dict)

    total_pages = math.ceil(total / limit) if limit > 0 else 0

    return {
        "users": users,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
    }


async def create_user(request: CreateUserRequest, created_by_id: str) -> Dict:
    """
    Create new user with temporary password.

    Args:
        request: CreateUserRequest with email, full_name, role_id
        created_by_id: Admin user ID creating this user

    Returns:
        Dict with user info and temporary_password

    Raises:
        HTTPException: If user creation fails or email already exists
    """
    try:
        # Generate simple temporary password: firstname@year (e.g., john@2025)
        # User is forced to change on first login anyway
        from datetime import datetime
        first_name = request.full_name.split()[0].lower()
        current_year = datetime.now().year
        temp_password = f"{first_name}@{current_year}"
        password_hash_value = hash_password(temp_password)

        # Check if email already exists
        existing_user = await fetch_one(
            """
            SELECT au.id, up.is_active
            FROM auth.users au
            LEFT JOIN user_profiles up ON up.id = au.id
            WHERE au.email = $1
            """,
            request.email
        )
        if existing_user:
            if existing_user.get('is_active') is False:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User with email {request.email} is deactivated. Please reactivate the user or permanently delete them first using hard_delete=true"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User with email {request.email} already exists"
                )

        # Check if role exists
        role_exists = await fetch_one(
            "SELECT id FROM roles WHERE id = $1",
            request.role_id
        )
        if not role_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role ID {request.role_id} does not exist"
            )

        # In test environment, create user directly without Supabase
        import os
        is_test = os.getenv("APP_ENV") == "test"

        if is_test:
            # Test mode: Create user directly in database
            from uuid import uuid4
            user_id = str(uuid4())

            # Create user in users table
            await execute_query(
                "INSERT INTO auth.users (id, email) VALUES ($1, $2)",
                UUID(user_id),
                request.email
            )
        else:
            # Production mode: Use Supabase Admin API
            from app.utils.supabase_client import get_supabase_client
            supabase = get_supabase_client()

            # Create user via Supabase Admin API
            user_response = supabase.auth.admin.create_user({
                "email": request.email,
                "password": temp_password,
                "email_confirm": True,  # Mark email as confirmed
                "user_metadata": {
                    "full_name": request.full_name
                }
            })

            user_id = user_response.user.id

        # Create user profile with password_hash and must_change_password flag
        await execute_query(
            """
            INSERT INTO user_profiles (id, full_name, role_id, is_active, password_hash, must_change_password)
            VALUES ($1, $2, $3, TRUE, $4, TRUE)
            """,
            UUID(user_id),
            request.full_name,
            request.role_id,
            password_hash_value
        )

        # Fetch created user with role info
        user_raw = await fetch_one(
            """
            SELECT
                up.id,
                au.email,
                up.full_name,
                up.role_id,
                r.role_name,
                up.is_active,
                up.must_change_password,
                up.created_at
            FROM user_profiles up
            JOIN auth.users au ON au.id = up.id
            LEFT JOIN roles r ON r.id = up.role_id
            WHERE up.id = $1
            """,
            UUID(user_id),
        )

        # Convert UUID to string
        user = dict(user_raw)
        user['id'] = str(user['id'])

        # Log activity
        admin = await fetch_one(
            "SELECT au.email, r.role_name FROM user_profiles up JOIN auth.users au ON au.id = up.id LEFT JOIN roles r ON r.id = up.role_id WHERE up.id = $1",
            created_by_id,
        )
        await log_activity(
            user_id=created_by_id,
            user_email=admin["email"],
            user_role=admin["role_name"],
            action_type="create_user",
            description=f"Created new user: {request.email}",
            module_key="admin",
            metadata={"new_user_id": user_id, "email": request.email},
        )

        logger.info(f"User created successfully: {request.email} (ID: {user_id})")

        return {"user": user, "temporary_password": temp_password}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create user error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )


async def update_user(
    user_id: str, request: UpdateUserRequest, updated_by_id: str
) -> Dict:
    """
    Update user information.

    Args:
        user_id: User UUID to update
        request: UpdateUserRequest
        updated_by_id: Admin user ID performing update

    Returns:
        Dict with updated user info

    Raises:
        HTTPException: If user not found or update fails
    """
    # Check if user exists
    user = await fetch_one("SELECT id FROM user_profiles WHERE id = $1", user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Build UPDATE statement dynamically
    update_fields = []
    params = []
    param_count = 1

    if request.full_name is not None:
        update_fields.append(f"full_name = ${param_count}")
        params.append(request.full_name)
        param_count += 1

    if request.role_id is not None:
        update_fields.append(f"role_id = ${param_count}")
        params.append(request.role_id)
        param_count += 1

    if request.is_active is not None:
        update_fields.append(f"is_active = ${param_count}")
        params.append(request.is_active)
        param_count += 1

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update provided",
        )

    # Add updated_at
    update_fields.append(f"updated_at = NOW()")

    # Add user_id to params
    params.append(user_id)

    # Execute update
    query = f"""
        UPDATE user_profiles
        SET {', '.join(update_fields)}
        WHERE id = ${param_count}
    """
    await execute_query(query, *params)

    # Fetch updated user
    updated_user_raw = await fetch_one(
        """
        SELECT
            up.id,
            au.email,
            up.full_name,
            up.role_id,
            r.role_name,
            up.is_active,
            up.must_change_password,
            up.created_at
        FROM user_profiles up
        JOIN auth.users au ON au.id = up.id
        LEFT JOIN roles r ON r.id = up.role_id
        WHERE up.id = $1
        """,
        user_id,
    )

    # Convert UUID to string
    updated_user = dict(updated_user_raw)
    updated_user['id'] = str(updated_user['id'])

    # Log activity
    admin = await fetch_one(
        "SELECT au.email, r.role_name FROM user_profiles up JOIN auth.users au ON au.id = up.id LEFT JOIN roles r ON r.id = up.role_id WHERE up.id = $1",
        updated_by_id,
    )
    await log_activity(
        user_id=updated_by_id,
        user_email=admin["email"],
        user_role=admin["role_name"],
        action_type="update_user",
        description=f"Updated user: {updated_user['email']}",
        module_key="admin",
        metadata={"updated_user_id": str(user_id)},
    )

    return {"user": updated_user}


async def delete_user(user_id: str, deleted_by_id: str, hard_delete: bool = False) -> None:
    """
    Delete user (soft delete by default, hard delete optional).

    Args:
        user_id: User UUID to delete
        deleted_by_id: Admin user ID performing deletion
        hard_delete: If True, permanently delete user from database

    Raises:
        HTTPException: If user not found or is admin deleting themselves
    """
    # Check if user exists
    user = await fetch_one(
        "SELECT up.id, au.email FROM user_profiles up JOIN auth.users au ON au.id = up.id WHERE up.id = $1",
        user_id,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Prevent self-deletion
    if user_id == deleted_by_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    if hard_delete:
        # Hard delete - permanently remove user from database
        try:
            import os
            is_test = os.getenv("APP_ENV") == "test"

            if is_test:
                # Test mode: Delete directly from database
                # Delete user_profiles first (if not cascading)
                await execute_query("DELETE FROM user_profiles WHERE id = $1", UUID(user_id))
                # Delete from users table
                await execute_query("DELETE FROM auth.users WHERE id = $1", UUID(user_id))
            else:
                # Production mode: Use Supabase Admin API
                from app.utils.supabase_client import get_supabase_client
                supabase = get_supabase_client()

                # Delete from Supabase auth (will cascade to user_profiles due to ON DELETE CASCADE)
                supabase.auth.admin.delete_user(user_id)

            logger.info(f"User permanently deleted: {user['email']} (ID: {user_id})")
        except Exception as e:
            logger.error(f"Hard delete user error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to permanently delete user: {str(e)}",
            )
    else:
        # Soft delete (deactivate)
        await execute_query(
            "UPDATE user_profiles SET is_active = FALSE, updated_at = NOW() WHERE id = $1",
            user_id,
        )

    # Log activity
    admin = await fetch_one(
        "SELECT au.email, r.role_name FROM user_profiles up JOIN auth.users au ON au.id = up.id LEFT JOIN roles r ON r.id = up.role_id WHERE up.id = $1",
        deleted_by_id,
    )
    await log_activity(
        user_id=deleted_by_id,
        user_email=admin["email"],
        user_role=admin["role_name"],
        action_type="hard_delete_user" if hard_delete else "delete_user",
        description=f"{'Permanently deleted' if hard_delete else 'Deactivated'} user: {user['email']}",
        module_key="admin",
        metadata={"deleted_user_id": str(user_id), "hard_delete": hard_delete},
    )


# ============================================================================
# ROLE MANAGEMENT
# ============================================================================


async def get_roles_list() -> List[Dict]:
    """Get all roles"""
    roles = await fetch_all(
        "SELECT id, role_name, description, created_at FROM roles ORDER BY id"
    )
    return roles


# ============================================================================
# MODULE MANAGEMENT
# ============================================================================


async def get_modules_list() -> List[Dict]:
    """Get all modules with hierarchical structure"""
    modules_raw = await fetch_all(
        """
        SELECT id, module_key, module_name, description, icon, display_order, is_active, parent_module_id
        FROM modules
        ORDER BY parent_module_id NULLS FIRST, display_order
        """
    )
    # Convert to list of dicts
    modules = [dict(m) for m in modules_raw]
    return modules


async def update_module(module_id: int, request: UpdateModuleRequest) -> Dict:
    """
    Update module settings with security validations and cascading logic

    Security Protocols:
    1. Critical Module Protection: Prevents disabling dashboard/admin modules
    2. Parent-Child Validation: Ensures parent is enabled when enabling child
    3. Permission Cleanup: Removes user permissions when disabling modules
    4. Cascade Disable: Automatically disables children when parent is disabled
    """
    # Fetch module details for validation
    module = await fetch_one(
        "SELECT id, module_key, module_name, parent_module_id, is_active FROM modules WHERE id = $1",
        module_id
    )
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )

    # SECURITY PROTOCOL 1: Critical Module Protection
    # Prevent disabling dashboard and admin modules (system-critical)
    if request.is_active == False:
        critical_modules = ['dashboard', 'admin']
        if module['module_key'] in critical_modules:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot disable critical system module: {module['module_name']}. "
                       f"This module is required for system operation."
            )

    # SECURITY PROTOCOL 2: Parent-Child Validation
    # When enabling a child module, ensure parent is enabled
    if request.is_active == True and module['parent_module_id']:
        parent = await fetch_one(
            "SELECT id, module_name, is_active FROM modules WHERE id = $1",
            module['parent_module_id']
        )
        if parent and not parent['is_active']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot enable sub-module '{module['module_name']}': "
                       f"parent module '{parent['module_name']}' is currently disabled. "
                       f"Please enable the parent module first."
            )

    # Build UPDATE statement
    update_fields = []
    params = []
    param_count = 1

    if request.is_active is not None:
        update_fields.append(f"is_active = ${param_count}")
        params.append(request.is_active)
        param_count += 1

    if request.display_order is not None:
        update_fields.append(f"display_order = ${param_count}")
        params.append(request.display_order)
        param_count += 1

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update provided",
        )

    params.append(module_id)

    query = f"""
        UPDATE modules
        SET {', '.join(update_fields)}
        WHERE id = ${param_count}
    """
    await execute_query(query, *params)

    # SECURITY PROTOCOL 3 & 4: Cascading Disable + Permission Cleanup
    if request.is_active is not None and request.is_active == False:
        # Get all affected modules (this module + all descendants)
        affected_modules = [module_id]

        # Check if this module has children
        submodules = await fetch_all(
            "SELECT id, module_key FROM modules WHERE parent_module_id = $1",
            module_id
        )

        if submodules:
            # Disable all sub-modules
            await execute_query(
                "UPDATE modules SET is_active = FALSE WHERE parent_module_id = $1",
                module_id
            )
            submodule_ids = [dict(sm)['id'] for sm in submodules]
            affected_modules.extend(submodule_ids)
            submodule_keys = [dict(sm)['module_key'] for sm in submodules]
            logger.info(f"Cascaded disable to {len(submodules)} sub-modules: {', '.join(submodule_keys)}")

        # SECURITY PROTOCOL 3: Permission Cleanup
        # Remove all user permissions for disabled modules
        for affected_id in affected_modules:
            deleted_count = await execute_query(
                "DELETE FROM user_module_permissions WHERE module_id = $1 RETURNING id",
                affected_id
            )
            if deleted_count:
                logger.info(f"Removed {deleted_count} user permissions for module ID {affected_id}")

    # Fetch updated module
    updated_module = await fetch_one("SELECT * FROM modules WHERE id = $1", module_id)
    return updated_module


async def get_module_users_count(module_id: int) -> Dict:
    """
    Get count of users who have permissions to a specific module

    Used for impact warnings before disabling modules
    Returns count and list of affected users
    """
    # Verify module exists
    module = await fetch_one(
        "SELECT id, module_name, module_key FROM modules WHERE id = $1",
        module_id
    )
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )

    # Get all users with permissions to this module
    users = await fetch_all(
        """
        SELECT
            up.id,
            u.email,
            up.full_name,
            r.role_name
        FROM user_module_permissions ump
        JOIN user_profiles up ON up.id = ump.user_id
        JOIN auth.users u ON u.id = up.id
        LEFT JOIN roles r ON r.id = up.role_id
        WHERE ump.module_id = $1 AND ump.can_access = TRUE
        ORDER BY up.full_name
        """,
        module_id
    )

    # Convert to dicts
    users_list = [dict(u) for u in users]

    return {
        "module_id": module['id'],
        "module_name": module['module_name'],
        "module_key": module['module_key'],
        "users_count": len(users_list),
        "users": users_list
    }


# ============================================================================
# PERMISSION MANAGEMENT
# ============================================================================


async def get_user_permissions(user_id: str) -> Dict:
    """Get user's module permissions"""
    # Get all modules with user's permission status
    permissions_raw = await fetch_all(
        """
        SELECT
            m.id as module_id,
            m.module_key,
            m.module_name,
            COALESCE(ump.can_access, FALSE) as can_access
        FROM modules m
        LEFT JOIN user_module_permissions ump ON ump.module_id = m.id AND ump.user_id = $1
        WHERE m.is_active = TRUE
        ORDER BY m.display_order
        """,
        user_id,
    )

    # Convert to list of dicts (no UUID fields here, but for consistency)
    permissions = [dict(p) for p in permissions_raw]

    return {"user_id": user_id, "permissions": permissions}


async def update_user_permissions(
    user_id: str, request: UpdatePermissionsRequest, granted_by_id: str
) -> Dict:
    """Update user's module permissions (bulk replace)"""
    # Check if user exists and is not admin
    user = await fetch_one(
        """
        SELECT up.id, r.role_name
        FROM user_profiles up
        LEFT JOIN roles r ON r.id = up.role_id
        WHERE up.id = $1
        """,
        user_id,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user["role_name"] == "Admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify admin permissions (admins have full access)",
        )

    # Delete existing permissions
    await execute_query("DELETE FROM user_module_permissions WHERE user_id = $1", user_id)

    # Insert new permissions
    if request.module_ids:
        values = []
        for module_id in request.module_ids:
            values.append(
                f"('{user_id}', {module_id}, TRUE)"
            )

        insert_query = f"""
            INSERT INTO user_module_permissions (user_id, module_id, can_access)
            VALUES {', '.join(values)}
        """
        await execute_query(insert_query)

    # Get module keys
    module_keys = await fetch_all(
        f"""
        SELECT module_key
        FROM modules
        WHERE id = ANY($1::int[])
        """,
        request.module_ids,
    )
    granted_modules = [m["module_key"] for m in module_keys]

    # Log activity
    admin = await fetch_one(
        "SELECT au.email, r.role_name FROM user_profiles up JOIN auth.users au ON au.id = up.id LEFT JOIN roles r ON r.id = up.role_id WHERE up.id = $1",
        granted_by_id,
    )
    user_email = await fetch_one(
        "SELECT email FROM auth.users WHERE id = $1", user_id
    )
    await log_activity(
        user_id=granted_by_id,
        user_email=admin["email"],
        user_role=admin["role_name"],
        action_type="update_permissions",
        description=f"Updated permissions for user: {user_email['email']}",
        module_key="admin",
        metadata={"target_user_id": str(user_id), "modules": granted_modules},
    )

    return {
        "message": "Permissions granted successfully",
        "granted_modules": granted_modules,
    }


# ============================================================================
# ACTIVITY LOGS
# ============================================================================


async def get_activity_logs(
    days: int = 7,
    user_id: Optional[str] = None,
    module_key: Optional[str] = None,
    action_type: Optional[str] = None,
    page: int = 1,
    limit: int = 100,
) -> Dict:
    """Get activity logs with filters"""
    # Build WHERE clause
    where_conditions = [f"created_at >= NOW() - INTERVAL '{days} days'"]
    params = []
    param_count = 1

    if user_id:
        where_conditions.append(f"user_id = ${param_count}")
        params.append(user_id)
        param_count += 1

    if module_key:
        where_conditions.append(f"module_key = ${param_count}")
        params.append(module_key)
        param_count += 1

    if action_type:
        where_conditions.append(f"action_type = ${param_count}")
        params.append(action_type)
        param_count += 1

    where_clause = f"WHERE {' AND '.join(where_conditions)}"

    # Get total count
    count_query = f"""
        SELECT COUNT(*) as total
        FROM activity_logs
        {where_clause}
    """
    count_result = await fetch_one(count_query, *params)
    total = count_result["total"] if count_result else 0

    # Get paginated logs
    offset = (page - 1) * limit
    logs_query = f"""
        SELECT
            id, user_email, user_role, action_type, module_key,
            description, metadata, success, created_at
        FROM activity_logs
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    params.extend([limit, offset])
    logs_raw = await fetch_all(logs_query, *params)

    # Convert logs to dicts and parse metadata JSON strings
    import json
    logs = []
    for log in logs_raw:
        log_dict = dict(log)
        # Parse metadata if it's a string
        if log_dict.get('metadata') and isinstance(log_dict['metadata'], str):
            try:
                log_dict['metadata'] = json.loads(log_dict['metadata'])
            except json.JSONDecodeError:
                log_dict['metadata'] = None
        logs.append(log_dict)

    return {"logs": logs, "total": total, "page": page, "limit": limit}


# ============================================================================
# USER ACCESSIBLE MODULES
# ============================================================================


async def get_user_accessible_modules(user_id: str) -> List[Dict]:
    """Get modules accessible to user"""
    modules_raw = await fetch_all(
        """
        SELECT
            m.id as module_id,
            m.module_key,
            m.module_name,
            m.icon,
            m.display_order,
            m.parent_module_id
        FROM user_module_permissions ump
        JOIN modules m ON m.id = ump.module_id
        WHERE ump.user_id = $1 AND ump.can_access = TRUE
        ORDER BY m.display_order
        """,
        UUID(user_id),
    )
    # Convert to list of dicts
    modules = [dict(m) for m in modules_raw]
    return modules


# ============================================================================
# ADMIN STATISTICS
# ============================================================================


async def get_admin_statistics() -> Dict:
    """Get admin panel statistics"""
    # Total users
    total_users_result = await fetch_one(
        "SELECT COUNT(*) as count FROM user_profiles"
    )
    total_users = total_users_result["count"] if total_users_result else 0

    # Active users
    active_users_result = await fetch_one(
        "SELECT COUNT(*) as count FROM user_profiles WHERE is_active = TRUE"
    )
    active_users = active_users_result["count"] if active_users_result else 0

    # Inactive users
    inactive_users = total_users - active_users

    # Admin count
    admin_count_result = await fetch_one(
        """
        SELECT COUNT(*) as count
        FROM user_profiles up
        JOIN roles r ON r.id = up.role_id
        WHERE r.role_name = 'Admin'
        """
    )
    total_admin = admin_count_result["count"] if admin_count_result else 0

    # Regular users
    total_regular_users = total_users - total_admin

    # Recent logins (24h)
    recent_logins_result = await fetch_one(
        """
        SELECT COUNT(*) as count
        FROM activity_logs
        WHERE action_type = 'login'
          AND created_at >= NOW() - INTERVAL '24 hours'
        """
    )
    recent_logins_24h = recent_logins_result["count"] if recent_logins_result else 0

    # Total activities (7 days)
    activities_7d_result = await fetch_one(
        """
        SELECT COUNT(*) as count
        FROM activity_logs
        WHERE created_at >= NOW() - INTERVAL '7 days'
        """
    )
    total_activities_7d = activities_7d_result["count"] if activities_7d_result else 0

    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "total_admin": total_admin,
        "total_regular_users": total_regular_users,
        "recent_logins_24h": recent_logins_24h,
        "total_activities_7d": total_activities_7d,
    }
