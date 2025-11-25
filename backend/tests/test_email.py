"""
================================================================================
Farm Management System - Email Tests
================================================================================
Version: 1.0.0
Last Updated: 2025-11-25

Test Coverage:
- Email templates (get all, get by key, default templates)
- Email queue (get all, filter by status, send email, send template email)
- Email recipients (get all, update, create new)
- Admin-only access control
- Input validation

Total Tests: 15

================================================================================
"""

import pytest
from httpx import AsyncClient
from typing import Dict


# ============================================================================
# EMAIL TEMPLATES TESTS
# ============================================================================


class TestEmailTemplates:
    """Test email template operations"""

    async def test_get_all_templates(self, client: AsyncClient, admin_headers):
        """Test getting all email templates."""
        response = await client.get(
            "/api/v1/email/templates",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Should have default templates from migration
        assert len(data) >= 3

        # Check expected default templates exist
        template_keys = [t['template_key'] for t in data]
        assert 'welcome' in template_keys
        assert 'ticket_created' in template_keys
        assert 'low_stock_alert' in template_keys

        # Verify structure
        first_template = data[0]
        assert 'id' in first_template
        assert 'template_key' in first_template
        assert 'name' in first_template
        assert 'subject' in first_template
        assert 'html_body' in first_template
        assert 'plain_body' in first_template
        assert 'variables' in first_template

    async def test_get_template_by_key(self, client: AsyncClient, admin_headers):
        """Test getting specific template by key."""
        response = await client.get(
            "/api/v1/email/templates/welcome",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['template_key'] == 'welcome'
        assert data['name'] == 'Welcome Email'
        assert '{{user_name}}' in data['html_body']
        assert isinstance(data['variables'], list)

    async def test_get_nonexistent_template(self, client: AsyncClient, admin_headers):
        """Test getting template that doesn't exist."""
        response = await client.get(
            "/api/v1/email/templates/nonexistent_template",
            headers=admin_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()['detail'].lower()


# ============================================================================
# EMAIL QUEUE TESTS
# ============================================================================


class TestEmailQueue:
    """Test email queue operations"""

    async def test_get_email_queue(self, client: AsyncClient, admin_headers):
        """Test getting email queue."""
        response = await client.get(
            "/api/v1/email/queue",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_email_queue_by_status(self, client: AsyncClient, admin_headers):
        """Test filtering email queue by status."""
        response = await client.get(
            "/api/v1/email/queue?status=pending",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_send_direct_email(self, client: AsyncClient, admin_headers):
        """Test sending a direct email."""
        email_data = {
            "to_email": "test@example.com",
            "subject": "Test Email",
            "body": "This is a test email body.",
            "html_body": "<p>This is a test email body.</p>"
        }

        response = await client.post(
            "/api/v1/email/send",
            headers=admin_headers,
            json=email_data
        )

        assert response.status_code == 200
        data = response.json()
        assert 'email_id' in data
        assert data['status'] == 'queued'

        # Verify email is in queue
        queue_response = await client.get(
            "/api/v1/email/queue?status=pending",
            headers=admin_headers
        )
        queue_data = queue_response.json()
        email_found = any(e['to_email'] == 'test@example.com' for e in queue_data)
        assert email_found

    async def test_send_template_email(self, client: AsyncClient, admin_headers):
        """Test sending email using template."""
        email_data = {
            "to_email": "user@example.com",
            "template_key": "welcome",
            "variables": {
                "app_name": "Farm Management System",
                "user_name": "Test User",
                "user_email": "user@example.com",
                "temp_password": "TempPass123!",
                "login_url": "http://localhost:3000/login",
                "support_email": "support@example.com"
            }
        }

        response = await client.post(
            "/api/v1/email/send-template",
            headers=admin_headers,
            json=email_data
        )

        assert response.status_code == 200
        data = response.json()
        assert 'email_id' in data
        assert data['status'] == 'queued'

    async def test_send_template_email_invalid_key(self, client: AsyncClient, admin_headers):
        """Test sending email with invalid template key."""
        email_data = {
            "to_email": "user@example.com",
            "template_key": "nonexistent_template",
            "variables": {}
        }

        response = await client.post(
            "/api/v1/email/send-template",
            headers=admin_headers,
            json=email_data
        )

        assert response.status_code == 400


# ============================================================================
# EMAIL RECIPIENTS TESTS
# ============================================================================


class TestEmailRecipients:
    """Test email recipient management"""

    async def test_get_all_recipients(self, client: AsyncClient, admin_headers):
        """Test getting all email recipients."""
        response = await client.get(
            "/api/v1/email/recipients",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Should have default recipients from migration
        assert len(data) >= 4

        # Check expected default recipient types
        notification_types = [r['notification_type'] for r in data]
        assert 'tickets_critical' in notification_types
        assert 'tickets_all' in notification_types
        assert 'low_stock' in notification_types
        assert 'user_created' in notification_types

    async def test_update_recipients(self, client: AsyncClient, admin_headers):
        """Test updating email recipients."""
        recipient_data = {
            "recipient_emails": ["admin@example.com", "manager@example.com"],
            "description": "Recipients for critical ticket notifications",
            "is_active": True
        }

        response = await client.put(
            "/api/v1/email/recipients/tickets_critical",
            headers=admin_headers,
            json=recipient_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data['notification_type'] == 'tickets_critical'
        assert len(data['recipient_emails']) == 2
        assert 'admin@example.com' in data['recipient_emails']
        assert data['is_active'] is True

    async def test_create_new_recipient_type(self, client: AsyncClient, admin_headers):
        """Test creating new recipient type."""
        recipient_data = {
            "recipient_emails": ["test@example.com"],
            "description": "Test notification recipients",
            "is_active": True
        }

        response = await client.put(
            "/api/v1/email/recipients/test_notifications",
            headers=admin_headers,
            json=recipient_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data['notification_type'] == 'test_notifications'
        assert data['recipient_emails'] == ['test@example.com']


# ============================================================================
# PERMISSIONS TESTS
# ============================================================================


class TestEmailPermissions:
    """Test email access control"""

    async def test_admin_can_access_templates(self, client: AsyncClient, admin_headers):
        """Test admin can access email templates."""
        response = await client.get(
            "/api/v1/email/templates",
            headers=admin_headers
        )

        assert response.status_code == 200

    async def test_unauthenticated_cannot_access_templates(self, client: AsyncClient):
        """Test unauthenticated users cannot access templates."""
        response = await client.get("/api/v1/email/templates")

        assert response.status_code == 403

    async def test_unauthenticated_cannot_send_email(self, client: AsyncClient):
        """Test unauthenticated users cannot send email."""
        email_data = {
            "to_email": "test@example.com",
            "subject": "Test",
            "body": "Test body"
        }

        response = await client.post(
            "/api/v1/email/send",
            json=email_data
        )

        assert response.status_code == 403
