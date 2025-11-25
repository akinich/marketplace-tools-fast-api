"""
================================================================================
Webhook Tests - Phase 3
================================================================================
Test coverage for webhook management, delivery, and event handling.

Test Classes:
- TestWebhookCRUD: Basic CRUD operations (8 tests)
- TestWebhookPermissions: Admin-only access control (3 tests)
- TestWebhookDeliveries: Delivery logs and filtering (4 tests)
- TestWebhookTesting: Test webhook endpoint (3 tests)
- TestWebhookEvents: Available events endpoint (2 tests)
- TestWebhookValidation: Input validation (5 tests)

Total: 25 tests
================================================================================
"""

import pytest
from httpx import AsyncClient
import json


# ============================================================================
# WEBHOOK CRUD OPERATIONS
# ============================================================================


@pytest.mark.integration
class TestWebhookCRUD:
    """Test webhook CRUD operations."""

    async def test_list_webhooks(self, client: AsyncClient, admin_headers):
        """Test listing all webhooks."""
        response = await client.get(
            "/api/v1/webhooks/",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_create_webhook(self, client: AsyncClient, admin_headers):
        """Test creating a webhook."""
        webhook_data = {
            "name": "Test Webhook",
            "url": "https://example.com/webhook",
            "events": ["ticket.created", "ticket.updated"],
            "custom_headers": {"X-Custom": "header"},
            "description": "Test webhook for ticket events",
            "is_active": True,
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "retry_delay_seconds": 60
        }

        response = await client.post(
            "/api/v1/webhooks/",
            headers=admin_headers,
            json=webhook_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == webhook_data["name"]
        assert data["url"] == webhook_data["url"]
        assert data["events"] == webhook_data["events"]
        assert data["custom_headers"] == webhook_data["custom_headers"]
        assert data["description"] == webhook_data["description"]
        assert data["is_active"] is True
        assert data["timeout_seconds"] == 30
        assert data["retry_attempts"] == 3
        assert "secret" in data
        assert "id" in data
        assert "created_at" in data

    async def test_get_webhook_by_id(self, client: AsyncClient, admin_headers):
        """Test getting a webhook by ID."""
        # Create a webhook first
        webhook_data = {
            "name": "Get Test Webhook",
            "url": "https://example.com/webhook2",
            "events": ["user.created"],
            "custom_headers": {},
            "is_active": True,
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "retry_delay_seconds": 60
        }

        create_response = await client.post(
            "/api/v1/webhooks/",
            headers=admin_headers,
            json=webhook_data
        )
        webhook_id = create_response.json()["id"]

        # Get the webhook
        response = await client.get(
            f"/api/v1/webhooks/{webhook_id}",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == webhook_id
        assert data["name"] == webhook_data["name"]
        assert data["url"] == webhook_data["url"]

    async def test_get_nonexistent_webhook(self, client: AsyncClient, admin_headers):
        """Test getting a webhook that doesn't exist."""
        response = await client.get(
            "/api/v1/webhooks/99999",
            headers=admin_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_update_webhook(self, client: AsyncClient, admin_headers):
        """Test updating a webhook."""
        # Create a webhook first
        webhook_data = {
            "name": "Original Name",
            "url": "https://example.com/webhook3",
            "events": ["ticket.created"],
            "custom_headers": {},
            "is_active": True,
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "retry_delay_seconds": 60
        }

        create_response = await client.post(
            "/api/v1/webhooks/",
            headers=admin_headers,
            json=webhook_data
        )
        webhook_id = create_response.json()["id"]

        # Update the webhook
        update_data = {
            "name": "Updated Name",
            "url": "https://example.com/webhook3-updated",
            "events": ["ticket.created", "ticket.closed"],
            "custom_headers": {"X-Updated": "true"},
            "description": "Updated description",
            "is_active": False,
            "timeout_seconds": 45,
            "retry_attempts": 5,
            "retry_delay_seconds": 120
        }

        response = await client.put(
            f"/api/v1/webhooks/{webhook_id}",
            headers=admin_headers,
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == webhook_id
        assert data["name"] == "Updated Name"
        assert data["url"] == "https://example.com/webhook3-updated"
        assert set(data["events"]) == set(update_data["events"])
        assert data["custom_headers"] == {"X-Updated": "true"}
        assert data["is_active"] is False
        assert data["timeout_seconds"] == 45
        assert data["retry_attempts"] == 5

    async def test_update_nonexistent_webhook(self, client: AsyncClient, admin_headers):
        """Test updating a webhook that doesn't exist."""
        update_data = {
            "name": "Nonexistent",
            "url": "https://example.com/webhook",
            "events": [],
            "custom_headers": {},
            "is_active": True,
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "retry_delay_seconds": 60
        }

        response = await client.put(
            "/api/v1/webhooks/99999",
            headers=admin_headers,
            json=update_data
        )

        assert response.status_code == 404

    async def test_delete_webhook(self, client: AsyncClient, admin_headers):
        """Test deleting a webhook."""
        # Create a webhook first
        webhook_data = {
            "name": "To Be Deleted",
            "url": "https://example.com/webhook4",
            "events": ["user.created"],
            "custom_headers": {},
            "is_active": True,
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "retry_delay_seconds": 60
        }

        create_response = await client.post(
            "/api/v1/webhooks/",
            headers=admin_headers,
            json=webhook_data
        )
        webhook_id = create_response.json()["id"]

        # Delete the webhook
        response = await client.delete(
            f"/api/v1/webhooks/{webhook_id}",
            headers=admin_headers
        )

        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Verify it's gone
        get_response = await client.get(
            f"/api/v1/webhooks/{webhook_id}",
            headers=admin_headers
        )
        assert get_response.status_code == 404


# ============================================================================
# WEBHOOK PERMISSIONS
# ============================================================================


@pytest.mark.integration
class TestWebhookPermissions:
    """Test webhook permission requirements."""

    async def test_list_webhooks_requires_admin(self, client: AsyncClient, user_headers):
        """Test that listing webhooks requires admin privileges."""
        response = await client.get(
            "/api/v1/webhooks/",
            headers=user_headers
        )

        assert response.status_code == 403

    async def test_create_webhook_requires_admin(self, client: AsyncClient, user_headers):
        """Test that creating webhooks requires admin privileges."""
        webhook_data = {
            "name": "Unauthorized Webhook",
            "url": "https://example.com/webhook",
            "events": ["ticket.created"],
            "custom_headers": {},
            "is_active": True,
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "retry_delay_seconds": 60
        }

        response = await client.post(
            "/api/v1/webhooks/",
            headers=user_headers,
            json=webhook_data
        )

        assert response.status_code == 403

    async def test_webhooks_require_authentication(self, client: AsyncClient):
        """Test that webhook endpoints require authentication."""
        response = await client.get("/api/v1/webhooks/")

        assert response.status_code == 403


# ============================================================================
# WEBHOOK DELIVERIES
# ============================================================================


@pytest.mark.integration
class TestWebhookDeliveries:
    """Test webhook delivery logs."""

    async def test_get_webhook_deliveries(self, client: AsyncClient, admin_headers):
        """Test getting delivery logs for a webhook."""
        # Create a webhook first
        webhook_data = {
            "name": "Delivery Test Webhook",
            "url": "https://example.com/webhook5",
            "events": ["ticket.created"],
            "custom_headers": {},
            "is_active": True,
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "retry_delay_seconds": 60
        }

        create_response = await client.post(
            "/api/v1/webhooks/",
            headers=admin_headers,
            json=webhook_data
        )
        webhook_id = create_response.json()["id"]

        # Get deliveries (should be empty initially)
        response = await client.get(
            f"/api/v1/webhooks/{webhook_id}/deliveries",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_webhook_deliveries_with_limit(self, client: AsyncClient, admin_headers):
        """Test getting delivery logs with limit parameter."""
        # Create a webhook first
        webhook_data = {
            "name": "Limit Test Webhook",
            "url": "https://example.com/webhook6",
            "events": ["user.created"],
            "custom_headers": {},
            "is_active": True,
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "retry_delay_seconds": 60
        }

        create_response = await client.post(
            "/api/v1/webhooks/",
            headers=admin_headers,
            json=webhook_data
        )
        webhook_id = create_response.json()["id"]

        # Get deliveries with limit
        response = await client.get(
            f"/api/v1/webhooks/{webhook_id}/deliveries?limit=10",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10

    async def test_get_webhook_deliveries_with_status_filter(
        self, client: AsyncClient, admin_headers
    ):
        """Test getting delivery logs filtered by status."""
        # Create a webhook first
        webhook_data = {
            "name": "Status Filter Webhook",
            "url": "https://example.com/webhook7",
            "events": ["ticket.updated"],
            "custom_headers": {},
            "is_active": True,
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "retry_delay_seconds": 60
        }

        create_response = await client.post(
            "/api/v1/webhooks/",
            headers=admin_headers,
            json=webhook_data
        )
        webhook_id = create_response.json()["id"]

        # Get deliveries filtered by status
        response = await client.get(
            f"/api/v1/webhooks/{webhook_id}/deliveries?status=pending",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_deliveries_requires_admin(self, client: AsyncClient, user_headers):
        """Test that getting delivery logs requires admin privileges."""
        response = await client.get(
            "/api/v1/webhooks/1/deliveries",
            headers=user_headers
        )

        assert response.status_code == 403


# ============================================================================
# WEBHOOK TESTING
# ============================================================================


@pytest.mark.integration
class TestWebhookTesting:
    """Test webhook testing endpoint."""

    async def test_get_available_events(self, client: AsyncClient, admin_headers):
        """Test getting list of available webhook events."""
        response = await client.get(
            "/api/v1/webhooks/events/available",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert isinstance(data["events"], list)
        assert len(data["events"]) > 0
        # Check for known events
        assert "ticket.created" in data["events"]
        assert "user.created" in data["events"]

    async def test_test_webhook_endpoint(self, client: AsyncClient, admin_headers):
        """Test the webhook testing endpoint."""
        # Create a webhook first
        webhook_data = {
            "name": "Test Endpoint Webhook",
            "url": "https://httpbin.org/post",  # Real endpoint that accepts POST
            "events": ["ticket.created"],
            "custom_headers": {},
            "is_active": True,
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "retry_delay_seconds": 60
        }

        create_response = await client.post(
            "/api/v1/webhooks/",
            headers=admin_headers,
            json=webhook_data
        )
        webhook_id = create_response.json()["id"]

        # Test the webhook
        test_data = {
            "webhook_id": webhook_id,
            "test_payload": {
                "test": "data",
                "message": "This is a test"
            }
        }

        response = await client.post(
            "/api/v1/webhooks/test",
            headers=admin_headers,
            json=test_data
        )

        assert response.status_code == 200
        data = response.json()
        # Test endpoint should return a response structure
        # Success may be False if httpbin.org is unreachable in CI/CD
        assert 'success' in data
        # Either success is True or we got a response with status_code/response_body
        assert data.get('success') is True or 'status_code' in data or 'response_body' in data

    async def test_test_nonexistent_webhook(self, client: AsyncClient, admin_headers):
        """Test testing a webhook that doesn't exist."""
        test_data = {
            "webhook_id": 99999,
            "test_payload": {"test": "data"}
        }

        response = await client.post(
            "/api/v1/webhooks/test",
            headers=admin_headers,
            json=test_data
        )

        assert response.status_code == 404


# ============================================================================
# WEBHOOK EVENTS
# ============================================================================


@pytest.mark.integration
class TestWebhookEvents:
    """Test webhook event filtering."""

    async def test_create_webhook_with_specific_events(
        self, client: AsyncClient, admin_headers
    ):
        """Test creating a webhook subscribed to specific events."""
        webhook_data = {
            "name": "Ticket Events Only",
            "url": "https://example.com/webhook8",
            "events": ["ticket.created", "ticket.updated", "ticket.closed"],
            "custom_headers": {},
            "is_active": True,
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "retry_delay_seconds": 60
        }

        response = await client.post(
            "/api/v1/webhooks/",
            headers=admin_headers,
            json=webhook_data
        )

        assert response.status_code == 200
        data = response.json()
        assert set(data["events"]) == set(webhook_data["events"])

    async def test_create_webhook_with_empty_events(
        self, client: AsyncClient, admin_headers
    ):
        """Test creating a webhook with no events subscribed."""
        webhook_data = {
            "name": "No Events Webhook",
            "url": "https://example.com/webhook9",
            "events": [],
            "custom_headers": {},
            "is_active": True,
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "retry_delay_seconds": 60
        }

        response = await client.post(
            "/api/v1/webhooks/",
            headers=admin_headers,
            json=webhook_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["events"] == []


# ============================================================================
# WEBHOOK VALIDATION
# ============================================================================


@pytest.mark.integration
class TestWebhookValidation:
    """Test webhook input validation."""

    async def test_create_webhook_with_invalid_url(
        self, client: AsyncClient, admin_headers
    ):
        """Test creating a webhook with an invalid URL."""
        webhook_data = {
            "name": "Invalid URL Webhook",
            "url": "not-a-valid-url",
            "events": ["ticket.created"],
            "custom_headers": {},
            "is_active": True,
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "retry_delay_seconds": 60
        }

        response = await client.post(
            "/api/v1/webhooks/",
            headers=admin_headers,
            json=webhook_data
        )

        assert response.status_code == 422  # Validation error

    async def test_create_webhook_with_invalid_timeout(
        self, client: AsyncClient, admin_headers
    ):
        """Test creating a webhook with timeout out of range."""
        webhook_data = {
            "name": "Invalid Timeout Webhook",
            "url": "https://example.com/webhook",
            "events": ["ticket.created"],
            "custom_headers": {},
            "is_active": True,
            "timeout_seconds": 200,  # Max is 120
            "retry_attempts": 3,
            "retry_delay_seconds": 60
        }

        response = await client.post(
            "/api/v1/webhooks/",
            headers=admin_headers,
            json=webhook_data
        )

        assert response.status_code == 422

    async def test_create_webhook_with_invalid_retry_attempts(
        self, client: AsyncClient, admin_headers
    ):
        """Test creating a webhook with retry_attempts out of range."""
        webhook_data = {
            "name": "Invalid Retry Webhook",
            "url": "https://example.com/webhook",
            "events": ["ticket.created"],
            "custom_headers": {},
            "is_active": True,
            "timeout_seconds": 30,
            "retry_attempts": 15,  # Max is 10
            "retry_delay_seconds": 60
        }

        response = await client.post(
            "/api/v1/webhooks/",
            headers=admin_headers,
            json=webhook_data
        )

        assert response.status_code == 422

    async def test_create_webhook_without_required_fields(
        self, client: AsyncClient, admin_headers
    ):
        """Test creating a webhook without required fields."""
        webhook_data = {
            "events": ["ticket.created"]
            # Missing name and url
        }

        response = await client.post(
            "/api/v1/webhooks/",
            headers=admin_headers,
            json=webhook_data
        )

        assert response.status_code == 422

    async def test_create_webhook_with_custom_headers(
        self, client: AsyncClient, admin_headers
    ):
        """Test creating a webhook with custom headers."""
        webhook_data = {
            "name": "Custom Headers Webhook",
            "url": "https://example.com/webhook10",
            "events": ["user.created"],
            "custom_headers": {
                "X-API-Key": "secret-key",
                "X-Environment": "production"
            },
            "is_active": True,
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "retry_delay_seconds": 60
        }

        response = await client.post(
            "/api/v1/webhooks/",
            headers=admin_headers,
            json=webhook_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["custom_headers"]["X-API-Key"] == "secret-key"
        assert data["custom_headers"]["X-Environment"] == "production"
