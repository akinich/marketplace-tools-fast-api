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
