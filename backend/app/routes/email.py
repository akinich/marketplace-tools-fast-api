"""
Email API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.database import get_db
from app.auth.dependencies import require_admin
from app.schemas.auth import CurrentUser
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
    current_user: CurrentUser = Depends(require_admin)
):
    """Get all email templates"""
    pool = get_db()
    async with pool.acquire() as conn:
        templates = await conn.fetch("SELECT * FROM email_templates ORDER BY template_key")
        return [dict(t) for t in templates]

@router.get("/templates/{template_key}", response_model=EmailTemplateResponse)
async def get_email_template(
    template_key: str,
    current_user: CurrentUser = Depends(require_admin)
):
    """Get specific email template"""
    pool = get_db()
    async with pool.acquire() as conn:
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
    current_user: CurrentUser = Depends(require_admin)
):
    """Get email queue"""
    pool = get_db()
    async with pool.acquire() as conn:
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
    current_user: CurrentUser = Depends(require_admin)
):
    """Send an email"""
    pool = get_db()
    async with pool.acquire() as conn:
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
    current_user: CurrentUser = Depends(require_admin)
):
    """Send email using template"""
    pool = get_db()
    async with pool.acquire() as conn:
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
    current_user: CurrentUser = Depends(require_admin)
):
    """Test SMTP configuration"""
    pool = get_db()
    async with pool.acquire() as conn:
        result = await email_service.test_smtp_connection(conn, request.test_email)

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])

        return result

# ============================================================================
# Email Recipients
# ============================================================================

@router.get("/recipients", response_model=List[EmailRecipientsResponse])
async def get_email_recipients(
    current_user: CurrentUser = Depends(require_admin)
):
    """Get all email recipient configurations"""
    pool = get_db()
    async with pool.acquire() as conn:
        recipients = await conn.fetch("SELECT * FROM email_recipients ORDER BY notification_type")
        return [dict(r) for r in recipients]

@router.put("/recipients/{notification_type}")
async def update_email_recipients(
    notification_type: str,
    request: EmailRecipientsSchema,
    current_user: CurrentUser = Depends(require_admin)
):
    """Update email recipients for a notification type"""
    pool = get_db()
    async with pool.acquire() as conn:
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
            current_user.id
        )
        return dict(updated)
