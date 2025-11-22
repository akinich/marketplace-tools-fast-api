# HANDOVER MESSAGE #3: SMTP Email Service

## 📋 MISSION
Build a complete **SMTP Email Service** with template management, email queue, recipient management, and integration with existing notifications (tickets, low stock, etc.).

**Note:** Password reset emails will remain with Supabase for now. We'll migrate them later once SMTP is proven stable.

## 🎯 WHAT YOU NEED TO BUILD

### Features:
1. **SMTP Configuration:** Admin UI to configure SMTP settings
2. **Email Templates:** Create/edit HTML + plain text email templates
3. **Email Queue:** Background processing with retry logic
4. **Recipient Lists:** Configure email recipients for different notification types
5. **Test Email:** Send test emails to verify configuration
6. **Integration:** Connect to existing ticket and inventory notifications

---

## 🗄️ PART 1: DATABASE MIGRATION

Create file: `backend/migrations/009_smtp_email.sql`

```sql
-- ============================================================================
-- Migration 009: SMTP Email Service
-- ============================================================================

-- Email templates table
CREATE TABLE IF NOT EXISTS email_templates (
    id SERIAL PRIMARY KEY,
    template_key VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    subject VARCHAR(500) NOT NULL,
    html_body TEXT NOT NULL,
    plain_body TEXT NOT NULL,
    variables JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES auth.users(id),
    updated_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_email_templates_key ON email_templates(template_key);

-- Email queue table
CREATE TABLE IF NOT EXISTS email_queue (
    id SERIAL PRIMARY KEY,
    to_email VARCHAR(255) NOT NULL,
    cc_emails TEXT[],
    bcc_emails TEXT[],
    subject VARCHAR(500) NOT NULL,
    html_body TEXT,
    plain_body TEXT NOT NULL,
    template_key VARCHAR(100),
    template_variables JSONB,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'sending', 'sent', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    error_message TEXT,
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_email_queue_status ON email_queue(status);
CREATE INDEX idx_email_queue_scheduled ON email_queue(scheduled_at);
CREATE INDEX idx_email_queue_to_email ON email_queue(to_email);

-- Email recipients configuration (for notification emails)
CREATE TABLE IF NOT EXISTS email_recipients (
    id SERIAL PRIMARY KEY,
    notification_type VARCHAR(100) NOT NULL,
    recipient_emails TEXT[] NOT NULL,
    is_active BOOLEAN DEFAULT true,
    description TEXT,
    created_by UUID REFERENCES auth.users(id),
    updated_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(notification_type)
);

CREATE INDEX idx_email_recipients_type ON email_recipients(notification_type);

-- Email send log (for tracking)
CREATE TABLE IF NOT EXISTS email_send_log (
    id SERIAL PRIMARY KEY,
    email_queue_id INTEGER REFERENCES email_queue(id) ON DELETE CASCADE,
    to_email VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_email_send_log_queue_id ON email_send_log(email_queue_id);
CREATE INDEX idx_email_send_log_status ON email_send_log(status);

-- Triggers for updated_at
CREATE TRIGGER trigger_update_email_templates_updated_at
    BEFORE UPDATE ON email_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_update_email_queue_updated_at
    BEFORE UPDATE ON email_queue
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_update_email_recipients_updated_at
    BEFORE UPDATE ON email_recipients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default email templates
INSERT INTO email_templates (template_key, name, description, subject, html_body, plain_body, variables) VALUES

-- Welcome email
('welcome', 'Welcome Email', 'Sent when a new user account is created',
'Welcome to {{app_name}}',
'<!DOCTYPE html>
<html>
<head><style>body{font-family:Arial,sans-serif;line-height:1.6;}</style></head>
<body>
<h2>Welcome to {{app_name}}!</h2>
<p>Hi {{user_name}},</p>
<p>Your account has been created successfully. Here are your login details:</p>
<ul>
<li><strong>Email:</strong> {{user_email}}</li>
<li><strong>Temporary Password:</strong> {{temp_password}}</li>
</ul>
<p>Please log in and change your password immediately.</p>
<p><a href="{{login_url}}" style="background:#007bff;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;display:inline-block;">Login Now</a></p>
<p>If you have any questions, contact us at {{support_email}}.</p>
<p>Best regards,<br>{{app_name}} Team</p>
</body>
</html>',
'Welcome to {{app_name}}!

Hi {{user_name}},

Your account has been created successfully. Here are your login details:

Email: {{user_email}}
Temporary Password: {{temp_password}}

Please log in and change your password immediately.

Login at: {{login_url}}

If you have any questions, contact us at {{support_email}}.

Best regards,
{{app_name}} Team',
'["app_name", "user_name", "user_email", "temp_password", "login_url", "support_email"]'::jsonb),

-- Ticket created
('ticket_created', 'Ticket Created', 'Sent when a new ticket is created',
'New Ticket Created: {{ticket_title}}',
'<!DOCTYPE html>
<html>
<head><style>body{font-family:Arial,sans-serif;line-height:1.6;}.priority-high{color:#dc3545;} .priority-medium{color:#ffc107;} .priority-low{color:#28a745;}</style></head>
<body>
<h2>New Ticket Created</h2>
<p><strong>Title:</strong> {{ticket_title}}</p>
<p><strong>Priority:</strong> <span class="priority-{{priority}}">{{priority}}</span></p>
<p><strong>Type:</strong> {{ticket_type}}</p>
<p><strong>Created by:</strong> {{created_by}}</p>
<p><strong>Description:</strong></p>
<p>{{description}}</p>
<p><a href="{{ticket_url}}" style="background:#007bff;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;display:inline-block;">View Ticket</a></p>
</body>
</html>',
'New Ticket Created

Title: {{ticket_title}}
Priority: {{priority}}
Type: {{ticket_type}}
Created by: {{created_by}}

Description:
{{description}}

View ticket at: {{ticket_url}}',
'["ticket_title", "priority", "ticket_type", "created_by", "description", "ticket_url"]'::jsonb),

-- Low stock alert
('low_stock_alert', 'Low Stock Alert', 'Sent when items are below reorder level',
'Low Stock Alert: {{item_count}} items need attention',
'<!DOCTYPE html>
<html>
<head><style>body{font-family:Arial,sans-serif;line-height:1.6;}table{border-collapse:collapse;width:100%;}th,td{border:1px solid #ddd;padding:8px;text-align:left;}th{background:#f2f2f2;}</style></head>
<body>
<h2>Low Stock Alert</h2>
<p>The following items are below their reorder levels:</p>
<table>
<tr><th>Item</th><th>Current Stock</th><th>Reorder Level</th></tr>
{{#items}}
<tr><td>{{name}}</td><td>{{current_quantity}}</td><td>{{reorder_level}}</td></tr>
{{/items}}
</table>
<p><a href="{{inventory_url}}" style="background:#007bff;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;display:inline-block;">View Inventory</a></p>
</body>
</html>',
'Low Stock Alert

The following items are below their reorder levels:

{{#items}}
- {{name}}: {{current_quantity}} (reorder at {{reorder_level}})
{{/items}}

View inventory at: {{inventory_url}}',
'["item_count", "items", "inventory_url"]'::jsonb)

ON CONFLICT (template_key) DO NOTHING;

-- Insert default email recipients
INSERT INTO email_recipients (notification_type, recipient_emails, description) VALUES
('tickets_critical', ARRAY[]::TEXT[], 'Recipients for critical priority tickets'),
('tickets_all', ARRAY[]::TEXT[], 'Recipients for all ticket notifications'),
('low_stock', ARRAY[]::TEXT[], 'Recipients for low stock alerts'),
('user_created', ARRAY[]::TEXT[], 'Recipients notified when new users are created')
ON CONFLICT (notification_type) DO NOTHING;

-- Verify migration
SELECT * FROM email_templates ORDER BY template_key;
SELECT * FROM email_recipients ORDER BY notification_type;
```

**Run this migration in Supabase and share output.**

---

## 🔧 PART 2: BACKEND IMPLEMENTATION

### File 1: Install dependencies

Update `backend/requirements.txt`:
```
aiosmtplib==3.0.1
jinja2==3.1.2
```

Run: `pip install aiosmtplib jinja2`

### File 2: `backend/app/models/email.py`

```python
"""
Email Models
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class EmailTemplateSchema(BaseModel):
    """Email template model"""
    template_key: str
    name: str
    description: Optional[str] = None
    subject: str
    html_body: str
    plain_body: str
    variables: List[str] = []
    is_active: bool = True

class EmailTemplateResponse(EmailTemplateSchema):
    """Email template with metadata"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EmailQueueSchema(BaseModel):
    """Email queue entry"""
    to_email: EmailStr
    cc_emails: Optional[List[EmailStr]] = None
    bcc_emails: Optional[List[EmailStr]] = None
    subject: str
    html_body: Optional[str] = None
    plain_body: str
    template_key: Optional[str] = None
    template_variables: Optional[Dict[str, Any]] = None
    priority: int = Field(default=5, ge=1, le=10)
    scheduled_at: Optional[datetime] = None

class EmailQueueResponse(EmailQueueSchema):
    """Email queue with status"""
    id: int
    status: str
    attempts: int
    max_attempts: int
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SendEmailRequest(BaseModel):
    """Request to send email"""
    to_email: EmailStr
    subject: str
    body: str
    html_body: Optional[str] = None
    cc_emails: Optional[List[EmailStr]] = None

class SendTemplateEmailRequest(BaseModel):
    """Request to send template email"""
    to_email: EmailStr
    template_key: str
    variables: Dict[str, Any]
    cc_emails: Optional[List[EmailStr]] = None

class EmailRecipientsSchema(BaseModel):
    """Email recipients configuration"""
    notification_type: str
    recipient_emails: List[EmailStr]
    description: Optional[str] = None
    is_active: bool = True

class EmailRecipientsResponse(EmailRecipientsSchema):
    """Email recipients with metadata"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SMTPTestRequest(BaseModel):
    """Test SMTP configuration"""
    test_email: EmailStr
```

### File 3: `backend/app/services/email_service.py`

```python
"""
Email Service - SMTP email sending with templates and queue
"""
import aiosmtplib
import logging
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from typing import Optional, List, Dict, Any
from asyncpg import Connection

from app.services import settings_service

logger = logging.getLogger(__name__)

async def send_email(
    conn: Connection,
    to_email: str,
    subject: str,
    plain_body: str,
    html_body: Optional[str] = None,
    cc_emails: Optional[List[str]] = None,
    priority: int = 5
) -> int:
    """
    Queue an email for sending
    Returns: email_queue_id
    """
    email_id = await conn.fetchval(
        """
        INSERT INTO email_queue (
            to_email, cc_emails, subject, plain_body, html_body, priority
        )
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
        """,
        to_email,
        cc_emails or [],
        subject,
        plain_body,
        html_body,
        priority
    )

    logger.info(f"Email queued: {email_id} to {to_email}")
    return email_id

async def send_template_email(
    conn: Connection,
    to_email: str,
    template_key: str,
    variables: Dict[str, Any],
    cc_emails: Optional[List[str]] = None,
    priority: int = 5
) -> int:
    """
    Send email using a template
    """
    # Get template
    template = await conn.fetchrow(
        """
        SELECT subject, html_body, plain_body
        FROM email_templates
        WHERE template_key = $1 AND is_active = true
        """,
        template_key
    )

    if not template:
        raise ValueError(f"Template '{template_key}' not found or inactive")

    # Render template
    subject = Template(template['subject']).render(**variables)
    html_body = Template(template['html_body']).render(**variables)
    plain_body = Template(template['plain_body']).render(**variables)

    # Queue email
    email_id = await conn.fetchval(
        """
        INSERT INTO email_queue (
            to_email, cc_emails, subject, plain_body, html_body,
            template_key, template_variables, priority
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8)
        RETURNING id
        """,
        to_email,
        cc_emails or [],
        subject,
        plain_body,
        html_body,
        template_key,
        variables,
        priority
    )

    logger.info(f"Template email queued: {email_id} using {template_key}")
    return email_id

async def process_email_queue(conn: Connection, batch_size: int = 10):
    """
    Process pending emails in queue
    Called by background scheduler
    """
    # Check if SMTP is enabled
    smtp_enabled = await settings_service.get_setting(conn, 'email.smtp_enabled', False)
    if not smtp_enabled:
        logger.debug("SMTP is disabled, skipping email processing")
        return

    # Get pending emails
    emails = await conn.fetch(
        """
        SELECT id, to_email, cc_emails, subject, plain_body, html_body, attempts, max_attempts
        FROM email_queue
        WHERE status = 'pending'
          AND scheduled_at <= NOW()
          AND attempts < max_attempts
        ORDER BY priority DESC, created_at ASC
        LIMIT $1
        FOR UPDATE SKIP LOCKED
        """,
        batch_size
    )

    if not emails:
        return

    logger.info(f"Processing {len(emails)} queued emails")

    # Get SMTP settings
    smtp_settings = await _get_smtp_settings(conn)

    for email in emails:
        email_id = email['id']

        try:
            # Mark as sending
            await conn.execute(
                "UPDATE email_queue SET status = 'sending', attempts = attempts + 1 WHERE id = $1",
                email_id
            )

            # Send email
            await _send_smtp_email(
                smtp_settings,
                to_email=email['to_email'],
                cc_emails=email['cc_emails'],
                subject=email['subject'],
                plain_body=email['plain_body'],
                html_body=email['html_body']
            )

            # Mark as sent
            await conn.execute(
                """
                UPDATE email_queue
                SET status = 'sent', sent_at = NOW()
                WHERE id = $1
                """,
                email_id
            )

            # Log success
            await conn.execute(
                """
                INSERT INTO email_send_log (email_queue_id, to_email, subject, status)
                VALUES ($1, $2, $3, 'sent')
                """,
                email_id, email['to_email'], email['subject']
            )

            logger.info(f"Email sent successfully: {email_id}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send email {email_id}: {error_msg}")

            # Check if max attempts reached
            if email['attempts'] + 1 >= email['max_attempts']:
                status = 'failed'
            else:
                status = 'pending'  # Will retry

            await conn.execute(
                """
                UPDATE email_queue
                SET status = $1, error_message = $2
                WHERE id = $3
                """,
                status, error_msg, email_id
            )

            # Log failure
            await conn.execute(
                """
                INSERT INTO email_send_log (email_queue_id, to_email, subject, status, error_message)
                VALUES ($1, $2, $3, 'failed', $4)
                """,
                email_id, email['to_email'], email['subject'], error_msg
            )

async def test_smtp_connection(conn: Connection, test_email: str) -> Dict[str, Any]:
    """Test SMTP configuration by sending a test email"""
    smtp_settings = await _get_smtp_settings(conn)

    try:
        await _send_smtp_email(
            smtp_settings,
            to_email=test_email,
            subject="SMTP Test Email",
            plain_body="This is a test email from your Farm Management System. SMTP is configured correctly!",
            html_body="<h2>SMTP Test Email</h2><p>This is a test email from your Farm Management System.</p><p><strong>SMTP is configured correctly!</strong></p>"
        )

        return {"success": True, "message": f"Test email sent to {test_email}"}
    except Exception as e:
        return {"success": False, "message": str(e)}

async def get_email_recipients(conn: Connection, notification_type: str) -> List[str]:
    """Get email recipients for a notification type"""
    row = await conn.fetchrow(
        """
        SELECT recipient_emails
        FROM email_recipients
        WHERE notification_type = $1 AND is_active = true
        """,
        notification_type
    )

    return row['recipient_emails'] if row else []

async def _get_smtp_settings(conn: Connection) -> Dict[str, Any]:
    """Get SMTP configuration from settings"""
    return {
        'host': await settings_service.get_setting(conn, 'email.smtp_host', ''),
        'port': await settings_service.get_setting(conn, 'email.smtp_port', 587),
        'use_tls': await settings_service.get_setting(conn, 'email.smtp_use_tls', True),
        'username': await settings_service.get_setting(conn, 'email.smtp_user', ''),
        'password': await settings_service.get_setting(conn, 'email.smtp_password', ''),
        'from_email': await settings_service.get_setting(conn, 'email.from_email', 'noreply@farmapp.com'),
        'from_name': await settings_service.get_setting(conn, 'email.from_name', 'Farm Management System'),
    }

async def _send_smtp_email(
    smtp_settings: Dict[str, Any],
    to_email: str,
    subject: str,
    plain_body: str,
    html_body: Optional[str] = None,
    cc_emails: Optional[List[str]] = None
):
    """Actually send email via SMTP"""
    # Create message
    if html_body:
        message = MIMEMultipart('alternative')
        message.attach(MIMEText(plain_body, 'plain'))
        message.attach(MIMEText(html_body, 'html'))
    else:
        message = MIMEText(plain_body, 'plain')

    message['From'] = f"{smtp_settings['from_name']} <{smtp_settings['from_email']}>"
    message['To'] = to_email
    message['Subject'] = subject

    if cc_emails:
        message['Cc'] = ', '.join(cc_emails)

    # Send via SMTP
    await aiosmtplib.send(
        message,
        hostname=smtp_settings['host'],
        port=smtp_settings['port'],
        username=smtp_settings['username'],
        password=smtp_settings['password'],
        use_tls=smtp_settings['use_tls'],
        timeout=30
    )
```

### File 4: `backend/app/routes/email.py`

```python
"""
Email API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from asyncpg import Connection

from app.database import get_db_connection
from app.dependencies import require_admin
from app.models.email import (
    EmailTemplateResponse,
    EmailQueueResponse,
    SendEmailRequest,
    SendTemplateEmailRequest,
    EmailRecipientsSchema,
    EmailRecipientsResponse,
    SMTPTestRequest
)
from app.services import email_service

router = APIRouter(prefix="/email", tags=["Email"])

# ============================================================================
# Email Templates
# ============================================================================

@router.get("/templates", response_model=List[EmailTemplateResponse])
async def get_email_templates(
    current_user: dict = Depends(require_admin),
    conn: Connection = Depends(get_db_connection)
):
    """Get all email templates"""
    templates = await conn.fetch("SELECT * FROM email_templates ORDER BY template_key")
    return [dict(t) for t in templates]

@router.get("/templates/{template_key}", response_model=EmailTemplateResponse)
async def get_email_template(
    template_key: str,
    current_user: dict = Depends(require_admin),
    conn: Connection = Depends(get_db_connection)
):
    """Get specific email template"""
    template = await conn.fetchrow(
        "SELECT * FROM email_templates WHERE template_key = $1",
        template_key
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return dict(template)

# ============================================================================
# Email Queue
# ============================================================================

@router.get("/queue", response_model=List[EmailQueueResponse])
async def get_email_queue(
    status: str = None,
    limit: int = 50,
    current_user: dict = Depends(require_admin),
    conn: Connection = Depends(get_db_connection)
):
    """Get email queue"""
    if status:
        emails = await conn.fetch(
            "SELECT * FROM email_queue WHERE status = $1 ORDER BY created_at DESC LIMIT $2",
            status, limit
        )
    else:
        emails = await conn.fetch(
            "SELECT * FROM email_queue ORDER BY created_at DESC LIMIT $1",
            limit
        )
    return [dict(e) for e in emails]

@router.post("/send")
async def send_email(
    request: SendEmailRequest,
    current_user: dict = Depends(require_admin),
    conn: Connection = Depends(get_db_connection)
):
    """Send an email"""
    email_id = await email_service.send_email(
        conn,
        to_email=request.to_email,
        subject=request.subject,
        plain_body=request.body,
        html_body=request.html_body,
        cc_emails=request.cc_emails
    )
    return {"email_id": email_id, "status": "queued"}

@router.post("/send-template")
async def send_template_email(
    request: SendTemplateEmailRequest,
    current_user: dict = Depends(require_admin),
    conn: Connection = Depends(get_db_connection)
):
    """Send email using template"""
    try:
        email_id = await email_service.send_template_email(
            conn,
            to_email=request.to_email,
            template_key=request.template_key,
            variables=request.variables,
            cc_emails=request.cc_emails
        )
        return {"email_id": email_id, "status": "queued"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/test")
async def test_smtp(
    request: SMTPTestRequest,
    current_user: dict = Depends(require_admin),
    conn: Connection = Depends(get_db_connection)
):
    """Test SMTP configuration"""
    result = await email_service.test_smtp_connection(conn, request.test_email)

    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])

    return result

# ============================================================================
# Email Recipients
# ============================================================================

@router.get("/recipients", response_model=List[EmailRecipientsResponse])
async def get_email_recipients(
    current_user: dict = Depends(require_admin),
    conn: Connection = Depends(get_db_connection)
):
    """Get all email recipient configurations"""
    recipients = await conn.fetch("SELECT * FROM email_recipients ORDER BY notification_type")
    return [dict(r) for r in recipients]

@router.put("/recipients/{notification_type}")
async def update_email_recipients(
    notification_type: str,
    request: EmailRecipientsSchema,
    current_user: dict = Depends(require_admin),
    conn: Connection = Depends(get_db_connection)
):
    """Update email recipients for a notification type"""
    updated = await conn.fetchrow(
        """
        INSERT INTO email_recipients (notification_type, recipient_emails, description, is_active, updated_by)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (notification_type) DO UPDATE
        SET recipient_emails = $2, description = $3, is_active = $4, updated_by = $5
        RETURNING *
        """,
        notification_type,
        request.recipient_emails,
        request.description,
        request.is_active,
        current_user['user_id']
    )
    return dict(updated)
```

### File 5: Update `backend/app/routes/__init__.py`

```python
from app.routes import email

app.include_router(email.router, prefix="/api/v1")
```

### File 6: Update scheduler in `backend/app/main.py`

Add email queue processing:

```python
from app.services import email_service

# Add this scheduled job
scheduler.add_job(
    process_email_queue_job,
    'interval',
    minutes=5,  # Process every 5 minutes
    id='process_email_queue',
    max_instances=1
)

async def process_email_queue_job():
    """Process email queue"""
    try:
        conn = await get_db_connection()
        await email_service.process_email_queue(conn, batch_size=20)
    except Exception as e:
        logger.error(f"Email queue processing failed: {e}")
```

---

## 🎨 PART 3: FRONTEND IMPLEMENTATION

### File 1: `frontend/src/api/email.js`

```javascript
import apiClient from './client';

export const emailAPI = {
  // Templates
  getTemplates: async () => {
    const response = await apiClient.get('/email/templates');
    return response.data;
  },

  getTemplate: async (templateKey) => {
    const response = await apiClient.get(`/email/templates/${templateKey}`);
    return response.data;
  },

  // Queue
  getQueue: async (status = null, limit = 50) => {
    const params = { limit };
    if (status) params.status = status;
    const response = await apiClient.get('/email/queue', { params });
    return response.data;
  },

  // Send
  sendEmail: async (data) => {
    const response = await apiClient.post('/email/send', data);
    return response.data;
  },

  sendTemplateEmail: async (data) => {
    const response = await apiClient.post('/email/send-template', data);
    return response.data;
  },

  testSMTP: async (testEmail) => {
    const response = await apiClient.post('/email/test', { test_email: testEmail });
    return response.data;
  },

  // Recipients
  getRecipients: async () => {
    const response = await apiClient.get('/email/recipients');
    return response.data;
  },

  updateRecipients: async (notificationType, data) => {
    const response = await apiClient.put(`/email/recipients/${notificationType}`, data);
    return response.data;
  }
};
```

### File 2: `frontend/src/pages/EmailManagementPage.jsx`

```javascript
import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Tabs,
  Tab,
  Typography,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Alert
} from '@mui/material';
import { Send as SendIcon, Email as EmailIcon } from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { emailAPI } from '../api/email';

function EmailManagementPage() {
  const { enqueueSnackbar } = useSnackbar();
  const [currentTab, setCurrentTab] = useState(0);
  const [loading, setLoading] = useState(false);

  // Test dialog
  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [testEmail, setTestEmail] = useState('');
  const [testing, setTesting] = useState(false);

  // Email queue
  const [emailQueue, setEmailQueue] = useState([]);

  // Recipients
  const [recipients, setRecipients] = useState([]);
  const [editingRecipient, setEditingRecipient] = useState(null);

  useEffect(() => {
    if (currentTab === 0) loadQueue();
    if (currentTab === 1) loadRecipients();
  }, [currentTab]);

  const loadQueue = async () => {
    try {
      setLoading(true);
      const data = await emailAPI.getQueue();
      setEmailQueue(data);
      setLoading(false);
    } catch (error) {
      enqueueSnackbar('Failed to load email queue', { variant: 'error' });
      setLoading(false);
    }
  };

  const loadRecipients = async () => {
    try {
      setLoading(true);
      const data = await emailAPI.getRecipients();
      setRecipients(data);
      setLoading(false);
    } catch (error) {
      enqueueSnackbar('Failed to load recipients', { variant: 'error' });
      setLoading(false);
    }
  };

  const handleTestSMTP = async () => {
    try {
      setTesting(true);
      await emailAPI.testSMTP(testEmail);
      enqueueSnackbar(`Test email sent to ${testEmail}`, { variant: 'success' });
      setTestDialogOpen(false);
      setTestEmail('');
      setTesting(false);
    } catch (error) {
      enqueueSnackbar(error.response?.data?.detail || 'Test email failed', { variant: 'error' });
      setTesting(false);
    }
  };

  const handleUpdateRecipients = async (notificationType, emails) => {
    try {
      await emailAPI.updateRecipients(notificationType, {
        notification_type: notificationType,
        recipient_emails: emails.split(',').map(e => e.trim()).filter(e => e),
        is_active: true
      });
      enqueueSnackbar('Recipients updated', { variant: 'success' });
      loadRecipients();
      setEditingRecipient(null);
    } catch (error) {
      enqueueSnackbar('Failed to update recipients', { variant: 'error' });
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'sent': return 'success';
      case 'failed': return 'error';
      case 'pending': return 'warning';
      case 'sending': return 'info';
      default: return 'default';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4">Email Management</Typography>
          <Button
            variant="contained"
            startIcon={<SendIcon />}
            onClick={() => setTestDialogOpen(true)}
          >
            Test SMTP
          </Button>
        </Box>

        <Tabs value={currentTab} onChange={(e, v) => setCurrentTab(v)} sx={{ mb: 3 }}>
          <Tab label="Email Queue" />
          <Tab label="Recipients" />
          <Tab label="Templates" />
        </Tabs>

        {/* Email Queue Tab */}
        {currentTab === 0 && (
          <Box>
            <Typography variant="h6" gutterBottom>Recent Emails</Typography>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>To</TableCell>
                  <TableCell>Subject</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Attempts</TableCell>
                  <TableCell>Created</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {emailQueue.map(email => (
                  <TableRow key={email.id}>
                    <TableCell>{email.to_email}</TableCell>
                    <TableCell>{email.subject}</TableCell>
                    <TableCell>
                      <Chip
                        label={email.status}
                        color={getStatusColor(email.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{email.attempts} / {email.max_attempts}</TableCell>
                    <TableCell>{new Date(email.created_at).toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        )}

        {/* Recipients Tab */}
        {currentTab === 1 && (
          <Box>
            <Typography variant="h6" gutterBottom>Notification Recipients</Typography>
            <Alert severity="info" sx={{ mb: 2 }}>
              Enter comma-separated email addresses for each notification type
            </Alert>
            <Grid container spacing={3}>
              {recipients.map(recipient => (
                <Grid item xs={12} key={recipient.notification_type}>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      {recipient.notification_type.replace(/_/g, ' ').toUpperCase()}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {recipient.description}
                    </Typography>
                    <TextField
                      fullWidth
                      size="small"
                      label="Email addresses (comma-separated)"
                      defaultValue={recipient.recipient_emails.join(', ')}
                      onBlur={(e) => handleUpdateRecipients(recipient.notification_type, e.target.value)}
                      placeholder="email1@example.com, email2@example.com"
                    />
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </Box>
        )}

        {/* Templates Tab */}
        {currentTab === 2 && (
          <Box>
            <Typography variant="h6" gutterBottom>Email Templates</Typography>
            <Alert severity="info">
              Email templates are managed in the database. Contact your administrator to modify templates.
            </Alert>
          </Box>
        )}
      </Paper>

      {/* Test SMTP Dialog */}
      <Dialog open={testDialogOpen} onClose={() => setTestDialogOpen(false)}>
        <DialogTitle>Test SMTP Configuration</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Test Email Address"
            type="email"
            value={testEmail}
            onChange={(e) => setTestEmail(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleTestSMTP}
            disabled={!testEmail || testing}
            variant="contained"
          >
            {testing ? 'Sending...' : 'Send Test Email'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default EmailManagementPage;
```

### File 3: Add route in `frontend/src/App.jsx`

```javascript
import EmailManagementPage from './pages/EmailManagementPage';

<Route path="/communication/smtp" element={<EmailManagementPage />} />
```

---

## 🧪 TESTING

1. **Configure SMTP in Settings page:**
   - Go to Settings → Email tab
   - Enter SMTP details (use Gmail for testing)
   - Save

2. **Test SMTP:**
   - Go to Email Management page
   - Click "Test SMTP"
   - Enter your email
   - Check inbox for test email

3. **Configure Recipients:**
   - Go to Recipients tab
   - Add email addresses for low stock alerts
   - Save

4. **Trigger notification:**
   - Create a critical ticket
   - Check if email is queued
   - Wait 5 minutes for processing
   - Verify email received

---

## ✅ VERIFICATION CHECKLIST

- [ ] Database migration successful
- [ ] Email templates created
- [ ] Can send test email
- [ ] Email queue processes automatically
- [ ] Recipients configuration works
- [ ] Low stock emails sent
- [ ] Ticket notification emails sent

---

## 🎯 SUCCESS CRITERIA

Complete when:
1. ✅ Test email sent successfully
2. ✅ Recipients configured
3. ✅ Queue processing working
4. ✅ Integration with notifications tested

**READY FOR HANDOVER #4: Webhook System**
