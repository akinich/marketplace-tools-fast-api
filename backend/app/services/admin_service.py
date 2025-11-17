"""
================================================================================
Farm Management System - Admin Service Layer
================================================================================
Version: 1.0.0
Last Updated: 2025-11-17

Changelog:
----------
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

from app.database import get_db, get_supabase, fetch_one, fetch_all, execute
from app.auth.password import generate_temporary_password, hash_password
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
            up.created_at
        FROM user_profiles up
        JOIN auth.users au ON au.id = up.id
        LEFT JOIN roles r ON r.id = up.role_id
        {where_clause}
        ORDER BY up.created_at DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
    """
    params.extend([limit, offset])
    users = await fetch_all(users_query, *params)

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
        HTTPException: If user creation fails
    """
    try:
        # Generate temporary password
        temp_password = generate_temporary_password()

        # Create user in Supabase Auth
        supabase = get_supabase()
        auth_response = supabase.auth.admin.create_user(
            {
                "email": request.email,
                "password": temp_password,
                "email_confirm": True,  # Auto-confirm email
            }
        )

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user in authentication system",
            )

        user_id = auth_response.user.id

        # Create user profile
        await execute(
            """
            INSERT INTO user_profiles (id, full_name, role_id, is_active)
            VALUES ($1, $2, $3, TRUE)
            """,
            user_id,
            request.full_name,
            request.role_id,
        )

        # Fetch created user with role info
        user = await fetch_one(
            """
            SELECT
                up.id,
                au.email,
                up.full_name,
                up.role_id,
                r.role_name,
                up.is_active,
                up.created_at
            FROM user_profiles up
            JOIN auth.users au ON au.id = up.id
            LEFT JOIN roles r ON r.id = up.role_id
            WHERE up.id = $1
            """,
            user_id,
        )

        # Log activity
        admin = await fetch_one(
            "SELECT email, r.role_name FROM user_profiles up LEFT JOIN roles r ON r.id = up.role_id WHERE up.id = $1",
            created_by_id,
        )
        await log_activity(
            user_id=created_by_id,
            user_email=admin["email"],
            user_role=admin["role_name"],
            action_type="create_user",
            description=f"Created new user: {request.email}",
            module_key="admin",
            metadata={"new_user_id": str(user_id), "email": request.email},
        )

        return {"user": user, "temporary_password": temp_password}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create user error: {e}")
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
    await execute(query, *params)

    # Fetch updated user
    updated_user = await fetch_one(
        """
        SELECT
            up.id,
            au.email,
            up.full_name,
            up.role_id,
            r.role_name,
            up.is_active,
            up.created_at
        FROM user_profiles up
        JOIN auth.users au ON au.id = up.id
        LEFT JOIN roles r ON r.id = up.role_id
        WHERE up.id = $1
        """,
        user_id,
    )

    # Log activity
    admin = await fetch_one(
        "SELECT email, r.role_name FROM user_profiles up LEFT JOIN roles r ON r.id = up.role_id WHERE up.id = $1",
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


async def delete_user(user_id: str, deleted_by_id: str) -> None:
    """
    Delete user (soft delete - deactivate).

    Args:
        user_id: User UUID to delete
        deleted_by_id: Admin user ID performing deletion

    Raises:
        HTTPException: If user not found or is admin deleting themselves
    """
    # Check if user exists
    user = await fetch_one(
        "SELECT id, email FROM user_profiles up JOIN auth.users au ON au.id = up.id WHERE up.id = $1",
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

    # Soft delete (deactivate)
    await execute(
        "UPDATE user_profiles SET is_active = FALSE, updated_at = NOW() WHERE id = $1",
        user_id,
    )

    # Log activity
    admin = await fetch_one(
        "SELECT email, r.role_name FROM user_profiles up LEFT JOIN roles r ON r.id = up.role_id WHERE up.id = $1",
        deleted_by_id,
    )
    await log_activity(
        user_id=deleted_by_id,
        user_email=admin["email"],
        user_role=admin["role_name"],
        action_type="delete_user",
        description=f"Deleted user: {user['email']}",
        module_key="admin",
        metadata={"deleted_user_id": str(user_id)},
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
    """Get all modules"""
    modules = await fetch_all(
        """
        SELECT id, module_key, module_name, description, icon, display_order, is_active
        FROM modules
        ORDER BY display_order
        """
    )
    return modules


async def update_module(module_id: int, request: UpdateModuleRequest) -> Dict:
    """Update module settings"""
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
    await execute(query, *params)

    # Fetch updated module
    module = await fetch_one("SELECT * FROM modules WHERE id = $1", module_id)
    return module


# ============================================================================
# PERMISSION MANAGEMENT
# ============================================================================


async def get_user_permissions(user_id: str) -> Dict:
    """Get user's module permissions"""
    # Get all modules with user's permission status
    permissions = await fetch_all(
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
    await execute("DELETE FROM user_module_permissions WHERE user_id = $1", user_id)

    # Insert new permissions
    if request.module_ids:
        values = []
        for module_id in request.module_ids:
            values.append(
                f"('{user_id}', {module_id}, TRUE, '{granted_by_id}', NOW())"
            )

        insert_query = f"""
            INSERT INTO user_module_permissions (user_id, module_id, can_access, granted_by, granted_at)
            VALUES {', '.join(values)}
        """
        await execute(insert_query)

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
        "SELECT email, r.role_name FROM user_profiles up LEFT JOIN roles r ON r.id = up.role_id WHERE up.id = $1",
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
        "message": "Permissions updated successfully",
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
    logs = await fetch_all(logs_query, *params)

    return {"logs": logs, "total": total, "page": page, "limit": limit}


# ============================================================================
# USER ACCESSIBLE MODULES
# ============================================================================


async def get_user_accessible_modules(user_id: str) -> List[Dict]:
    """Get modules accessible to user (using view)"""
    modules = await fetch_all(
        """
        SELECT module_id, module_key, module_name, icon, display_order
        FROM user_accessible_modules
        WHERE user_id = $1
        ORDER BY display_order
        """,
        user_id,
    )
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
