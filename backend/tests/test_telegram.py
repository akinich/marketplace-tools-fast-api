"""
================================================================================
Farm Management System - Telegram Tests
================================================================================
Version: 1.0.0
Last Updated: 2025-11-25

Test Coverage:
- Telegram notification settings (get, update)
- Bot status and health checks
- Test notifications
- User account linking (create code, status, unlink)
- Admin-only and user access control

Total Tests: 12

================================================================================
"""

import pytest
from httpx import AsyncClient
from typing import Dict


# ============================================================================
# TELEGRAM SETTINGS TESTS
# ============================================================================


class TestTelegramSettings:
    """Test Telegram notification settings"""

    async def test_get_notification_settings(self, client: AsyncClient, admin_headers):
        """Test getting notification settings."""
        response = await client.get(
            "/api/v1/telegram/settings",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify expected settings exist
        assert "tickets_channel_id" in data
        assert "po_channel_id" in data
        assert "inventory_channel_id" in data
        assert "enable_ticket_notifications" in data
        assert "enable_po_notifications" in data
        assert "enable_inventory_notifications" in data

    async def test_update_notification_settings(self, client: AsyncClient, admin_headers):
        """Test updating notification settings."""
        update_data = {
            "enable_ticket_notifications": False,
            "enable_po_notifications": True
        }

        response = await client.put(
            "/api/v1/telegram/settings",
            headers=admin_headers,
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["enable_ticket_notifications"] is False
        assert data["enable_po_notifications"] is True

    async def test_update_settings_with_no_data(self, client: AsyncClient, admin_headers):
        """Test updating settings with no data fails."""
        response = await client.put(
            "/api/v1/telegram/settings",
            headers=admin_headers,
            json={}
        )

        assert response.status_code == 400
        assert "no settings" in response.json()["detail"].lower()


# ============================================================================
# TELEGRAM BOT STATUS TESTS
# ============================================================================


class TestTelegramBotStatus:
    """Test Telegram bot status and health"""

    async def test_get_bot_status(self, client: AsyncClient, admin_headers):
        """Test getting bot status."""
        response = await client.get(
            "/api/v1/telegram/status",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "status" in data
        assert data["status"] in ["active", "inactive", "error"]

    async def test_send_test_notification(self, client: AsyncClient, admin_headers):
        """Test sending test notification."""
        test_data = {
            "channel_type": "tickets"
        }

        response = await client.post(
            "/api/v1/telegram/test",
            headers=admin_headers,
            json=test_data
        )

        # May return 500 if bot is not configured (expected in test environment)
        # Or 200 with success/error in response if bot is configured
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            # Response should indicate success or failure with reason
            assert "success" in data or "error" in data or "message" in data


# ============================================================================
# TELEGRAM USER LINKING TESTS
# ============================================================================


class TestTelegramLinking:
    """Test Telegram user account linking"""

    async def test_create_link_code(self, client: AsyncClient, user_headers):
        """Test creating a link code for user."""
        response = await client.post(
            "/api/v1/telegram/link/create",
            headers=user_headers
        )

        assert response.status_code == 201  # Created status
        data = response.json()

        # Verify link code structure
        assert "link_code" in data
        assert "expires_at" in data
        assert len(data["link_code"]) > 0

    async def test_get_link_status_not_linked(self, client: AsyncClient, user_headers):
        """Test getting link status when not linked."""
        response = await client.get(
            "/api/v1/telegram/link/status",
            headers=user_headers
        )

        assert response.status_code == 200
        data = response.json()

        # User should not be linked initially
        assert "is_linked" in data
        assert data["is_linked"] is False

    async def test_unlink_when_not_linked(self, client: AsyncClient, user_headers):
        """Test unlinking when user is not linked."""
        response = await client.post(
            "/api/v1/telegram/link/unlink",
            headers=user_headers
        )

        # Should succeed (no-op) or return appropriate message
        assert response.status_code in [200, 400]


# ============================================================================
# PERMISSIONS TESTS
# ============================================================================


class TestTelegramPermissions:
    """Test Telegram access control"""

    async def test_admin_can_access_settings(self, client: AsyncClient, admin_headers):
        """Test admin can access settings."""
        response = await client.get(
            "/api/v1/telegram/settings",
            headers=admin_headers
        )

        assert response.status_code == 200

    async def test_regular_user_cannot_access_settings(self, client: AsyncClient, user_headers):
        """Test regular user cannot access settings."""
        response = await client.get(
            "/api/v1/telegram/settings",
            headers=user_headers
        )

        assert response.status_code == 403

    async def test_unauthenticated_cannot_access_settings(self, client: AsyncClient):
        """Test unauthenticated users cannot access settings."""
        response = await client.get("/api/v1/telegram/settings")

        assert response.status_code == 403

    async def test_user_can_create_link_code(self, client: AsyncClient, user_headers):
        """Test regular user can create link code."""
        response = await client.post(
            "/api/v1/telegram/link/create",
            headers=user_headers
        )

        assert response.status_code == 201  # Created status
