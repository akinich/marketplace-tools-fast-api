# HANDOVER MESSAGE #4: Webhook System

## 📋 MISSION
Build a complete **Webhook System** for event-driven integrations. Allow admins to configure webhooks that trigger on events like ticket created, user created, low stock, etc.

## 🎯 FEATURES TO BUILD

1. **Webhook Management:** CRUD for webhooks (URL, events, headers, secret)
2. **Event System:** Trigger webhooks when events occur
3. **Delivery Tracking:** Log all webhook deliveries with status
4. **Retry Logic:** Automatic retry for failed webhooks
5. **Security:** HMAC signature verification
6. **Admin UI:** Manage webhooks, view delivery logs, test webhooks

---

## 🗄️ PART 1: DATABASE MIGRATION

Create file: `backend/migrations/010_webhooks.sql`

```sql
-- ============================================================================
-- Migration 010: Webhook System
-- ============================================================================

-- Webhooks table
CREATE TABLE IF NOT EXISTS webhooks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    secret VARCHAR(255) NOT NULL,
    events TEXT[] NOT NULL DEFAULT '{}',
    custom_headers JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    timeout_seconds INTEGER DEFAULT 30 CHECK (timeout_seconds BETWEEN 5 AND 120),
    retry_attempts INTEGER DEFAULT 3 CHECK (retry_attempts BETWEEN 0 AND 10),
    retry_delay_seconds INTEGER DEFAULT 60 CHECK (retry_delay_seconds BETWEEN 10 AND 3600),
    description TEXT,
    created_by UUID REFERENCES auth.users(id),
    updated_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_webhooks_active ON webhooks(is_active);
CREATE INDEX idx_webhooks_events ON webhooks USING GIN(events);

-- Webhook deliveries table
CREATE TABLE IF NOT EXISTS webhook_deliveries (
    id SERIAL PRIMARY KEY,
    webhook_id INTEGER REFERENCES webhooks(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'success', 'failed', 'retrying')),
    response_status_code INTEGER,
    response_body TEXT,
    error_message TEXT,
    attempts INTEGER DEFAULT 0,
    delivered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_webhook_deliveries_webhook_id ON webhook_deliveries(webhook_id);
CREATE INDEX idx_webhook_deliveries_event_type ON webhook_deliveries(event_type);
CREATE INDEX idx_webhook_deliveries_status ON webhook_deliveries(status);
CREATE INDEX idx_webhook_deliveries_created_at ON webhook_deliveries(created_at DESC);

-- Triggers
CREATE TRIGGER trigger_update_webhooks_updated_at
    BEFORE UPDATE ON webhooks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_update_webhook_deliveries_updated_at
    BEFORE UPDATE ON webhook_deliveries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Verify migration
SELECT id, name, url, events, is_active FROM webhooks;
```

**Run this in Supabase and share output.**

---

## 🔧 PART 2: BACKEND IMPLEMENTATION

### File 1: Install dependency

Update `backend/requirements.txt`:
```
httpx==0.25.2
```

Run: `pip install httpx`

### File 2: `backend/app/models/webhooks.py`

```python
"""
Webhook Models
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime

class WebhookSchema(BaseModel):
    """Webhook configuration"""
    name: str
    url: HttpUrl
    events: List[str] = []
    custom_headers: Dict[str, str] = {}
    description: Optional[str] = None
    is_active: bool = True
    timeout_seconds: int = Field(default=30, ge=5, le=120)
    retry_attempts: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: int = Field(default=60, ge=10, le=3600)

class WebhookResponse(WebhookSchema):
    """Webhook with metadata"""
    id: int
    secret: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WebhookDeliveryResponse(BaseModel):
    """Webhook delivery log"""
    id: int
    webhook_id: int
    event_type: str
    payload: Dict[str, Any]
    status: str
    response_status_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    attempts: int
    delivered_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class WebhookTestRequest(BaseModel):
    """Test webhook"""
    webhook_id: int
    test_payload: Optional[Dict[str, Any]] = None
```

### File 3: `backend/app/services/webhook_service.py`

```python
"""
Webhook Service - Event-driven integrations
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

            # Send webhook
            result = await _send_webhook(
                url=delivery['url'],
                secret=delivery['secret'],
                event_type=delivery['event_type'],
                payload=delivery['payload'],
                custom_headers=delivery['custom_headers'],
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

    result = await _send_webhook(
        url=webhook['url'],
        secret=webhook['secret'],
        event_type='test',
        payload=payload,
        custom_headers=webhook['custom_headers'],
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
```

### File 4: `backend/app/routes/webhooks.py`

```python
"""
Webhook API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import secrets
from asyncpg import Connection

from app.database import get_db_connection
from app.dependencies import require_admin
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
    current_user: dict = Depends(require_admin),
    conn: Connection = Depends(get_db_connection)
):
    """List all webhooks"""
    webhooks = await conn.fetch("SELECT * FROM webhooks ORDER BY created_at DESC")
    return [dict(w) for w in webhooks]

@router.post("/", response_model=WebhookResponse)
async def create_webhook(
    webhook: WebhookSchema,
    current_user: dict = Depends(require_admin),
    conn: Connection = Depends(get_db_connection)
):
    """Create a new webhook"""
    # Generate secret
    secret = secrets.token_urlsafe(32)

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
        webhook.custom_headers,
        webhook.description,
        webhook.is_active,
        webhook.timeout_seconds,
        webhook.retry_attempts,
        webhook.retry_delay_seconds,
        current_user['user_id']
    )

    return dict(created)

@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    current_user: dict = Depends(require_admin),
    conn: Connection = Depends(get_db_connection)
):
    """Get webhook details"""
    webhook = await conn.fetchrow("SELECT * FROM webhooks WHERE id = $1", webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return dict(webhook)

@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    webhook: WebhookSchema,
    current_user: dict = Depends(require_admin),
    conn: Connection = Depends(get_db_connection)
):
    """Update webhook"""
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
        webhook.custom_headers,
        webhook.description,
        webhook.is_active,
        webhook.timeout_seconds,
        webhook.retry_attempts,
        webhook.retry_delay_seconds,
        current_user['user_id']
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return dict(updated)

@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    current_user: dict = Depends(require_admin),
    conn: Connection = Depends(get_db_connection)
):
    """Delete webhook"""
    result = await conn.execute("DELETE FROM webhooks WHERE id = $1", webhook_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"message": "Webhook deleted"}

@router.post("/test")
async def test_webhook(
    request: WebhookTestRequest,
    current_user: dict = Depends(require_admin),
    conn: Connection = Depends(get_db_connection)
):
    """Test a webhook"""
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
    current_user: dict = Depends(require_admin),
    conn: Connection = Depends(get_db_connection)
):
    """Get delivery logs for a webhook"""
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
    current_user: dict = Depends(require_admin)
):
    """Get list of available webhook events"""
    return {"events": webhook_service.AVAILABLE_EVENTS}
```

### File 5: Update `backend/app/routes/__init__.py`

```python
from app.routes import webhooks

app.include_router(webhooks.router, prefix="/api/v1")
```

### File 6: Update scheduler in `backend/app/main.py`

```python
from app.services import webhook_service

scheduler.add_job(
    process_webhook_queue_job,
    'interval',
    minutes=2,  # Process every 2 minutes
    id='process_webhook_queue',
    max_instances=1
)

async def process_webhook_queue_job():
    """Process webhook queue"""
    try:
        conn = await get_db_connection()
        await webhook_service.process_webhook_queue(conn, batch_size=20)
    except Exception as e:
        logger.error(f"Webhook queue processing failed: {e}")
```

### File 7: Integrate with existing code

In `backend/app/routes/tickets.py`, add webhook trigger:

```python
from app.services import webhook_service

@router.post("/api/v1/tickets")
async def create_ticket(...):
    ticket = await ticket_service.create(...)

    # Trigger webhook
    await webhook_service.trigger_event(
        conn,
        'ticket.created',
        {
            "id": ticket['id'],
            "title": ticket['title'],
            "priority": ticket['priority'],
            "created_by": ticket['created_by_email']
        }
    )

    return ticket
```

---

## 🎨 PART 3: FRONTEND IMPLEMENTATION

### File 1: `frontend/src/api/webhooks.js`

```javascript
import apiClient from './client';

export const webhooksAPI = {
  list: async () => {
    const response = await apiClient.get('/webhooks');
    return response.data;
  },

  get: async (id) => {
    const response = await apiClient.get(`/webhooks/${id}`);
    return response.data;
  },

  create: async (data) => {
    const response = await apiClient.post('/webhooks', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await apiClient.put(`/webhooks/${id}`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await apiClient.delete(`/webhooks/${id}`);
    return response.data;
  },

  test: async (webhookId, testPayload = null) => {
    const response = await apiClient.post('/webhooks/test', {
      webhook_id: webhookId,
      test_payload: testPayload
    });
    return response.data;
  },

  getDeliveries: async (webhookId, limit = 50, status = null) => {
    const params = { limit };
    if (status) params.status = status;
    const response = await apiClient.get(`/webhooks/${webhookId}/deliveries`, { params });
    return response.data;
  },

  getAvailableEvents: async () => {
    const response = await apiClient.get('/webhooks/events/available');
    return response.data;
  }
};
```

### File 2: `frontend/src/pages/WebhooksPage.jsx`

```javascript
import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Button,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  Typography,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Send as SendIcon,
  History as HistoryIcon
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { webhooksAPI } from '../api/webhooks';

function WebhooksPage() {
  const { enqueueSnackbar } = useSnackbar();
  const [webhooks, setWebhooks] = useState([]);
  const [availableEvents, setAvailableEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingWebhook, setEditingWebhook] = useState(null);
  const [deliveriesDialogOpen, setDeliveriesDialogOpen] = useState(false);
  const [deliveries, setDeliveries] = useState([]);

  const [formData, setFormData] = useState({
    name: '',
    url: '',
    events: [],
    description: '',
    is_active: true,
    timeout_seconds: 30,
    retry_attempts: 3
  });

  useEffect(() => {
    loadWebhooks();
    loadAvailableEvents();
  }, []);

  const loadWebhooks = async () => {
    try {
      setLoading(true);
      const data = await webhooksAPI.list();
      setWebhooks(data);
      setLoading(false);
    } catch (error) {
      enqueueSnackbar('Failed to load webhooks', { variant: 'error' });
      setLoading(false);
    }
  };

  const loadAvailableEvents = async () => {
    try {
      const data = await webhooksAPI.getAvailableEvents();
      setAvailableEvents(data.events);
    } catch (error) {
      console.error('Failed to load events:', error);
    }
  };

  const handleSubmit = async () => {
    try {
      if (editingWebhook) {
        await webhooksAPI.update(editingWebhook.id, formData);
        enqueueSnackbar('Webhook updated', { variant: 'success' });
      } else {
        await webhooksAPI.create(formData);
        enqueueSnackbar('Webhook created', { variant: 'success' });
      }
      setDialogOpen(false);
      setEditingWebhook(null);
      loadWebhooks();
    } catch (error) {
      enqueueSnackbar(error.response?.data?.detail || 'Failed to save webhook', { variant: 'error' });
    }
  };

  const handleEdit = (webhook) => {
    setEditingWebhook(webhook);
    setFormData({
      name: webhook.name,
      url: webhook.url,
      events: webhook.events,
      description: webhook.description || '',
      is_active: webhook.is_active,
      timeout_seconds: webhook.timeout_seconds,
      retry_attempts: webhook.retry_attempts
    });
    setDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this webhook?')) return;

    try {
      await webhooksAPI.delete(id);
      enqueueSnackbar('Webhook deleted', { variant: 'success' });
      loadWebhooks();
    } catch (error) {
      enqueueSnackbar('Failed to delete webhook', { variant: 'error' });
    }
  };

  const handleTest = async (webhook) => {
    try {
      const result = await webhooksAPI.test(webhook.id);
      if (result.success) {
        enqueueSnackbar('Test webhook sent successfully', { variant: 'success' });
      } else {
        enqueueSnackbar(`Test failed: ${result.error}`, { variant: 'error' });
      }
    } catch (error) {
      enqueueSnackbar('Failed to test webhook', { variant: 'error' });
    }
  };

  const handleViewDeliveries = async (webhook) => {
    try {
      const data = await webhooksAPI.getDeliveries(webhook.id);
      setDeliveries(data);
      setDeliveriesDialogOpen(true);
    } catch (error) {
      enqueueSnackbar('Failed to load deliveries', { variant: 'error' });
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success': return 'success';
      case 'failed': return 'error';
      case 'pending': return 'warning';
      case 'retrying': return 'info';
      default: return 'default';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4">Webhooks</Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              setEditingWebhook(null);
              setFormData({
                name: '',
                url: '',
                events: [],
                description: '',
                is_active: true,
                timeout_seconds: 30,
                retry_attempts: 3
              });
              setDialogOpen(true);
            }}
          >
            Add Webhook
          </Button>
        </Box>

        <Alert severity="info" sx={{ mb: 2 }}>
          Webhooks allow you to receive real-time notifications when events occur.
          Configure endpoints to integrate with external services like Slack, Discord, or custom applications.
        </Alert>

        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>URL</TableCell>
              <TableCell>Events</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {webhooks.map(webhook => (
              <TableRow key={webhook.id}>
                <TableCell>{webhook.name}</TableCell>
                <TableCell>{webhook.url}</TableCell>
                <TableCell>
                  {webhook.events.map(event => (
                    <Chip key={event} label={event} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                  ))}
                </TableCell>
                <TableCell>
                  <Chip
                    label={webhook.is_active ? 'Active' : 'Inactive'}
                    color={webhook.is_active ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <IconButton size="small" onClick={() => handleTest(webhook)}>
                    <SendIcon />
                  </IconButton>
                  <IconButton size="small" onClick={() => handleViewDeliveries(webhook)}>
                    <HistoryIcon />
                  </IconButton>
                  <IconButton size="small" onClick={() => handleEdit(webhook)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton size="small" onClick={() => handleDelete(webhook.id)}>
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingWebhook ? 'Edit Webhook' : 'Create Webhook'}</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            sx={{ mt: 2, mb: 2 }}
          />
          <TextField
            fullWidth
            label="URL"
            value={formData.url}
            onChange={(e) => setFormData({...formData, url: e.target.value})}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Events</InputLabel>
            <Select
              multiple
              value={formData.events}
              onChange={(e) => setFormData({...formData, events: e.target.value})}
              renderValue={(selected) => selected.join(', ')}
            >
              {availableEvents.map(event => (
                <MenuItem key={event} value={event}>{event}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            fullWidth
            label="Description"
            multiline
            rows={2}
            value={formData.description}
            onChange={(e) => setFormData({...formData, description: e.target.value})}
            sx={{ mb: 2 }}
          />
          <FormControlLabel
            control={
              <Switch
                checked={formData.is_active}
                onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
              />
            }
            label="Active"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingWebhook ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Deliveries Dialog */}
      <Dialog
        open={deliveriesDialogOpen}
        onClose={() => setDeliveriesDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Delivery Log</DialogTitle>
        <DialogContent>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Event</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Attempts</TableCell>
                <TableCell>Time</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {deliveries.map(delivery => (
                <TableRow key={delivery.id}>
                  <TableCell>{delivery.event_type}</TableCell>
                  <TableCell>
                    <Chip label={delivery.status} color={getStatusColor(delivery.status)} size="small" />
                  </TableCell>
                  <TableCell>{delivery.attempts}</TableCell>
                  <TableCell>{new Date(delivery.created_at).toLocaleString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeliveriesDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default WebhooksPage;
```

### File 3: Add route in `frontend/src/App.jsx`

```javascript
import WebhooksPage from './pages/WebhooksPage';

<Route path="/communication/webhooks" element={<WebhooksPage />} />
```

---

## 🧪 TESTING

1. Create webhook pointing to webhook.site or requestbin.com
2. Select events (e.g., ticket.created)
3. Click Test - verify webhook received
4. Create a ticket - verify webhook triggered
5. Check delivery log

---

## ✅ VERIFICATION CHECKLIST

- [ ] Can create webhook
- [ ] Test webhook works
- [ ] Webhooks trigger on events
- [ ] Delivery log shows attempts
- [ ] Retry logic works for failures
- [ ] Can view delivery history

---

**READY FOR HANDOVER #5: API Key Management**
