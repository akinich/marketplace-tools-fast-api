"""
================================================================================
Farm Management System - Users/Admin Module Tests
================================================================================
Version: 1.0.0
Last Updated: 2025-11-25

Description:
    Tests for user management and admin panel functionality.
    Tests user CRUD, permissions, modules, roles, and activity logs.

Test Coverage:
    - User CRUD operations (list, create, update, delete)
    - Soft delete and hard delete
    - User permissions management
    - Module management (list, update, toggle status)
    - Role management
    - Activity logs with filtering
    - Admin statistics
    - Access control (admin-only endpoints)

================================================================================
"""

import pytest
from httpx import AsyncClient
from typing import Dict
from app.database import fetch_one, execute_query


# ============================================================================
# USER MANAGEMENT TESTS
# ============================================================================


@pytest.mark.integration
class TestUserManagement:
    """Test user management operations."""

    async def test_list_users(self, client: AsyncClient, admin_headers):
        """Test listing all users."""
        response = await client.get("/api/v1/admin/users", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert len(data["users"]) > 0

    async def test_list_users_requires_admin(self, client: AsyncClient, user_headers):
        """Test that listing users requires admin privileges."""
        response = await client.get("/api/v1/admin/users", headers=user_headers)

        assert response.status_code == 403

    async def test_list_users_with_pagination(self, client: AsyncClient, admin_headers):
        """Test user listing with pagination."""
        response = await client.get(
            "/api/v1/admin/users?page=1&limit=5", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["limit"] == 5

    async def test_filter_users_by_active_status(
        self, client: AsyncClient, admin_headers
    ):
        """Test filtering users by active status."""
        response = await client.get(
            "/api/v1/admin/users?is_active=true", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        # All returned users should be active
        for user in data["users"]:
            assert user["is_active"] is True

    async def test_filter_users_by_role(self, client: AsyncClient, admin_headers):
        """Test filtering users by role."""
        response = await client.get(
            "/api/v1/admin/users?role=Admin", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        # All returned users should be Admins
        for user in data["users"]:
            assert user["role_name"] == "Admin"

    async def test_create_user(self, client: AsyncClient, admin_headers):
        """Test creating a new user."""
        user_data = {
            "email": "newuser@test.com",
            "full_name": "New Test User",
            "role_id": 2,  # User role
            "temporary_password": "TempPass123!",
        }

        response = await client.post(
            "/api/v1/admin/users", headers=admin_headers, json=user_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == "newuser@test.com"
        assert data["user"]["full_name"] == "New Test User"
        assert data["user"]["must_change_password"] is True
        assert "temporary_password" in data

    async def test_create_user_requires_admin(self, client: AsyncClient, user_headers):
        """Test that creating users requires admin privileges."""
        user_data = {
            "email": "hacker@test.com",
            "full_name": "Hacker",
            "role_id": 1,
            "temporary_password": "HackPass123!",
        }

        response = await client.post(
            "/api/v1/admin/users", headers=user_headers, json=user_data
        )

        assert response.status_code == 403

    async def test_create_user_with_duplicate_email(
        self, client: AsyncClient, admin_headers, test_admin_user
    ):
        """Test that creating user with duplicate email fails."""
        user_data = {
            "email": test_admin_user["email"],  # Already exists
            "full_name": "Duplicate User",
            "role_id": 2,
            "temporary_password": "TempPass123!",
        }

        response = await client.post(
            "/api/v1/admin/users", headers=admin_headers, json=user_data
        )

        assert response.status_code == 400

    async def test_update_user(self, client: AsyncClient, admin_headers):
        """Test updating a user."""
        # First create a user
        user_data = {
            "email": "updateme@test.com",
            "full_name": "Original Name",
            "role_id": 2,
            "temporary_password": "TempPass123!",
        }
        create_response = await client.post(
            "/api/v1/admin/users", headers=admin_headers, json=user_data
        )
        user_id = create_response.json()["user"]["id"]

        # Update the user
        update_data = {"full_name": "Updated Name", "is_active": True}
        response = await client.put(
            f"/api/v1/admin/users/{user_id}", headers=admin_headers, json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"

    async def test_soft_delete_user(self, client: AsyncClient, admin_headers):
        """Test soft deleting a user (deactivation)."""
        # Create a user
        user_data = {
            "email": "softdelete@test.com",
            "full_name": "To Be Deactivated",
            "role_id": 2,
            "temporary_password": "TempPass123!",
        }
        create_response = await client.post(
            "/api/v1/admin/users", headers=admin_headers, json=user_data
        )
        user_id = create_response.json()["user"]["id"]

        # Soft delete (deactivate)
        response = await client.delete(
            f"/api/v1/admin/users/{user_id}", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "deactivated" in data["message"].lower()

        # Verify user still exists but is inactive
        user = await fetch_one(
            "SELECT is_active FROM user_profiles WHERE id = $1", user_id
        )
        assert user is not None
        assert user["is_active"] is False

    async def test_hard_delete_user(self, client: AsyncClient, admin_headers):
        """Test hard deleting a user (permanent removal)."""
        # Create a user
        user_data = {
            "email": "harddelete@test.com",
            "full_name": "To Be Permanently Deleted",
            "role_id": 2,
            "temporary_password": "TempPass123!",
        }
        create_response = await client.post(
            "/api/v1/admin/users", headers=admin_headers, json=user_data
        )
        user_id = create_response.json()["user"]["id"]

        # Hard delete
        response = await client.delete(
            f"/api/v1/admin/users/{user_id}?hard_delete=true", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "permanently deleted" in data["message"].lower()

        # Verify user is completely gone
        user = await fetch_one(
            "SELECT * FROM user_profiles WHERE id = $1", user_id
        )
        assert user is None

    async def test_delete_user_requires_admin(
        self, client: AsyncClient, user_headers, test_admin_user
    ):
        """Test that deleting users requires admin privileges."""
        response = await client.delete(
            f"/api/v1/admin/users/{test_admin_user['id']}", headers=user_headers
        )

        assert response.status_code == 403


# ============================================================================
# ROLE MANAGEMENT TESTS
# ============================================================================


@pytest.mark.integration
class TestRoleManagement:
    """Test role management operations."""

    async def test_list_roles(self, client: AsyncClient, admin_headers):
        """Test listing all roles."""
        response = await client.get("/api/v1/admin/roles", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "roles" in data
        assert len(data["roles"]) >= 2  # At least Admin and User roles

        # Verify Admin and User roles exist
        role_names = [role["role_name"] for role in data["roles"]]
        assert "Admin" in role_names
        assert "User" in role_names

    async def test_list_roles_requires_admin(self, client: AsyncClient, user_headers):
        """Test that listing roles requires admin privileges."""
        response = await client.get("/api/v1/admin/roles", headers=user_headers)

        assert response.status_code == 403


# ============================================================================
# MODULE MANAGEMENT TESTS
# ============================================================================


@pytest.mark.integration
class TestModuleManagement:
    """Test module management operations."""

    async def test_list_modules(self, client: AsyncClient, admin_headers):
        """Test listing all modules."""
        response = await client.get("/api/v1/admin/modules", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "modules" in data
        assert len(data["modules"]) > 0

        # Modules should have required fields
        for module in data["modules"]:
            assert "id" in module
            assert "module_key" in module
            assert "module_name" in module
            assert "is_active" in module

    async def test_update_module(self, client: AsyncClient, admin_headers):
        """Test updating a module."""
        # First get a module
        modules_response = await client.get(
            "/api/v1/admin/modules", headers=admin_headers
        )
        modules = modules_response.json()["modules"]
        module_id = modules[0]["id"]

        # Update it
        update_data = {"is_active": True, "display_order": 1}
        response = await client.put(
            f"/api/v1/admin/modules/{module_id}",
            headers=admin_headers,
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    async def test_disable_module(self, client: AsyncClient, admin_headers):
        """Test disabling a module."""
        # Get a non-critical module
        modules_response = await client.get(
            "/api/v1/admin/modules", headers=admin_headers
        )
        modules = modules_response.json()["modules"]

        # Find a module that's not 'admin' or 'auth' (critical modules)
        target_module = None
        for module in modules:
            if module["module_key"] not in ["admin", "auth"]:
                target_module = module
                break

        if target_module:
            update_data = {"is_active": False}
            response = await client.put(
                f"/api/v1/admin/modules/{target_module['id']}",
                headers=admin_headers,
                json=update_data,
            )

            assert response.status_code == 200

    async def test_get_module_users_count(self, client: AsyncClient, admin_headers):
        """Test getting users count for a module."""
        # Get a module
        modules_response = await client.get(
            "/api/v1/admin/modules", headers=admin_headers
        )
        module_id = modules_response.json()["modules"][0]["id"]

        # Get users count
        response = await client.get(
            f"/api/v1/admin/modules/{module_id}/users-count", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "users_count" in data
        assert "module_key" in data

    async def test_module_operations_require_admin(
        self, client: AsyncClient, user_headers
    ):
        """Test that module operations require admin privileges."""
        # List modules
        response = await client.get("/api/v1/admin/modules", headers=user_headers)
        assert response.status_code == 403

        # Update module
        update_data = {"is_active": False}
        response = await client.put(
            "/api/v1/admin/modules/1", headers=user_headers, json=update_data
        )
        assert response.status_code == 403


# ============================================================================
# PERMISSION MANAGEMENT TESTS
# ============================================================================


@pytest.mark.integration
class TestPermissionManagement:
    """Test user permission management operations."""

    async def test_get_user_permissions(
        self, client: AsyncClient, admin_headers, test_regular_user
    ):
        """Test getting a user's permissions."""
        response = await client.get(
            f"/api/v1/admin/permissions/{test_regular_user['id']}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "permissions" in data

    async def test_update_user_permissions(
        self, client: AsyncClient, admin_headers
    ):
        """Test updating a user's permissions."""
        # Create a user
        user_data = {
            "email": "permstest@test.com",
            "full_name": "Permissions Test User",
            "role_id": 2,
            "temporary_password": "TempPass123!",
        }
        create_response = await client.post(
            "/api/v1/admin/users", headers=admin_headers, json=user_data
        )
        user_id = create_response.json()["user"]["id"]

        # Get available modules
        modules_response = await client.get(
            "/api/v1/admin/modules", headers=admin_headers
        )
        module_ids = [m["id"] for m in modules_response.json()["modules"][:2]]

        # Update permissions
        perms_data = {"module_ids": module_ids}
        response = await client.put(
            f"/api/v1/admin/permissions/{user_id}",
            headers=admin_headers,
            json=perms_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert "granted" in data["message"].lower()

    async def test_get_user_accessible_modules(
        self, client: AsyncClient, admin_headers, test_admin_user
    ):
        """Test getting modules accessible to a user."""
        response = await client.get(
            f"/api/v1/admin/user-modules/{test_admin_user['id']}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "modules" in data

    async def test_permission_operations_require_admin(
        self, client: AsyncClient, user_headers, test_regular_user
    ):
        """Test that permission operations require admin privileges."""
        # Get permissions
        response = await client.get(
            f"/api/v1/admin/permissions/{test_regular_user['id']}",
            headers=user_headers,
        )
        assert response.status_code == 403

        # Update permissions
        perms_data = {"module_ids": [1, 2]}
        response = await client.put(
            f"/api/v1/admin/permissions/{test_regular_user['id']}",
            headers=user_headers,
            json=perms_data,
        )
        assert response.status_code == 403


# ============================================================================
# ACTIVITY LOG TESTS
# ============================================================================


@pytest.mark.integration
class TestActivityLogs:
    """Test activity logging functionality."""

    async def test_get_activity_logs(self, client: AsyncClient, admin_headers):
        """Test getting activity logs."""
        response = await client.get(
            "/api/v1/admin/activity-logs", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data

    async def test_filter_activity_logs_by_days(
        self, client: AsyncClient, admin_headers
    ):
        """Test filtering activity logs by days."""
        response = await client.get(
            "/api/v1/admin/activity-logs?days=7", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "logs" in data

    async def test_filter_activity_logs_by_user(
        self, client: AsyncClient, admin_headers, test_admin_user
    ):
        """Test filtering activity logs by user."""
        response = await client.get(
            f"/api/v1/admin/activity-logs?user_id={test_admin_user['id']}",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # All logs should be for the specified user
        for log in data["logs"]:
            if log.get("user_id"):
                assert log["user_id"] == test_admin_user["id"]

    async def test_filter_activity_logs_by_module(
        self, client: AsyncClient, admin_headers
    ):
        """Test filtering activity logs by module."""
        response = await client.get(
            "/api/v1/admin/activity-logs?module_key=admin", headers=admin_headers
        )

        assert response.status_code == 200

    async def test_filter_activity_logs_by_action_type(
        self, client: AsyncClient, admin_headers
    ):
        """Test filtering activity logs by action type."""
        response = await client.get(
            "/api/v1/admin/activity-logs?action_type=create_user",
            headers=admin_headers,
        )

        assert response.status_code == 200

    async def test_activity_logs_pagination(self, client: AsyncClient, admin_headers):
        """Test activity logs pagination."""
        response = await client.get(
            "/api/v1/admin/activity-logs?page=1&limit=20", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["limit"] == 20

    async def test_activity_logs_require_admin(self, client: AsyncClient, user_headers):
        """Test that activity logs require admin privileges."""
        response = await client.get(
            "/api/v1/admin/activity-logs", headers=user_headers
        )

        assert response.status_code == 403


# ============================================================================
# STATISTICS TESTS
# ============================================================================


@pytest.mark.integration
class TestAdminStatistics:
    """Test admin statistics endpoint."""

    async def test_get_admin_statistics(self, client: AsyncClient, admin_headers):
        """Test getting admin statistics."""
        response = await client.get(
            "/api/v1/admin/statistics", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Check for expected statistics
        assert "total_users" in data or "users" in data
        assert isinstance(data, dict)

    async def test_statistics_require_admin(self, client: AsyncClient, user_headers):
        """Test that statistics require admin privileges."""
        response = await client.get(
            "/api/v1/admin/statistics", headers=user_headers
        )

        assert response.status_code == 403


# ============================================================================
# ACCOUNT UNLOCK TESTS
# ============================================================================


@pytest.mark.integration
class TestAccountUnlock:
    """Test account unlocking functionality."""

    async def test_unlock_user_account(self, client: AsyncClient, admin_headers):
        """Test unlocking a locked user account."""
        # Create a user
        user_data = {
            "email": "lockeduser@test.com",
            "full_name": "Locked User",
            "role_id": 2,
            "temporary_password": "TempPass123!",
        }
        create_response = await client.post(
            "/api/v1/admin/users", headers=admin_headers, json=user_data
        )
        user_id = create_response.json()["user"]["id"]

        # Simulate account being locked (would normally happen after failed logins)
        await execute_query(
            "UPDATE user_profiles SET locked_until = NOW() + INTERVAL '30 minutes' WHERE id = $1",
            user_id,
        )

        # Unlock the account
        response = await client.post(
            f"/api/v1/admin/users/{user_id}/unlock", headers=admin_headers
        )

        assert response.status_code == 200

    async def test_unlock_account_requires_admin(
        self, client: AsyncClient, user_headers, test_admin_user
    ):
        """Test that unlocking accounts requires admin privileges."""
        response = await client.post(
            f"/api/v1/admin/users/{test_admin_user['id']}/unlock",
            headers=user_headers,
        )

        assert response.status_code == 403
