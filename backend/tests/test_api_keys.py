"""
================================================================================
Farm Management System - API Keys Module Tests
================================================================================
Version: 1.0.0
Last Updated: 2025-11-25

Description:
    Tests for API key management system - creation, revocation, usage tracking.
    Tests scope validation, expiration, and admin operations.

Test Coverage:
    - API key CRUD operations (list, create, revoke)
    - Scope management and validation
    - Key expiration
    - Usage tracking and logs
    - Admin operations (list all, revoke any)
    - Access control and permissions
    - Key prefix generation

================================================================================
"""

import pytest
from httpx import AsyncClient
from typing import Dict
from app.database import fetch_one, fetch_all


# ============================================================================
# API KEY LIST TESTS
# ============================================================================


@pytest.mark.integration
class TestAPIKeyList:
    """Test API key listing endpoints."""

    async def test_list_my_api_keys(
        self, client: AsyncClient, user_headers
    ):
        """Test listing current user's API keys."""
        response = await client.get("/api/v1/api-keys/", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All keys should belong to the current user
        # (empty list is valid if no keys created yet)

    async def test_list_api_keys_without_auth(self, client: AsyncClient):
        """Test listing API keys without authentication."""
        response = await client.get("/api/v1/api-keys/")

        assert response.status_code == 403

    async def test_list_api_keys_shows_no_full_key(
        self, client: AsyncClient, user_headers
    ):
        """Test that listing API keys doesn't expose full keys."""
        # First create a key
        key_data = {
            "name": "Test Key",
            "scopes": ["inventory:read"],
            "description": "Testing key list",
            "expires_in_days": 30,
        }
        await client.post("/api/v1/api-keys/", headers=user_headers, json=key_data)

        # List keys
        response = await client.get("/api/v1/api-keys/", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        for key in data:
            # Should have prefix but not full api_key
            assert "key_prefix" in key
            assert "api_key" not in key  # Full key never exposed in list


# ============================================================================
# API KEY CREATION TESTS
# ============================================================================


@pytest.mark.integration
class TestAPIKeyCreation:
    """Test API key creation."""

    async def test_create_api_key(self, client: AsyncClient, user_headers):
        """Test creating a new API key."""
        key_data = {
            "name": "Test API Key",
            "scopes": ["inventory:read", "inventory:write"],
            "description": "For automated testing",
            "expires_in_days": 30,
        }

        response = await client.post(
            "/api/v1/api-keys/", headers=user_headers, json=key_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test API Key"
        assert "api_key" in data  # Full key shown only once
        assert data["api_key"].startswith("farm_")  # Check prefix format
        assert "key_prefix" in data
        assert set(data["scopes"]) == {"inventory:read", "inventory:write"}

    async def test_create_api_key_without_auth(self, client: AsyncClient):
        """Test creating API key without authentication."""
        key_data = {
            "name": "Unauthorized Key",
            "scopes": ["inventory:read"],
        }

        response = await client.post("/api/v1/api-keys/", json=key_data)

        assert response.status_code == 403

    async def test_create_api_key_with_invalid_scopes(
        self, client: AsyncClient, user_headers
    ):
        """Test creating API key with invalid scopes."""
        key_data = {
            "name": "Invalid Scopes Key",
            "scopes": ["invalid:scope", "hacker:access"],
        }

        response = await client.post(
            "/api/v1/api-keys/", headers=user_headers, json=key_data
        )

        assert response.status_code == 400

    async def test_create_api_key_with_wildcard_scope(
        self, client: AsyncClient, user_headers
    ):
        """Test creating API key with wildcard scope."""
        key_data = {
            "name": "Wildcard Key",
            "scopes": ["inventory:*"],
            "expires_in_days": 30,
        }

        response = await client.post(
            "/api/v1/api-keys/", headers=user_headers, json=key_data
        )

        assert response.status_code == 201
        data = response.json()
        assert "inventory:*" in data["scopes"]

    async def test_create_api_key_with_custom_expiry(
        self, client: AsyncClient, user_headers
    ):
        """Test creating API key with custom expiration."""
        key_data = {
            "name": "Short-lived Key",
            "scopes": ["tickets:read"],
            "expires_in_days": 7,
        }

        response = await client.post(
            "/api/v1/api-keys/", headers=user_headers, json=key_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["expires_at"] is not None

    async def test_create_api_key_without_description(
        self, client: AsyncClient, user_headers
    ):
        """Test creating API key without description (optional field)."""
        key_data = {
            "name": "No Description Key",
            "scopes": ["dashboard:read"],
        }

        response = await client.post(
            "/api/v1/api-keys/", headers=user_headers, json=key_data
        )

        assert response.status_code == 201


# ============================================================================
# API KEY REVOCATION TESTS
# ============================================================================


@pytest.mark.integration
class TestAPIKeyRevocation:
    """Test API key revocation."""

    async def test_revoke_own_api_key(self, client: AsyncClient, user_headers):
        """Test revoking own API key."""
        # Create a key
        key_data = {
            "name": "Key to Revoke",
            "scopes": ["inventory:read"],
        }
        create_response = await client.post(
            "/api/v1/api-keys/", headers=user_headers, json=key_data
        )
        key_id = create_response.json()["id"]

        # Revoke it
        response = await client.delete(
            f"/api/v1/api-keys/{key_id}", headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "revoked" in data["message"].lower()

        # Verify it's revoked in database
        key = await fetch_one(
            "SELECT is_active, revoked_at FROM api_keys WHERE id = $1", key_id
        )
        assert key["is_active"] is False
        assert key["revoked_at"] is not None

    async def test_revoke_nonexistent_key(self, client: AsyncClient, user_headers):
        """Test revoking a key that doesn't exist."""
        response = await client.delete("/api/v1/api-keys/99999", headers=user_headers)

        assert response.status_code == 404

    async def test_revoke_other_users_key(
        self, client: AsyncClient, user_headers, admin_headers
    ):
        """Test that users cannot revoke other users' keys."""
        # Admin creates a key
        key_data = {
            "name": "Admin's Key",
            "scopes": ["users:read"],
        }
        create_response = await client.post(
            "/api/v1/api-keys/", headers=admin_headers, json=key_data
        )
        key_id = create_response.json()["id"]

        # Regular user tries to revoke it (should fail)
        response = await client.delete(
            f"/api/v1/api-keys/{key_id}", headers=user_headers
        )

        assert response.status_code == 404  # Returns 404 to avoid info leak

    async def test_revoke_already_revoked_key(
        self, client: AsyncClient, user_headers
    ):
        """Test revoking an already revoked key."""
        # Create and revoke a key
        key_data = {
            "name": "Double Revoke Test",
            "scopes": ["inventory:read"],
        }
        create_response = await client.post(
            "/api/v1/api-keys/", headers=user_headers, json=key_data
        )
        key_id = create_response.json()["id"]

        # First revocation
        await client.delete(f"/api/v1/api-keys/{key_id}", headers=user_headers)

        # Second revocation (should still succeed or return 404)
        response = await client.delete(
            f"/api/v1/api-keys/{key_id}", headers=user_headers
        )

        assert response.status_code in [200, 404]


# ============================================================================
# SCOPE MANAGEMENT TESTS
# ============================================================================


@pytest.mark.integration
class TestScopeManagement:
    """Test API key scope functionality."""

    async def test_get_available_scopes(self, client: AsyncClient, user_headers):
        """Test getting list of available scopes."""
        response = await client.get(
            "/api/v1/api-keys/scopes/available", headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "scopes" in data
        assert isinstance(data["scopes"], list)
        assert len(data["scopes"]) > 0

        # Check for expected scopes
        scopes = data["scopes"]
        assert "inventory:read" in scopes or any("inventory" in s for s in scopes)

    async def test_available_scopes_without_auth(self, client: AsyncClient):
        """Test that scopes list requires authentication."""
        response = await client.get("/api/v1/api-keys/scopes/available")

        assert response.status_code == 403

    async def test_create_key_with_multiple_scopes(
        self, client: AsyncClient, user_headers
    ):
        """Test creating API key with multiple scopes."""
        key_data = {
            "name": "Multi-Scope Key",
            "scopes": [
                "inventory:read",
                "inventory:write",
                "tickets:read",
                "dashboard:read",
            ],
        }

        response = await client.post(
            "/api/v1/api-keys/", headers=user_headers, json=key_data
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["scopes"]) == 4


# ============================================================================
# USAGE TRACKING TESTS
# ============================================================================


@pytest.mark.integration
class TestAPIKeyUsage:
    """Test API key usage tracking."""

    async def test_get_api_key_usage(self, client: AsyncClient, user_headers):
        """Test getting usage logs for an API key."""
        # Create a key
        key_data = {
            "name": "Usage Test Key",
            "scopes": ["inventory:read"],
        }
        create_response = await client.post(
            "/api/v1/api-keys/", headers=user_headers, json=key_data
        )
        key_id = create_response.json()["id"]

        # Get usage (might be empty if key not used yet)
        response = await client.get(
            f"/api/v1/api-keys/{key_id}/usage", headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_usage_for_nonexistent_key(
        self, client: AsyncClient, user_headers
    ):
        """Test getting usage for non-existent key."""
        response = await client.get(
            "/api/v1/api-keys/99999/usage", headers=user_headers
        )

        assert response.status_code == 404

    async def test_get_usage_for_other_users_key(
        self, client: AsyncClient, user_headers, admin_headers
    ):
        """Test that users cannot view other users' key usage."""
        # Admin creates a key
        key_data = {
            "name": "Admin Usage Key",
            "scopes": ["users:read"],
        }
        create_response = await client.post(
            "/api/v1/api-keys/", headers=admin_headers, json=key_data
        )
        key_id = create_response.json()["id"]

        # Regular user tries to view usage (should fail)
        response = await client.get(
            f"/api/v1/api-keys/{key_id}/usage", headers=user_headers
        )

        assert response.status_code == 404

    async def test_get_usage_with_limit(self, client: AsyncClient, user_headers):
        """Test getting usage logs with custom limit."""
        # Create a key
        key_data = {
            "name": "Limited Usage Key",
            "scopes": ["inventory:read"],
        }
        create_response = await client.post(
            "/api/v1/api-keys/", headers=user_headers, json=key_data
        )
        key_id = create_response.json()["id"]

        # Get usage with limit
        response = await client.get(
            f"/api/v1/api-keys/{key_id}/usage?limit=10", headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10


# ============================================================================
# ADMIN OPERATIONS TESTS
# ============================================================================


@pytest.mark.integration
class TestAdminAPIKeyOperations:
    """Test admin-only API key operations."""

    async def test_admin_list_all_api_keys(self, client: AsyncClient, admin_headers):
        """Test admin listing all API keys."""
        response = await client.get(
            "/api/v1/api-keys/admin/all", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_regular_user_cannot_list_all_keys(
        self, client: AsyncClient, user_headers
    ):
        """Test that regular users cannot list all API keys."""
        response = await client.get(
            "/api/v1/api-keys/admin/all", headers=user_headers
        )

        assert response.status_code == 403

    async def test_admin_revoke_any_key(
        self, client: AsyncClient, user_headers, admin_headers
    ):
        """Test that admin can revoke any user's API key."""
        # Regular user creates a key
        key_data = {
            "name": "User's Key",
            "scopes": ["inventory:read"],
        }
        create_response = await client.post(
            "/api/v1/api-keys/", headers=user_headers, json=key_data
        )
        key_id = create_response.json()["id"]

        # Admin revokes it
        response = await client.delete(
            f"/api/v1/api-keys/admin/{key_id}", headers=admin_headers
        )

        assert response.status_code == 200

    async def test_regular_user_cannot_use_admin_revoke(
        self, client: AsyncClient, user_headers, admin_headers
    ):
        """Test that regular users cannot use admin revoke endpoint."""
        # Admin creates a key
        key_data = {
            "name": "Protected Key",
            "scopes": ["users:write"],
        }
        create_response = await client.post(
            "/api/v1/api-keys/", headers=admin_headers, json=key_data
        )
        key_id = create_response.json()["id"]

        # Regular user tries to revoke via admin endpoint (should fail)
        response = await client.delete(
            f"/api/v1/api-keys/admin/{key_id}", headers=user_headers
        )

        assert response.status_code == 403


# ============================================================================
# KEY EXPIRATION TESTS
# ============================================================================


@pytest.mark.integration
class TestAPIKeyExpiration:
    """Test API key expiration functionality."""

    async def test_create_key_with_expiration(
        self, client: AsyncClient, user_headers
    ):
        """Test creating API key with expiration date."""
        key_data = {
            "name": "Expiring Key",
            "scopes": ["inventory:read"],
            "expires_in_days": 1,  # Expires in 1 day
        }

        response = await client.post(
            "/api/v1/api-keys/", headers=user_headers, json=key_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["expires_at"] is not None

    async def test_create_key_without_expiration(
        self, client: AsyncClient, user_headers
    ):
        """Test creating API key without expiration (if supported)."""
        key_data = {
            "name": "Never Expires Key",
            "scopes": ["dashboard:read"],
            # No expires_in_days specified
        }

        response = await client.post(
            "/api/v1/api-keys/", headers=user_headers, json=key_data
        )

        # Should either succeed with null expiration or use default
        assert response.status_code == 201


# ============================================================================
# KEY PREFIX TESTS
# ============================================================================


@pytest.mark.integration
class TestAPIKeyPrefix:
    """Test API key prefix functionality."""

    async def test_api_key_has_valid_prefix(
        self, client: AsyncClient, user_headers
    ):
        """Test that created API keys have valid prefix format."""
        key_data = {
            "name": "Prefix Test Key",
            "scopes": ["inventory:read"],
        }

        response = await client.post(
            "/api/v1/api-keys/", headers=user_headers, json=key_data
        )

        assert response.status_code == 201
        data = response.json()

        # Full key should start with farm_
        assert data["api_key"].startswith("farm_")

        # Key prefix should match beginning of full key
        assert data["api_key"].startswith(data["key_prefix"])

    async def test_key_prefix_shown_in_list(
        self, client: AsyncClient, user_headers
    ):
        """Test that key prefix is shown when listing keys."""
        # Create a key
        key_data = {
            "name": "List Prefix Test",
            "scopes": ["tickets:read"],
        }
        await client.post("/api/v1/api-keys/", headers=user_headers, json=key_data)

        # List keys
        response = await client.get("/api/v1/api-keys/", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        for key in data:
            assert "key_prefix" in key
            assert len(key["key_prefix"]) > 0
