"""
================================================================================
Farm Management System - Admin Panel Schemas
================================================================================
Version: 1.0.0
Last Updated: 2025-11-17

Changelog:
----------
v1.0.0 (2025-11-17):
  - Initial admin panel Pydantic models
  - User management schemas
  - Role and permission schemas
  - Activity log schemas
  - Module management schemas

================================================================================
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# USER MANAGEMENT SCHEMAS
# ============================================================================


class UserListItem(BaseModel):
    """User list item (for GET /admin/users)"""

    id: str
    email: str
    full_name: str
    role_id: int
    role_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UsersListResponse(BaseModel):
    """Paginated users list response"""

    users: List[UserListItem]
    total: int
    page: int
    limit: int
    total_pages: int


class CreateUserRequest(BaseModel):
    """Create new user request"""

    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")
    role_id: int = Field(..., ge=1, description="Role ID (1=Admin, 2=User)")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "newuser@example.com",
                "full_name": "Jane Smith",
                "role_id": 2,
            }
        }


class CreateUserResponse(BaseModel):
    """Create user response"""

    user: UserListItem
    temporary_password: str = Field(..., description="Auto-generated temporary password")

    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "id": "uuid",
                    "email": "newuser@example.com",
                    "full_name": "Jane Smith",
                    "role_id": 2,
                    "role_name": "User",
                    "is_active": True,
                    "created_at": "2025-11-17T10:00:00Z",
                },
                "temporary_password": "TempPass123!",
            }
        }


class UpdateUserRequest(BaseModel):
    """Update user request"""

    full_name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Full name"
    )
    role_id: Optional[int] = Field(None, ge=1, description="Role ID")
    is_active: Optional[bool] = Field(None, description="Active status")

    class Config:
        json_schema_extra = {
            "example": {"full_name": "Jane Doe", "role_id": 1, "is_active": True}
        }


class UpdateUserResponse(BaseModel):
    """Update user response"""

    user: UserListItem


class DeleteUserResponse(BaseModel):
    """Delete user response"""

    message: str = Field(default="User deleted successfully")


# ============================================================================
# ROLE SCHEMAS
# ============================================================================


class RoleItem(BaseModel):
    """Role item"""

    id: int
    role_name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class RolesListResponse(BaseModel):
    """Roles list response"""

    roles: List[RoleItem]


# ============================================================================
# MODULE SCHEMAS
# ============================================================================


class ModuleItem(BaseModel):
    """Module item"""

    id: int
    module_key: str
    module_name: str
    description: Optional[str]
    icon: str
    display_order: int
    is_active: bool

    class Config:
        from_attributes = True


class ModulesListResponse(BaseModel):
    """Modules list response"""

    modules: List[ModuleItem]


class UpdateModuleRequest(BaseModel):
    """Update module request"""

    is_active: Optional[bool] = Field(None, description="Active status")
    display_order: Optional[int] = Field(None, ge=0, description="Display order")

    class Config:
        json_schema_extra = {"example": {"is_active": True, "display_order": 2}}


# ============================================================================
# PERMISSION SCHEMAS
# ============================================================================


class ModulePermissionItem(BaseModel):
    """Module permission item"""

    module_id: int
    module_key: str
    module_name: str
    can_access: bool


class UserPermissionsResponse(BaseModel):
    """User's module permissions response"""

    user_id: str
    permissions: List[ModulePermissionItem]


class UpdatePermissionsRequest(BaseModel):
    """Update user permissions request"""

    module_ids: List[int] = Field(
        ..., description="List of module IDs to grant access to"
    )

    class Config:
        json_schema_extra = {"example": {"module_ids": [1, 2, 3]}}


class UpdatePermissionsResponse(BaseModel):
    """Update permissions response"""

    message: str = Field(default="Permissions updated successfully")
    granted_modules: List[str] = Field(
        ..., description="List of granted module keys"
    )


# ============================================================================
# ACTIVITY LOG SCHEMAS
# ============================================================================


class ActivityLogItem(BaseModel):
    """Activity log item"""

    id: int
    user_email: str
    user_role: str
    action_type: str
    module_key: Optional[str]
    description: str
    metadata: Optional[Dict[str, Any]]
    success: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityLogsResponse(BaseModel):
    """Activity logs response"""

    logs: List[ActivityLogItem]
    total: int
    page: int
    limit: int


# ============================================================================
# USER MODULES ACCESS SCHEMAS
# ============================================================================


class UserModuleItem(BaseModel):
    """User's accessible module"""

    module_id: int
    module_key: str
    module_name: str
    icon: str
    display_order: int


class UserModulesResponse(BaseModel):
    """User's accessible modules response"""

    modules: List[UserModuleItem]


# ============================================================================
# STATISTICS SCHEMAS
# ============================================================================


class AdminStatsResponse(BaseModel):
    """Admin panel statistics"""

    total_users: int
    active_users: int
    inactive_users: int
    total_admin: int
    total_regular_users: int
    recent_logins_24h: int
    total_activities_7d: int

    class Config:
        json_schema_extra = {
            "example": {
                "total_users": 25,
                "active_users": 23,
                "inactive_users": 2,
                "total_admin": 3,
                "total_regular_users": 22,
                "recent_logins_24h": 15,
                "total_activities_7d": 1250,
            }
        }
