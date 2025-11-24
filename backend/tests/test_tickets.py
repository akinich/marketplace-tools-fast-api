"""
================================================================================
Farm Management System - Tickets Module Tests
================================================================================
Version: 1.0.0
Last Updated: 2025-11-25

Description:
    Tests for ticket system - issue tracking, feature requests, and comments.
    Tests CRUD operations, permissions, filtering, and admin functionality.

Test Coverage:
    - Ticket CRUD operations (list, get, create, update, delete)
    - Comment system (add, update, delete)
    - Admin operations (set priority, change status, close tickets)
    - Permission checks (user vs admin)
    - Filtering and pagination
    - Statistics endpoints

================================================================================
"""

import pytest
from httpx import AsyncClient
from typing import Dict
from app.database import fetch_one, fetch_all, execute_query


# ============================================================================
# TICKET LIST TESTS
# ============================================================================


@pytest.mark.integration
class TestTicketList:
    """Test ticket listing endpoints."""

    async def test_list_all_tickets(
        self, client: AsyncClient, test_admin_user, admin_headers
    ):
        """Test listing all tickets."""
        response = await client.get("/api/v1/tickets", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "tickets" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data

    async def test_list_tickets_without_auth(self, client: AsyncClient):
        """Test listing tickets without authentication."""
        response = await client.get("/api/v1/tickets")

        assert response.status_code == 403

    async def test_list_tickets_with_pagination(
        self, client: AsyncClient, admin_headers
    ):
        """Test ticket listing with pagination."""
        response = await client.get(
            "/api/v1/tickets?page=1&limit=10", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["limit"] == 10

    async def test_filter_tickets_by_type(self, client: AsyncClient, admin_headers):
        """Test filtering tickets by type."""
        response = await client.get(
            "/api/v1/tickets?ticket_type=issue", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        # All returned tickets should be of type 'issue'
        for ticket in data["tickets"]:
            assert ticket["ticket_type"] == "issue"

    async def test_filter_tickets_by_status(self, client: AsyncClient, admin_headers):
        """Test filtering tickets by status."""
        response = await client.get(
            "/api/v1/tickets?status=open", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        # All returned tickets should have status 'open'
        for ticket in data["tickets"]:
            assert ticket["status"] == "open"

    async def test_filter_tickets_by_priority(
        self, client: AsyncClient, admin_headers
    ):
        """Test filtering tickets by priority."""
        response = await client.get(
            "/api/v1/tickets?priority=high", headers=admin_headers
        )

        assert response.status_code == 200

    async def test_list_my_tickets(
        self, client: AsyncClient, test_regular_user, user_headers
    ):
        """Test listing current user's tickets."""
        response = await client.get("/api/v1/tickets/my", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        # All tickets should belong to the current user
        for ticket in data["tickets"]:
            assert ticket["created_by"]["id"] == test_regular_user["id"]


# ============================================================================
# TICKET CRUD TESTS
# ============================================================================


@pytest.mark.integration
class TestTicketCRUD:
    """Test ticket CRUD operations."""

    async def test_create_ticket(
        self, client: AsyncClient, test_regular_user, user_headers
    ):
        """Test creating a new ticket."""
        ticket_data = {
            "title": "Test Issue",
            "description": "This is a test issue",
            "ticket_type": "issue",
        }

        response = await client.post(
            "/api/v1/tickets", headers=user_headers, json=ticket_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Issue"
        assert data["ticket_type"] == "issue"
        assert data["status"] == "open"
        assert data["created_by"]["id"] == test_regular_user["id"]

    async def test_create_ticket_without_auth(self, client: AsyncClient):
        """Test creating ticket without authentication."""
        ticket_data = {
            "title": "Test Issue",
            "description": "This is a test issue",
            "ticket_type": "issue",
        }

        response = await client.post("/api/v1/tickets", json=ticket_data)

        assert response.status_code == 403

    async def test_create_feature_request(
        self, client: AsyncClient, user_headers
    ):
        """Test creating a feature request ticket."""
        ticket_data = {
            "title": "New Feature Request",
            "description": "Please add this feature",
            "ticket_type": "feature_request",
        }

        response = await client.post(
            "/api/v1/tickets", headers=user_headers, json=ticket_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["ticket_type"] == "feature_request"

    async def test_get_ticket_by_id(
        self, client: AsyncClient, user_headers
    ):
        """Test getting a specific ticket by ID."""
        # First create a ticket
        ticket_data = {
            "title": "Get Test Ticket",
            "description": "Testing GET endpoint",
            "ticket_type": "issue",
        }
        create_response = await client.post(
            "/api/v1/tickets", headers=user_headers, json=ticket_data
        )
        ticket_id = create_response.json()["id"]

        # Now get it
        response = await client.get(f"/api/v1/tickets/{ticket_id}", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ticket_id
        assert data["title"] == "Get Test Ticket"
        assert "comments" in data

    async def test_get_nonexistent_ticket(self, client: AsyncClient, user_headers):
        """Test getting a ticket that doesn't exist."""
        response = await client.get("/api/v1/tickets/99999", headers=user_headers)

        assert response.status_code == 404

    async def test_update_own_ticket(
        self, client: AsyncClient, test_regular_user, user_headers
    ):
        """Test updating own ticket."""
        # Create ticket
        ticket_data = {
            "title": "Original Title",
            "description": "Original description",
            "ticket_type": "issue",
        }
        create_response = await client.post(
            "/api/v1/tickets", headers=user_headers, json=ticket_data
        )
        ticket_id = create_response.json()["id"]

        # Update it
        update_data = {
            "title": "Updated Title",
            "description": "Updated description",
        }
        response = await client.put(
            f"/api/v1/tickets/{ticket_id}", headers=user_headers, json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated description"

    async def test_update_other_users_ticket(
        self, client: AsyncClient, test_regular_user, test_admin_user, user_headers, admin_headers
    ):
        """Test that users cannot update other users' tickets."""
        # Admin creates a ticket
        ticket_data = {
            "title": "Admin's Ticket",
            "description": "Admin created this",
            "ticket_type": "issue",
        }
        create_response = await client.post(
            "/api/v1/tickets", headers=admin_headers, json=ticket_data
        )
        ticket_id = create_response.json()["id"]

        # Regular user tries to update it (should fail)
        update_data = {"title": "Hacked!"}
        response = await client.put(
            f"/api/v1/tickets/{ticket_id}", headers=user_headers, json=update_data
        )

        assert response.status_code == 403

    async def test_delete_own_ticket(self, client: AsyncClient, user_headers):
        """Test deleting own ticket."""
        # Create ticket
        ticket_data = {
            "title": "To Be Deleted",
            "description": "This ticket will be deleted",
            "ticket_type": "issue",
        }
        create_response = await client.post(
            "/api/v1/tickets", headers=user_headers, json=ticket_data
        )
        ticket_id = create_response.json()["id"]

        # Delete it
        response = await client.delete(
            f"/api/v1/tickets/{ticket_id}", headers=user_headers
        )

        assert response.status_code == 200

        # Verify it's gone
        get_response = await client.get(
            f"/api/v1/tickets/{ticket_id}", headers=user_headers
        )
        assert get_response.status_code == 404

    async def test_delete_other_users_ticket_fails(
        self, client: AsyncClient, admin_headers, user_headers
    ):
        """Test that users cannot delete other users' tickets."""
        # Admin creates ticket
        ticket_data = {
            "title": "Protected Ticket",
            "description": "Regular user shouldn't delete this",
            "ticket_type": "issue",
        }
        create_response = await client.post(
            "/api/v1/tickets", headers=admin_headers, json=ticket_data
        )
        ticket_id = create_response.json()["id"]

        # Regular user tries to delete (should fail)
        response = await client.delete(
            f"/api/v1/tickets/{ticket_id}", headers=user_headers
        )

        assert response.status_code == 403


# ============================================================================
# ADMIN OPERATIONS TESTS
# ============================================================================


@pytest.mark.integration
class TestAdminTicketOperations:
    """Test admin-only ticket operations."""

    async def test_admin_set_priority(
        self, client: AsyncClient, admin_headers, user_headers
    ):
        """Test admin setting ticket priority."""
        # User creates ticket (no priority)
        ticket_data = {
            "title": "Needs Priority",
            "description": "Admin should set priority",
            "ticket_type": "issue",
        }
        create_response = await client.post(
            "/api/v1/tickets", headers=user_headers, json=ticket_data
        )
        ticket_id = create_response.json()["id"]

        # Admin sets priority
        admin_update = {"priority": "high"}
        response = await client.put(
            f"/api/v1/tickets/{ticket_id}/admin",
            headers=admin_headers,
            json=admin_update,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == "high"

    async def test_regular_user_cannot_set_priority(
        self, client: AsyncClient, user_headers
    ):
        """Test that regular users cannot use admin update endpoint."""
        # Create ticket
        ticket_data = {
            "title": "Test Ticket",
            "description": "Testing permissions",
            "ticket_type": "issue",
        }
        create_response = await client.post(
            "/api/v1/tickets", headers=user_headers, json=ticket_data
        )
        ticket_id = create_response.json()["id"]

        # Try admin update (should fail)
        admin_update = {"priority": "critical"}
        response = await client.put(
            f"/api/v1/tickets/{ticket_id}/admin",
            headers=user_headers,
            json=admin_update,
        )

        assert response.status_code == 403

    async def test_admin_change_status(
        self, client: AsyncClient, admin_headers, user_headers
    ):
        """Test admin changing ticket status."""
        # Create ticket
        ticket_data = {
            "title": "Status Change Test",
            "description": "Admin will change status",
            "ticket_type": "issue",
        }
        create_response = await client.post(
            "/api/v1/tickets", headers=user_headers, json=ticket_data
        )
        ticket_id = create_response.json()["id"]

        # Admin changes status
        admin_update = {"status": "in_progress"}
        response = await client.put(
            f"/api/v1/tickets/{ticket_id}/admin",
            headers=admin_headers,
            json=admin_update,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"

    async def test_admin_close_ticket(
        self, client: AsyncClient, admin_headers, user_headers
    ):
        """Test admin closing a ticket."""
        # Create ticket
        ticket_data = {
            "title": "To Be Closed",
            "description": "Admin will close this",
            "ticket_type": "issue",
        }
        create_response = await client.post(
            "/api/v1/tickets", headers=user_headers, json=ticket_data
        )
        ticket_id = create_response.json()["id"]

        # Admin closes it
        close_data = {"closing_comment": "Issue resolved"}
        response = await client.post(
            f"/api/v1/tickets/{ticket_id}/close",
            headers=admin_headers,
            json=close_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "closed"
        assert data["closed_by"] is not None

    async def test_regular_user_cannot_close_ticket(
        self, client: AsyncClient, user_headers
    ):
        """Test that regular users cannot close tickets."""
        # Create ticket
        ticket_data = {
            "title": "Can't Close",
            "description": "User shouldn't close this",
            "ticket_type": "issue",
        }
        create_response = await client.post(
            "/api/v1/tickets", headers=user_headers, json=ticket_data
        )
        ticket_id = create_response.json()["id"]

        # Try to close (should fail)
        close_data = {"closing_comment": "Trying to close"}
        response = await client.post(
            f"/api/v1/tickets/{ticket_id}/close",
            headers=user_headers,
            json=close_data,
        )

        assert response.status_code == 403

    async def test_admin_delete_any_ticket(
        self, client: AsyncClient, user_headers, admin_headers
    ):
        """Test that admin can delete any user's ticket."""
        # User creates ticket
        ticket_data = {
            "title": "User's Ticket",
            "description": "Admin can delete this",
            "ticket_type": "issue",
        }
        create_response = await client.post(
            "/api/v1/tickets", headers=user_headers, json=ticket_data
        )
        ticket_id = create_response.json()["id"]

        # Admin deletes it
        response = await client.delete(
            f"/api/v1/tickets/{ticket_id}", headers=admin_headers
        )

        assert response.status_code == 200


# ============================================================================
# COMMENT TESTS
# ============================================================================


@pytest.mark.integration
class TestTicketComments:
    """Test ticket comment functionality."""

    async def test_add_comment(
        self, client: AsyncClient, user_headers
    ):
        """Test adding a comment to a ticket."""
        # Create ticket
        ticket_data = {
            "title": "Test Ticket",
            "description": "For comment testing",
            "ticket_type": "issue",
        }
        create_response = await client.post(
            "/api/v1/tickets", headers=user_headers, json=ticket_data
        )
        ticket_id = create_response.json()["id"]

        # Add comment
        comment_data = {"comment": "This is a test comment"}
        response = await client.post(
            f"/api/v1/tickets/{ticket_id}/comments",
            headers=user_headers,
            json=comment_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["comment"] == "This is a test comment"

    async def test_get_ticket_with_comments(
        self, client: AsyncClient, user_headers
    ):
        """Test that ticket details include comments."""
        # Create ticket
        ticket_data = {
            "title": "Ticket With Comments",
            "description": "Will have comments",
            "ticket_type": "issue",
        }
        create_response = await client.post(
            "/api/v1/tickets", headers=user_headers, json=ticket_data
        )
        ticket_id = create_response.json()["id"]

        # Add comment
        comment_data = {"comment": "First comment"}
        await client.post(
            f"/api/v1/tickets/{ticket_id}/comments",
            headers=user_headers,
            json=comment_data,
        )

        # Get ticket
        response = await client.get(f"/api/v1/tickets/{ticket_id}", headers=user_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["comments"]) >= 1
        assert any(c["comment"] == "First comment" for c in data["comments"])

    async def test_update_own_comment(
        self, client: AsyncClient, user_headers
    ):
        """Test updating own comment."""
        # Create ticket and comment
        ticket_data = {
            "title": "Test Ticket",
            "description": "For comment update test",
            "ticket_type": "issue",
        }
        ticket_response = await client.post(
            "/api/v1/tickets", headers=user_headers, json=ticket_data
        )
        ticket_id = ticket_response.json()["id"]

        comment_data = {"comment": "Original comment"}
        comment_response = await client.post(
            f"/api/v1/tickets/{ticket_id}/comments",
            headers=user_headers,
            json=comment_data,
        )
        comment_id = comment_response.json()["id"]

        # Update comment
        update_data = {"comment": "Updated comment"}
        response = await client.put(
            f"/api/v1/tickets/comments/{comment_id}",
            headers=user_headers,
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["comment"] == "Updated comment"

    async def test_delete_own_comment(
        self, client: AsyncClient, user_headers
    ):
        """Test deleting own comment."""
        # Create ticket and comment
        ticket_data = {
            "title": "Test Ticket",
            "description": "For comment delete test",
            "ticket_type": "issue",
        }
        ticket_response = await client.post(
            "/api/v1/tickets", headers=user_headers, json=ticket_data
        )
        ticket_id = ticket_response.json()["id"]

        comment_data = {"comment": "Comment to delete"}
        comment_response = await client.post(
            f"/api/v1/tickets/{ticket_id}/comments",
            headers=user_headers,
            json=comment_data,
        )
        comment_id = comment_response.json()["id"]

        # Delete comment
        response = await client.delete(
            f"/api/v1/tickets/comments/{comment_id}", headers=user_headers
        )

        assert response.status_code == 200


# ============================================================================
# STATISTICS TESTS
# ============================================================================


@pytest.mark.integration
class TestTicketStatistics:
    """Test ticket statistics endpoint."""

    async def test_get_ticket_stats(self, client: AsyncClient, admin_headers):
        """Test getting ticket statistics."""
        response = await client.get("/api/v1/tickets/stats", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_status" in data
        assert "by_type" in data
        assert "by_priority" in data

    async def test_stats_require_auth(self, client: AsyncClient):
        """Test that stats endpoint requires authentication."""
        response = await client.get("/api/v1/tickets/stats")

        assert response.status_code == 403
