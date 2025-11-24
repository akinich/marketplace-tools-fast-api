"""
Webhook Service - Event-driven integrations
Version: 1.0.0
"""
import httpx
import hmac
import hashlib
import json
import logging
from typing import Dict, Any, List, Optional
from asyncpg import Connection
from datetime import datetime

logger = logging.getLogger(__name__)

AVAILABLE_EVENTS = [
    'ticket.created',
    'ticket.updated',
    'ticket.closed',
    'user.created',
    'user.updated',
    'inventory.low_stock',
    'purchase_order.created',
    'purchase_order.approved',
]

async def trigger_event(
    conn: Connection,
    event_type: str,
    payload: Dict[str, Any]
):
    """
    Trigger webhooks for an event
    """
    if event_type not in AVAILABLE_EVENTS:
        logger.warning(f"Unknown event type: {event_type}")
        return

    # Get active webhooks subscribed to this event
    webhooks = await conn.fetch(
        """
        SELECT id, url, secret, custom_headers, timeout_seconds
        FROM webhooks
        WHERE is_active = true AND $1 = ANY(events)
        """,
        event_type
    )

    if not webhooks:
        logger.debug(f"No webhooks subscribed to {event_type}")
        return

    logger.info(f"Triggering {len(webhooks)} webhooks for event: {event_type}")

    for webhook in webhooks:
        # Queue delivery
        await queue_webhook_delivery(
            conn,
            webhook_id=webhook['id'],
            event_type=event_type,
            payload=payload
        )

async def queue_webhook_delivery(
    conn: Connection,
    webhook_id: int,
    event_type: str,
    payload: Dict[str, Any]
) -> int:
    """Queue a webhook delivery"""
    delivery_id = await conn.fetchval(
        """
        INSERT INTO webhook_deliveries (webhook_id, event_type, payload, status)
        VALUES ($1, $2, $3::jsonb, 'pending')
        RETURNING id
        """,
        webhook_id,
        event_type,
        json.dumps(payload)
    )

    logger.debug(f"Webhook delivery queued: {delivery_id}")
    return delivery_id

async def process_webhook_queue(conn: Connection, batch_size: int = 10):
    """
    Process pending webhook deliveries
    Called by background scheduler
    """
    # Get pending deliveries
    deliveries = await conn.fetch(
        """
        SELECT
            wd.id,
            wd.webhook_id,
            wd.event_type,
            wd.payload,
            wd.attempts,
            w.url,
            w.secret,
            w.custom_headers,
            w.timeout_seconds,
            w.retry_attempts
        FROM webhook_deliveries wd
        JOIN webhooks w ON wd.webhook_id = w.id
        WHERE wd.status IN ('pending', 'retrying')
          AND wd.attempts < w.retry_attempts
          AND w.is_active = true
        ORDER BY wd.created_at ASC
        LIMIT $1
        FOR UPDATE SKIP LOCKED
        """,
        batch_size
    )

    if not deliveries:
        return

    logger.info(f"Processing {len(deliveries)} webhook deliveries")

    for delivery in deliveries:
        delivery_id = delivery['id']

        try:
            # Mark as sending
            await conn.execute(
                """
                UPDATE webhook_deliveries
                SET status = 'retrying', attempts = attempts + 1
                WHERE id = $1
                """,
                delivery_id
            )

            # Parse JSON fields if they're strings
            payload = delivery['payload']
            if isinstance(payload, str):
                payload = json.loads(payload) if payload else {}

            custom_headers = delivery['custom_headers']
            if isinstance(custom_headers, str):
                custom_headers = json.loads(custom_headers) if custom_headers else {}

            # Send webhook
            result = await _send_webhook(
                url=delivery['url'],
                secret=delivery['secret'],
                event_type=delivery['event_type'],
                payload=payload,
                custom_headers=custom_headers,
                timeout=delivery['timeout_seconds']
            )

            # Update delivery status
            if result['success']:
                await conn.execute(
                    """
                    UPDATE webhook_deliveries
                    SET
                        status = 'success',
                        response_status_code = $2,
                        response_body = $3,
                        delivered_at = NOW()
                    WHERE id = $1
                    """,
                    delivery_id,
                    result['status_code'],
                    result['response_body']
                )
                logger.info(f"Webhook delivered successfully: {delivery_id}")
            else:
                # Check if max attempts reached
                if delivery['attempts'] + 1 >= delivery['retry_attempts']:
                    status = 'failed'
                else:
                    status = 'pending'  # Will retry

                await conn.execute(
                    """
                    UPDATE webhook_deliveries
                    SET
                        status = $2,
                        response_status_code = $3,
                        response_body = $4,
                        error_message = $5
                    WHERE id = $1
                    """,
                    delivery_id,
                    status,
                    result.get('status_code'),
                    result.get('response_body'),
                    result.get('error')
                )
                logger.warning(f"Webhook delivery failed: {delivery_id} - {result.get('error')}")

        except Exception as e:
            logger.error(f"Error processing webhook delivery {delivery_id}: {e}")
            await conn.execute(
                """
                UPDATE webhook_deliveries
                SET status = 'failed', error_message = $2
                WHERE id = $1
                """,
                delivery_id,
                str(e)
            )

async def test_webhook(
    conn: Connection,
    webhook_id: int,
    test_payload: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Test a webhook"""
    webhook = await conn.fetchrow(
        "SELECT url, secret, custom_headers, timeout_seconds FROM webhooks WHERE id = $1",
        webhook_id
    )

    if not webhook:
        raise ValueError("Webhook not found")

    payload = test_payload or {
        "event": "test",
        "message": "This is a test webhook",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Parse custom_headers if it's a JSON string
    custom_headers = webhook['custom_headers']
    if isinstance(custom_headers, str):
        custom_headers = json.loads(custom_headers) if custom_headers else {}

    result = await _send_webhook(
        url=webhook['url'],
        secret=webhook['secret'],
        event_type='test',
        payload=payload,
        custom_headers=custom_headers,
        timeout=webhook['timeout_seconds']
    )

    return result

async def _send_webhook(
    url: str,
    secret: str,
    event_type: str,
    payload: Dict[str, Any],
    custom_headers: Optional[Dict[str, str]] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Send webhook HTTP request
    """
    # Prepare payload
    webhook_payload = {
        "event": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": payload
    }

    payload_json = json.dumps(webhook_payload)

    # Generate HMAC signature
    signature = _generate_signature(payload_json, secret)

    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "X-Webhook-Event": event_type,
        "User-Agent": "FarmManagementSystem-Webhook/1.0"
    }

    if custom_headers:
        headers.update(custom_headers)

    # Send request
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                url,
                content=payload_json,
                headers=headers
            )

            return {
                "success": 200 <= response.status_code < 300,
                "status_code": response.status_code,
                "response_body": response.text[:1000],  # Limit to 1000 chars
            }

    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "Request timeout"
        }
    except httpx.RequestError as e:
        return {
            "success": False,
            "error": f"Request error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }

def _generate_signature(payload: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature"""
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify webhook signature"""
    expected_signature = _generate_signature(payload, secret)
    return hmac.compare_digest(signature, expected_signature)
