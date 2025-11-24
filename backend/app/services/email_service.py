"""
Email Service - Multi-provider email sending with templates and queue

Supports 6 providers:
- SMTP (traditional SMTP servers - for Railway, VPS, etc.)
- SendGrid (100 emails/day free - Enterprise trusted)
- Resend (100 emails/day free - Modern, developer-friendly)
- Brevo (300 emails/day free - Best free tier!)
- Mailgun (5000 emails/3 months - Pay-as-you-go after)
- AWS SES (Pay-per-use - Enterprise, not implemented)
"""
import aiosmtplib
import httpx
import base64
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
    # Check if email is enabled
    email_enabled = await settings_service.get_setting(conn, 'email.smtp_enabled', False)
    if not email_enabled:
        logger.debug("Email service is disabled, skipping email processing")
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

    # Get provider
    provider = await settings_service.get_setting(conn, 'email.provider', 'smtp')

    for email in emails:
        email_id = email['id']

        try:
            # Mark as sending
            await conn.execute(
                "UPDATE email_queue SET status = 'sending', attempts = attempts + 1 WHERE id = $1",
                email_id
            )

            # Send email based on provider
            await _send_email_via_provider(
                conn,
                provider=provider,
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

            logger.info(f"Email sent successfully: {email_id} via {provider}")

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

async def test_email_connection(conn: Connection, test_email: str) -> Dict[str, Any]:
    """Test email configuration by sending a test email"""
    try:
        provider = await settings_service.get_setting(conn, 'email.provider', 'smtp')
        logger.info(f"Testing email connection using provider: {provider}, sending to {test_email}")

        await _send_email_via_provider(
            conn,
            provider=provider,
            to_email=test_email,
            subject="Email Test - Farm Management System",
            plain_body=f"This is a test email from your Farm Management System.\n\nProvider: {provider}\n\nEmail service is configured correctly!",
            html_body=f"<h2>Email Test</h2><p>This is a test email from your Farm Management System.</p><p><strong>Provider:</strong> {provider}</p><p><strong>Email service is configured correctly!</strong></p>"
        )

        logger.info(f"✅ Test email sent successfully to {test_email} via {provider}")
        return {"success": True, "message": f"Test email sent to {test_email} via {provider}"}
    except Exception as e:
        logger.error(f"❌ Email test failed: {str(e)}", exc_info=True)
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

# ============================================================================
# PROVIDER ROUTING
# ============================================================================

async def _send_email_via_provider(
    conn: Connection,
    provider: str,
    to_email: str,
    subject: str,
    plain_body: str,
    html_body: Optional[str] = None,
    cc_emails: Optional[List[str]] = None
):
    """Route email to appropriate provider"""
    provider = provider.lower()

    if provider == 'smtp':
        settings = await _get_smtp_settings(conn)
        await _send_via_smtp(settings, to_email, subject, plain_body, html_body, cc_emails)
    elif provider == 'sendgrid':
        settings = await _get_sendgrid_settings(conn)
        await _send_via_sendgrid(settings, to_email, subject, plain_body, html_body, cc_emails)
    elif provider == 'resend':
        settings = await _get_resend_settings(conn)
        await _send_via_resend(settings, to_email, subject, plain_body, html_body, cc_emails)
    elif provider == 'brevo':
        settings = await _get_brevo_settings(conn)
        await _send_via_brevo(settings, to_email, subject, plain_body, html_body, cc_emails)
    elif provider == 'mailgun':
        settings = await _get_mailgun_settings(conn)
        await _send_via_mailgun(settings, to_email, subject, plain_body, html_body, cc_emails)
    elif provider == 'aws_ses':
        settings = await _get_aws_ses_settings(conn)
        await _send_via_aws_ses(settings, to_email, subject, plain_body, html_body, cc_emails)
    else:
        raise ValueError(f"Unknown email provider: {provider}")

# ============================================================================
# SMTP PROVIDER
# ============================================================================

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

async def _send_via_smtp(
    smtp_settings: Dict[str, Any],
    to_email: str,
    subject: str,
    plain_body: str,
    html_body: Optional[str] = None,
    cc_emails: Optional[List[str]] = None
):
    """Send email via SMTP"""
    # Validate settings
    if not smtp_settings['host']:
        raise ValueError("SMTP host is not configured")
    if not smtp_settings['username']:
        raise ValueError("SMTP username is not configured")
    if not smtp_settings['password']:
        raise ValueError("SMTP password is not configured")

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

    # Determine SSL/TLS settings based on port
    port = smtp_settings['port']

    # Port 465 = SSL/TLS (implicit encryption)
    # Port 587 = STARTTLS (explicit TLS upgrade)
    if port == 465:
        use_tls = True
        start_tls = False
        logger.debug(f"Using SSL/TLS for port 465")
    elif port == 587:
        use_tls = False
        start_tls = True
        logger.debug(f"Using STARTTLS for port 587")
    else:
        use_tls = smtp_settings.get('use_tls', False)
        start_tls = not use_tls
        logger.debug(f"Port {port}: use_tls={use_tls}, start_tls={start_tls}")

    logger.debug(f"Connecting to {smtp_settings['host']}:{port} (use_tls={use_tls}, start_tls={start_tls})")

    await aiosmtplib.send(
        message,
        hostname=smtp_settings['host'],
        port=port,
        username=smtp_settings['username'],
        password=smtp_settings['password'],
        use_tls=use_tls,
        start_tls=start_tls,
        timeout=30
    )

# ============================================================================
# SENDGRID PROVIDER
# ============================================================================

async def _get_sendgrid_settings(conn: Connection) -> Dict[str, Any]:
    """Get SendGrid configuration from settings"""
    return {
        'api_key': await settings_service.get_setting(conn, 'email.sendgrid_api_key', ''),
        'from_email': await settings_service.get_setting(conn, 'email.from_email', 'noreply@farmapp.com'),
        'from_name': await settings_service.get_setting(conn, 'email.from_name', 'Farm Management System'),
    }

async def _send_via_sendgrid(
    sendgrid_settings: Dict[str, Any],
    to_email: str,
    subject: str,
    plain_body: str,
    html_body: Optional[str] = None,
    cc_emails: Optional[List[str]] = None
):
    """Send email via SendGrid API"""
    if not sendgrid_settings['api_key']:
        raise ValueError("SendGrid API key is not configured")

    # Build email payload
    payload = {
        "personalizations": [{
            "to": [{"email": to_email}],
        }],
        "from": {
            "email": sendgrid_settings['from_email'],
            "name": sendgrid_settings['from_name']
        },
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": plain_body}
        ]
    }

    if html_body:
        payload["content"].append({"type": "text/html", "value": html_body})

    if cc_emails:
        payload["personalizations"][0]["cc"] = [{"email": email} for email in cc_emails]

    # Send via SendGrid API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            json=payload,
            headers={
                "Authorization": f"Bearer {sendgrid_settings['api_key']}",
                "Content-Type": "application/json"
            },
            timeout=30
        )

        if response.status_code not in (200, 202):
            raise Exception(f"SendGrid API error: {response.status_code} - {response.text}")

    logger.debug(f"Email sent via SendGrid API to {to_email}")

# ============================================================================
# RESEND PROVIDER
# ============================================================================

async def _get_resend_settings(conn: Connection) -> Dict[str, Any]:
    """Get Resend configuration from settings"""
    return {
        'api_key': await settings_service.get_setting(conn, 'email.resend_api_key', ''),
        'from_email': await settings_service.get_setting(conn, 'email.from_email', 'noreply@farmapp.com'),
        'from_name': await settings_service.get_setting(conn, 'email.from_name', 'Farm Management System'),
    }

async def _send_via_resend(
    resend_settings: Dict[str, Any],
    to_email: str,
    subject: str,
    plain_body: str,
    html_body: Optional[str] = None,
    cc_emails: Optional[List[str]] = None
):
    """Send email via Resend API"""
    if not resend_settings['api_key']:
        raise ValueError("Resend API key is not configured")

    # Build email payload (Resend has the simplest API!)
    payload = {
        "from": f"{resend_settings['from_name']} <{resend_settings['from_email']}>",
        "to": [to_email],
        "subject": subject,
    }

    # Resend prefers HTML, fallback to text
    if html_body:
        payload["html"] = html_body
    else:
        payload["text"] = plain_body

    if cc_emails:
        payload["cc"] = cc_emails

    # Send via Resend API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.resend.com/emails",
            json=payload,
            headers={
                "Authorization": f"Bearer {resend_settings['api_key']}",
                "Content-Type": "application/json"
            },
            timeout=30
        )

        if response.status_code not in (200, 201):
            raise Exception(f"Resend API error: {response.status_code} - {response.text}")

    logger.debug(f"Email sent via Resend API to {to_email}")

# ============================================================================
# BREVO PROVIDER
# ============================================================================

async def _get_brevo_settings(conn: Connection) -> Dict[str, Any]:
    """Get Brevo configuration from settings"""
    return {
        'api_key': await settings_service.get_setting(conn, 'email.brevo_api_key', ''),
        'from_email': await settings_service.get_setting(conn, 'email.from_email', 'noreply@farmapp.com'),
        'from_name': await settings_service.get_setting(conn, 'email.from_name', 'Farm Management System'),
    }

async def _send_via_brevo(
    brevo_settings: Dict[str, Any],
    to_email: str,
    subject: str,
    plain_body: str,
    html_body: Optional[str] = None,
    cc_emails: Optional[List[str]] = None
):
    """Send email via Brevo API"""
    if not brevo_settings['api_key']:
        raise ValueError("Brevo API key is not configured")

    # Build email payload
    payload = {
        "sender": {
            "email": brevo_settings['from_email'],
            "name": brevo_settings['from_name']
        },
        "to": [{"email": to_email}],
        "subject": subject,
    }

    # Brevo prefers HTML
    if html_body:
        payload["htmlContent"] = html_body
    else:
        payload["textContent"] = plain_body

    if cc_emails:
        payload["cc"] = [{"email": email} for email in cc_emails]

    # Send via Brevo API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.brevo.com/v3/smtp/email",
            json=payload,
            headers={
                "api-key": brevo_settings['api_key'],
                "Content-Type": "application/json"
            },
            timeout=30
        )

        if response.status_code not in (200, 201):
            raise Exception(f"Brevo API error: {response.status_code} - {response.text}")

    logger.debug(f"Email sent via Brevo API to {to_email}")

# ============================================================================
# MAILGUN PROVIDER
# ============================================================================

async def _get_mailgun_settings(conn: Connection) -> Dict[str, Any]:
    """Get Mailgun configuration from settings"""
    return {
        'api_key': await settings_service.get_setting(conn, 'email.mailgun_api_key', ''),
        'domain': await settings_service.get_setting(conn, 'email.mailgun_domain', ''),
        'from_email': await settings_service.get_setting(conn, 'email.from_email', 'noreply@farmapp.com'),
        'from_name': await settings_service.get_setting(conn, 'email.from_name', 'Farm Management System'),
    }

async def _send_via_mailgun(
    mailgun_settings: Dict[str, Any],
    to_email: str,
    subject: str,
    plain_body: str,
    html_body: Optional[str] = None,
    cc_emails: Optional[List[str]] = None
):
    """Send email via Mailgun API"""
    if not mailgun_settings['api_key']:
        raise ValueError("Mailgun API key is not configured")
    if not mailgun_settings['domain']:
        raise ValueError("Mailgun domain is not configured")

    # Build email payload
    data = {
        "from": f"{mailgun_settings['from_name']} <{mailgun_settings['from_email']}>",
        "to": to_email,
        "subject": subject,
        "text": plain_body
    }

    if html_body:
        data["html"] = html_body

    if cc_emails:
        data["cc"] = ", ".join(cc_emails)

    # Send via Mailgun API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.mailgun.net/v3/{mailgun_settings['domain']}/messages",
            data=data,
            auth=("api", mailgun_settings['api_key']),
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"Mailgun API error: {response.status_code} - {response.text}")

    logger.debug(f"Email sent via Mailgun API to {to_email}")

# ============================================================================
# AWS SES PROVIDER
# ============================================================================

async def _get_aws_ses_settings(conn: Connection) -> Dict[str, Any]:
    """Get AWS SES configuration from settings"""
    return {
        'access_key': await settings_service.get_setting(conn, 'email.aws_access_key', ''),
        'secret_key': await settings_service.get_setting(conn, 'email.aws_secret_key', ''),
        'region': await settings_service.get_setting(conn, 'email.aws_region', 'us-east-1'),
        'from_email': await settings_service.get_setting(conn, 'email.from_email', 'noreply@farmapp.com'),
        'from_name': await settings_service.get_setting(conn, 'email.from_name', 'Farm Management System'),
    }

async def _send_via_aws_ses(
    aws_settings: Dict[str, Any],
    to_email: str,
    subject: str,
    plain_body: str,
    html_body: Optional[str] = None,
    cc_emails: Optional[List[str]] = None
):
    """Send email via AWS SES API"""
    if not aws_settings['access_key']:
        raise ValueError("AWS access key is not configured")
    if not aws_settings['secret_key']:
        raise ValueError("AWS secret key is not configured")

    # For now, raise not implemented (AWS SES requires more complex auth)
    raise NotImplementedError("AWS SES provider not yet implemented - use SendGrid or Mailgun")
