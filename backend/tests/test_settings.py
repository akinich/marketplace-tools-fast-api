"""
================================================================================
Farm Management System - Settings Tests
================================================================================
Version: 1.0.0
Last Updated: 2025-11-25

Test Coverage:
- Settings CRUD operations (get all, get by category, update)
- Public settings access
- Admin-only access control
- Validation (data types, ranges, invalid keys)
- Audit log functionality
- Category management

Total Tests: 18

================================================================================
"""

import pytest
from httpx import AsyncClient
from typing import Dict


# ============================================================================
# SETTINGS READ OPERATIONS
# ============================================================================


class TestSettingsRead:
    """Test settings read operations"""

    async def test_get_all_settings(self, client: AsyncClient, admin_headers):
        """Test getting all settings as admin."""
        response = await client.get(
            "/api/v1/settings/",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Verify structure of first setting
        setting = data[0]
        assert "id" in setting
        assert "setting_key" in setting
        assert "setting_value" in setting
        assert "data_type" in setting
        assert "category" in setting
        assert "created_at" in setting
        assert "updated_at" in setting

    async def test_get_public_settings(self, client: AsyncClient, admin_headers):
        """Test getting public settings."""
        response = await client.get(
            "/api/v1/settings/public",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

        # Public settings should include app.name, app.timezone, etc.
        # Check at least some expected public settings exist
        assert any(key.startswith("app.") for key in data.keys())

    async def test_get_categories(self, client: AsyncClient, admin_headers):
        """Test getting setting categories."""
        response = await client.get(
            "/api/v1/settings/categories",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Expected categories from default settings
        expected_categories = ["auth", "email", "webhooks", "app", "features"]
        for category in expected_categories:
            assert category in data

    async def test_get_settings_by_category(self, client: AsyncClient, admin_headers):
        """Test getting settings by specific category."""
        response = await client.get(
            "/api/v1/settings/category/auth",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # All settings should be in 'auth' category
        for setting in data:
            assert setting["category"] == "auth"
            assert setting["setting_key"].startswith("auth.")

    async def test_get_settings_by_nonexistent_category(self, client: AsyncClient, admin_headers):
        """Test getting settings for non-existent category returns empty list."""
        response = await client.get(
            "/api/v1/settings/category/nonexistent",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


# ============================================================================
# SETTINGS UPDATE OPERATIONS
# ============================================================================


class TestSettingsUpdate:
    """Test settings update operations"""

    async def test_update_integer_setting(self, client: AsyncClient, admin_headers):
        """Test updating an integer setting."""
        # Update JWT expiry time
        response = await client.put(
            "/api/v1/settings/auth.jwt_expiry_minutes",
            headers=admin_headers,
            json={"setting_value": 60}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["setting_key"] == "auth.jwt_expiry_minutes"
        assert data["setting_value"] == 60
        assert data["data_type"] == "integer"

    async def test_update_boolean_setting(self, client: AsyncClient, admin_headers):
        """Test updating a boolean setting."""
        # Enable SMTP
        response = await client.put(
            "/api/v1/settings/email.smtp_enabled",
            headers=admin_headers,
            json={"setting_value": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["setting_key"] == "email.smtp_enabled"
        assert data["setting_value"] is True
        assert data["data_type"] == "boolean"

    async def test_update_string_setting(self, client: AsyncClient, admin_headers):
        """Test updating a string setting."""
        # Update app name
        response = await client.put(
            "/api/v1/settings/app.name",
            headers=admin_headers,
            json={"setting_value": "Test Farm System"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["setting_key"] == "app.name"
        assert data["setting_value"] == "Test Farm System"
        assert data["data_type"] == "string"

    async def test_update_nonexistent_setting(self, client: AsyncClient, admin_headers):
        """Test updating a non-existent setting fails."""
        response = await client.put(
            "/api/v1/settings/nonexistent.setting",
            headers=admin_headers,
            json={"setting_value": "test"}
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()


# ============================================================================
# VALIDATION TESTS
# ============================================================================


class TestSettingsValidation:
    """Test settings validation rules"""

    async def test_integer_min_validation(self, client: AsyncClient, admin_headers):
        """Test integer minimum value validation."""
        # auth.jwt_expiry_minutes has min: 5, max: 1440
        response = await client.put(
            "/api/v1/settings/auth.jwt_expiry_minutes",
            headers=admin_headers,
            json={"setting_value": 2}  # Below minimum
        )

        assert response.status_code == 400
        assert "at least" in response.json()["detail"].lower()

    async def test_integer_max_validation(self, client: AsyncClient, admin_headers):
        """Test integer maximum value validation."""
        # auth.jwt_expiry_minutes has min: 5, max: 1440
        response = await client.put(
            "/api/v1/settings/auth.jwt_expiry_minutes",
            headers=admin_headers,
            json={"setting_value": 2000}  # Above maximum
        )

        assert response.status_code == 400
        assert "at most" in response.json()["detail"].lower()

    async def test_invalid_data_type(self, client: AsyncClient, admin_headers):
        """Test invalid data type for integer setting."""
        response = await client.put(
            "/api/v1/settings/auth.jwt_expiry_minutes",
            headers=admin_headers,
            json={"setting_value": "not_a_number"}
        )

        assert response.status_code == 400

    async def test_valid_integer_within_range(self, client: AsyncClient, admin_headers):
        """Test valid integer within range succeeds."""
        # auth.max_login_attempts has min: 3, max: 10
        response = await client.put(
            "/api/v1/settings/auth.max_login_attempts",
            headers=admin_headers,
            json={"setting_value": 7}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["setting_value"] == 7


# ============================================================================
# PERMISSIONS TESTS
# ============================================================================


class TestSettingsPermissions:
    """Test settings access control"""

    async def test_admin_can_access_all_settings(self, client: AsyncClient, admin_headers):
        """Test admin can access all settings."""
        response = await client.get(
            "/api/v1/settings/",
            headers=admin_headers
        )

        assert response.status_code == 200

    async def test_unauthenticated_cannot_access_settings(self, client: AsyncClient):
        """Test unauthenticated users cannot access settings."""
        response = await client.get("/api/v1/settings/")

        assert response.status_code == 403

    async def test_unauthenticated_cannot_update_settings(self, client: AsyncClient):
        """Test unauthenticated users cannot update settings."""
        response = await client.put(
            "/api/v1/settings/app.name",
            json={"setting_value": "Hacked"}
        )

        assert response.status_code == 403


# ============================================================================
# AUDIT LOG TESTS
# ============================================================================


class TestSettingsAuditLog:
    """Test settings audit log functionality"""

    async def test_audit_log_records_changes(self, client: AsyncClient, admin_headers, test_admin_user):
        """Test that setting changes are logged in audit log."""
        # Make a change
        await client.put(
            "/api/v1/settings/auth.jwt_expiry_minutes",
            headers=admin_headers,
            json={"setting_value": 45}
        )

        # Check audit log
        response = await client.get(
            "/api/v1/settings/audit-log",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Find the change we just made
        log_entry = next(
            (entry for entry in data if entry["setting_key"] == "auth.jwt_expiry_minutes"),
            None
        )
        assert log_entry is not None
        assert log_entry["new_value"] == 45
        assert "changed_by" in log_entry
        assert "changed_at" in log_entry

    async def test_audit_log_filter_by_setting_key(self, client: AsyncClient, admin_headers):
        """Test filtering audit log by setting key."""
        # Make a change
        await client.put(
            "/api/v1/settings/auth.max_login_attempts",
            headers=admin_headers,
            json={"setting_value": 8}
        )

        # Get audit log for specific setting
        response = await client.get(
            "/api/v1/settings/audit-log?setting_key=auth.max_login_attempts",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # All entries should be for the requested setting
        for entry in data:
            assert entry["setting_key"] == "auth.max_login_attempts"

    async def test_audit_log_limit(self, client: AsyncClient, admin_headers):
        """Test audit log respects limit parameter."""
        response = await client.get(
            "/api/v1/settings/audit-log?limit=5",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
