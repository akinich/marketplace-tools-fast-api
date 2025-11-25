"""
================================================================================
Farm Management System - WebSocket Tests
================================================================================
Version: 1.0.0
Last Updated: 2025-11-25

Test Coverage:
- WebSocket status endpoint (get connection info)
- WebSocket test endpoint (send test notification)
- Admin-only access control
- Connection manager state

Note: Full WebSocket connection testing (WS protocol) requires special
test client setup and is not included in this test suite.

Total Tests: 6

================================================================================
"""

import pytest
from httpx import AsyncClient
from typing import Dict


# ============================================================================
# WEBSOCKET STATUS TESTS
# ============================================================================


class TestWebSocketStatus:
    """Test WebSocket status endpoint"""

    async def test_get_websocket_status(self, client: AsyncClient, admin_headers):
        """Test getting WebSocket connection status."""
        response = await client.get(
            "/api/v1/websocket/status",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "total_connections" in data
        assert "online_users_count" in data
        assert "online_users" in data
        assert "rooms" in data
        assert "timestamp" in data

        # Initially no connections (REST tests don't establish WS connections)
        assert isinstance(data["total_connections"], int)
        assert isinstance(data["online_users_count"], int)
        assert isinstance(data["online_users"], list)
        assert isinstance(data["rooms"], dict)

    async def test_websocket_status_returns_correct_types(self, client: AsyncClient, admin_headers):
        """Test WebSocket status returns correct data types."""
        response = await client.get(
            "/api/v1/websocket/status",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify types
        assert isinstance(data["total_connections"], int)
        assert isinstance(data["online_users_count"], int)
        assert isinstance(data["online_users"], list)
        assert isinstance(data["rooms"], dict)
        assert isinstance(data["timestamp"], str)

        # Counts should be non-negative
        assert data["total_connections"] >= 0
        assert data["online_users_count"] >= 0


# ============================================================================
# WEBSOCKET TEST ENDPOINT TESTS
# ============================================================================


class TestWebSocketTest:
    """Test WebSocket test notification endpoint"""

    async def test_send_test_notification_not_connected(self, client: AsyncClient, admin_headers):
        """Test sending test notification when user is not connected."""
        response = await client.post(
            "/api/v1/websocket/test",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # User is not connected via WebSocket in REST tests
        assert data["success"] is False
        assert data["connected"] is False
        assert "not connected" in data["message"].lower()

    async def test_test_endpoint_returns_correct_structure(self, client: AsyncClient, admin_headers):
        """Test that test endpoint returns expected structure."""
        response = await client.post(
            "/api/v1/websocket/test",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "success" in data
        assert "message" in data
        assert "connected" in data


# ============================================================================
# PERMISSIONS TESTS
# ============================================================================


class TestWebSocketPermissions:
    """Test WebSocket access control"""

    async def test_unauthenticated_cannot_access_status(self, client: AsyncClient):
        """Test unauthenticated users cannot access WebSocket status."""
        response = await client.get("/api/v1/websocket/status")

        assert response.status_code == 403

    async def test_unauthenticated_cannot_send_test(self, client: AsyncClient):
        """Test unauthenticated users cannot send test notification."""
        response = await client.post("/api/v1/websocket/test")

        assert response.status_code == 403

    async def test_admin_can_access_status(self, client: AsyncClient, admin_headers):
        """Test admin can access WebSocket status."""
        response = await client.get(
            "/api/v1/websocket/status",
            headers=admin_headers
        )

        assert response.status_code == 200
