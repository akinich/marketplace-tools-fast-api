"""
================================================================================
Farm Management System - Admin Panel Routes
================================================================================
Version: 1.0.0
Last Updated: 2025-11-17

Changelog:
----------
v1.0.0 (2025-11-17):
  - Initial admin panel endpoints
  - User management (CRUD)
  - Role management
  - Module management
  - Permission management
  - Activity logs
  - Admin statistics

================================================================================
"""

from fastapi import APIRouter, Depends, Query, status
from typing import Optional

from app.schemas.admin import *
from app.schemas.auth import CurrentUser, ErrorResponse
from app.auth.dependencies import require_admin
from app.services import admin_service

router = APIRouter()


# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================


@router.get(
    "/users",
    response_model=UsersListResponse,
    summary="List Users",
    description="Get paginated list of all users (Admin only)",
)
async def list_users(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    role: Optional[str] = Query(None, description="Filter by role name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    admin: CurrentUser = Depends(require_admin),
):
    """List all users with optional filters"""
    result = await admin_service.get_users_list(
        is_active=is_active, role=role, page=page, limit=limit
    )
    return result


@router.post(
    "/users",
    response_model=CreateUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User",
    description="Create new user with temporary password (Admin only)",
)
async def create_user(
    request: CreateUserRequest,
    admin: CurrentUser = Depends(require_admin),
):
    """Create new user"""
    result = await admin_service.create_user(request, admin.id)
    return result


@router.put(
    "/users/{user_id}",
    response_model=UpdateUserResponse,
    summary="Update User",
    description="Update user information (Admin only)",
)
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    admin: CurrentUser = Depends(require_admin),
):
    """Update user"""
    result = await admin_service.update_user(user_id, request, admin.id)
    return result


@router.delete(
    "/users/{user_id}",
    response_model=DeleteUserResponse,
    summary="Delete User",
    description="Delete/deactivate user (Admin only)",
)
async def delete_user(
    user_id: str,
    admin: CurrentUser = Depends(require_admin),
):
    """Delete user (soft delete - deactivate)"""
    await admin_service.delete_user(user_id, admin.id)
    return DeleteUserResponse(message="User deleted successfully")


# ============================================================================
# ROLE MANAGEMENT ENDPOINTS
# ============================================================================


@router.get(
    "/roles",
    response_model=RolesListResponse,
    summary="List Roles",
    description="Get all available roles",
)
async def list_roles(admin: CurrentUser = Depends(require_admin)):
    """List all roles"""
    roles = await admin_service.get_roles_list()
    return {"roles": roles}


# ============================================================================
# MODULE MANAGEMENT ENDPOINTS
# ============================================================================


@router.get(
    "/modules",
    response_model=ModulesListResponse,
    summary="List Modules",
    description="Get all system modules",
)
async def list_modules(admin: CurrentUser = Depends(require_admin)):
    """List all modules"""
    modules = await admin_service.get_modules_list()
    return {"modules": modules}


@router.put(
    "/modules/{module_id}",
    response_model=ModuleItem,
    summary="Update Module",
    description="Update module settings (enable/disable, reorder)",
)
async def update_module(
    module_id: int,
    request: UpdateModuleRequest,
    admin: CurrentUser = Depends(require_admin),
):
    """Update module"""
    module = await admin_service.update_module(module_id, request)
    return module


# ============================================================================
# PERMISSION MANAGEMENT ENDPOINTS
# ============================================================================


@router.get(
    "/permissions/{user_id}",
    response_model=UserPermissionsResponse,
    summary="Get User Permissions",
    description="Get user's module permissions",
)
async def get_user_permissions(
    user_id: str,
    admin: CurrentUser = Depends(require_admin),
):
    """Get user permissions"""
    result = await admin_service.get_user_permissions(user_id)
    return result


@router.put(
    "/permissions/{user_id}",
    response_model=UpdatePermissionsResponse,
    summary="Update User Permissions",
    description="Update user's module permissions (bulk replace)",
)
async def update_user_permissions(
    user_id: str,
    request: UpdatePermissionsRequest,
    admin: CurrentUser = Depends(require_admin),
):
    """Update user permissions"""
    result = await admin_service.update_user_permissions(user_id, request, admin.id)
    return result


# ============================================================================
# ACTIVITY LOG ENDPOINTS
# ============================================================================


@router.get(
    "/activity-logs",
    response_model=ActivityLogsResponse,
    summary="Get Activity Logs",
    description="Get system activity logs with filters",
)
async def get_activity_logs(
    days: int = Query(7, ge=1, le=90, description="Days back to fetch"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    module_key: Optional[str] = Query(None, description="Filter by module"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=500, description="Items per page"),
    admin: CurrentUser = Depends(require_admin),
):
    """Get activity logs"""
    result = await admin_service.get_activity_logs(
        days=days,
        user_id=user_id,
        module_key=module_key,
        action_type=action_type,
        page=page,
        limit=limit,
    )
    return result


# ============================================================================
# USER MODULES ENDPOINT
# ============================================================================


@router.get(
    "/user-modules/{user_id}",
    response_model=UserModulesResponse,
    summary="Get User Accessible Modules",
    description="Get modules accessible to a specific user",
)
async def get_user_modules(
    user_id: str,
    admin: CurrentUser = Depends(require_admin),
):
    """Get user's accessible modules"""
    modules = await admin_service.get_user_accessible_modules(user_id)
    return {"modules": modules}


# ============================================================================
# STATISTICS ENDPOINT
# ============================================================================


@router.get(
    "/statistics",
    response_model=AdminStatsResponse,
    summary="Get Admin Statistics",
    description="Get admin panel statistics and metrics",
)
async def get_statistics(admin: CurrentUser = Depends(require_admin)):
    """Get admin statistics"""
    stats = await admin_service.get_admin_statistics()
    return stats
