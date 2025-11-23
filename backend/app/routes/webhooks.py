"""
Webhook API Routes
Version: 1.0.0
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import secrets
import json

from app.database import get_db
from app.auth.dependencies import require_admin
from app.schemas.auth import CurrentUser
from app.models.webhooks import (
    WebhookSchema,
    WebhookResponse,
    WebhookDeliveryResponse,
    WebhookTestRequest
)
from app.services import webhook_service

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.get("/", response_model=List[WebhookResponse])
async def list_webhooks(
    current_user: CurrentUser = Depends(require_admin)
):
    """List all webhooks"""
    pool = get_db()
    async with pool.acquire() as conn:
        webhooks = await conn.fetch("SELECT * FROM webhooks ORDER BY created_at DESC")
        return [dict(w) for w in webhooks]

@router.post("/", response_model=WebhookResponse)
async def create_webhook(
    webhook: WebhookSchema,
    current_user: CurrentUser = Depends(require_admin)
):
    """Create a new webhook"""
    # Generate secret
    secret = secrets.token_urlsafe(32)

    pool = get_db()
    async with pool.acquire() as conn:
        created = await conn.fetchrow(
            """
            INSERT INTO webhooks (
                name, url, secret, events, custom_headers, description,
                is_active, timeout_seconds, retry_attempts, retry_delay_seconds,
                created_by
            )
            VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9, $10, $11)
            RETURNING *
            """,
            webhook.name,
            str(webhook.url),
            secret,
            webhook.events,
            json.dumps(webhook.custom_headers),
            webhook.description,
            webhook.is_active,
            webhook.timeout_seconds,
            webhook.retry_attempts,
            webhook.retry_delay_seconds,
            current_user.id
        )

        return dict(created)

@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    current_user: CurrentUser = Depends(require_admin)
):
    """Get webhook details"""
    pool = get_db()
    async with pool.acquire() as conn:
        webhook = await conn.fetchrow("SELECT * FROM webhooks WHERE id = $1", webhook_id)
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        return dict(webhook)

@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    webhook: WebhookSchema,
    current_user: CurrentUser = Depends(require_admin)
):
    """Update webhook"""
    pool = get_db()
    async with pool.acquire() as conn:
        updated = await conn.fetchrow(
            """
            UPDATE webhooks SET
                name = $2, url = $3, events = $4, custom_headers = $5::jsonb,
                description = $6, is_active = $7, timeout_seconds = $8,
                retry_attempts = $9, retry_delay_seconds = $10, updated_by = $11
            WHERE id = $1
            RETURNING *
            """,
            webhook_id,
            webhook.name,
            str(webhook.url),
            webhook.events,
            json.dumps(webhook.custom_headers),
            webhook.description,
            webhook.is_active,
            webhook.timeout_seconds,
            webhook.retry_attempts,
            webhook.retry_delay_seconds,
            current_user.id
        )

        if not updated:
            raise HTTPException(status_code=404, detail="Webhook not found")

        return dict(updated)

@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    current_user: CurrentUser = Depends(require_admin)
):
    """Delete webhook"""
    pool = get_db()
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM webhooks WHERE id = $1", webhook_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Webhook not found")
        return {"message": "Webhook deleted"}

@router.post("/test")
async def test_webhook(
    request: WebhookTestRequest,
    current_user: CurrentUser = Depends(require_admin)
):
    """Test a webhook"""
    pool = get_db()
    async with pool.acquire() as conn:
        try:
            result = await webhook_service.test_webhook(
                conn,
                request.webhook_id,
                request.test_payload
            )
            return result
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

@router.get("/{webhook_id}/deliveries", response_model=List[WebhookDeliveryResponse])
async def get_webhook_deliveries(
    webhook_id: int,
    limit: int = 50,
    status: Optional[str] = None,
    current_user: CurrentUser = Depends(require_admin)
):
    """Get delivery logs for a webhook"""
    pool = get_db()
    async with pool.acquire() as conn:
        if status:
            deliveries = await conn.fetch(
                """
                SELECT * FROM webhook_deliveries
                WHERE webhook_id = $1 AND status = $2
                ORDER BY created_at DESC
                LIMIT $3
                """,
                webhook_id, status, limit
            )
        else:
            deliveries = await conn.fetch(
                """
                SELECT * FROM webhook_deliveries
                WHERE webhook_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                webhook_id, limit
            )

        return [dict(d) for d in deliveries]

@router.get("/events/available")
async def get_available_events(
    current_user: CurrentUser = Depends(require_admin)
):
    """Get list of available webhook events"""
    return {"events": webhook_service.AVAILABLE_EVENTS}
