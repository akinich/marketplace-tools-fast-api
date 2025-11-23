# Email / SMTP Service - Implementation Guide

## Overview

The Email/SMTP Service provides a robust, multi-provider email delivery system for the Farm Management application. It supports both traditional SMTP and modern API-based email providers, with features including email templates, queue management, and recipient tracking.

**Version:** 1.0.0
**Status:** ✅ Production Ready
**Module Key:** `communication/smtp`

---

## Table of Contents

1. [Architecture](#architecture)
2. [Supported Providers](#supported-providers)
3. [Database Schema](#database-schema)
4. [Configuration](#configuration)
5. [Email Templates](#email-templates)
6. [Email Queue System](#email-queue-system)
7. [API Endpoints](#api-endpoints)
8. [Setup Guide](#setup-guide)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)

---

## Architecture

### Multi-Provider Design

The email service uses a **provider-based architecture** that allows switching between different email delivery methods:

```
┌─────────────────────────────────────────────┐
│         Email Service (email_service.py)    │
├─────────────────────────────────────────────┤
│  Provider Router (based on email.provider)  │
├──────────┬──────────┬──────────┬───────────┤
│   SMTP   │ SendGrid │  Resend  │  Brevo    │
│  (Port   │   API    │   API    │   API     │
│ 25/465/  │          │          │           │
│   587)   │          │          │  Mailgun  │
└──────────┴──────────┴──────────┴───────────┘
```

### Key Components

1. **Email Service** (`backend/app/services/email_service.py`)
   - Provider routing logic
   - Template rendering with Jinja2
   - Queue processing
   - Error handling and retry logic

2. **Email Routes** (`backend/app/routes/email.py`)
   - REST API endpoints
   - Authentication and authorization
   - Request validation

3. **Email Models** (`backend/app/models/email.py`)
   - Pydantic schemas for validation
   - Type safety for email operations

4. **Background Scheduler** (`backend/app/scheduler.py`)
   - Queue processing every 5 minutes
   - Automatic retry on failure

5. **Frontend UI** (`frontend/src/pages/EmailManagementPage.jsx`)
   - Template management
   - Queue monitoring
   - Recipient configuration
   - Test email functionality

---

## Supported Providers

### 1. SMTP (Traditional Email Servers)

**Use Case:** Self-hosted servers, Railway, VPS
**Limitations:** Blocked on Render (ports 25, 465, 587)

**Configuration:**
- `email.smtp_host` - SMTP server hostname
- `email.smtp_port` - Port (25, 465, 587)
- `email.smtp_user` - SMTP username
- `email.smtp_password` - SMTP password
- `email.smtp_use_tls` - TLS/SSL toggle

**Port Configuration:**
- **Port 465:** SSL/TLS (encrypted from start)
- **Port 587:** STARTTLS (starts unencrypted, upgrades to TLS)
- **Port 25:** Plain SMTP (not recommended)

### 2. SendGrid

**Free Tier:** 100 emails/day (forever)
**Trial:** 60 days with higher limits
**Website:** https://sendgrid.com

**Configuration:**
- `email.sendgrid_api_key` - SendGrid API key (starts with `SG.`)

**Permissions Required:** "Mail Send" or "Full Access"

**Pros:**
- Very reliable delivery
- Good documentation
- Generous free tier

**Cons:**
- Requires credit card after trial

### 3. Resend

**Free Tier:** 100 emails/day, 3,000/month
**Website:** https://resend.com

**Configuration:**
- `email.resend_api_key` - Resend API key (starts with `re_`)

**Pros:**
- Modern API design
- No credit card required
- Developer-friendly

**Cons:**
- Newer service (less proven)
- Lower free tier than Brevo

### 4. Brevo (formerly Sendinblue)

**Free Tier:** 300 emails/day (BEST!)
**Website:** https://brevo.com

**Configuration:**
- `email.brevo_api_key` - Brevo API key

**Pros:**
- Highest free tier (300/day)
- No credit card required
- Includes SMS and marketing tools
- Proven service

**Recommended Choice:** ⭐ **Best for small-medium farms**

### 5. Mailgun

**Free Tier:** 5,000 emails/3 months trial
**Website:** https://mailgun.com

**Configuration:**
- `email.mailgun_api_key` - Mailgun API key
- `email.mailgun_domain` - Verified domain

**Pros:**
- Higher initial allowance
- Very powerful API

**Cons:**
- Requires domain verification
- Trial ends after 3 months
- More complex setup

---

## Database Schema

### Tables Created (Migration 009_smtp_email.sql)

#### 1. `email_templates`

Stores reusable email templates with Jinja2 variable substitution.

```sql
CREATE TABLE email_templates (
    id SERIAL PRIMARY KEY,
    template_key VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    html_body TEXT NOT NULL,
    plain_body TEXT NOT NULL,
    variables JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Default Templates:**
- `welcome` - New user welcome email
- `ticket_created` - Support ticket confirmation
- `low_stock_alert` - Inventory alerts

#### 2. `email_queue`

Queue for scheduled/pending email delivery.

```sql
CREATE TABLE email_queue (
    id SERIAL PRIMARY KEY,
    to_email VARCHAR(255) NOT NULL,
    cc_emails JSONB DEFAULT '[]'::jsonb,
    bcc_emails JSONB DEFAULT '[]'::jsonb,
    subject VARCHAR(500) NOT NULL,
    html_body TEXT,
    plain_body TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    error_message TEXT,
    scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Status Values:**
- `pending` - Waiting to be sent
- `sent` - Successfully delivered
- `failed` - Permanently failed (max attempts reached)
- `retrying` - Failed but will retry

**Priority:** 1 (highest) to 10 (lowest)

#### 3. `email_recipients`

Manages recipient lists for different notification types.

```sql
CREATE TABLE email_recipients (
    id SERIAL PRIMARY KEY,
    notification_type VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(notification_type, email)
);
```

**Notification Types:**
- `low_stock` - Inventory alerts
- `new_ticket` - Support tickets
- `system_alerts` - Critical system notifications

#### 4. `email_send_log`

Audit trail for all sent emails.

```sql
CREATE TABLE email_send_log (
    id SERIAL PRIMARY KEY,
    queue_id INTEGER REFERENCES email_queue(id),
    to_email VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL,
    provider VARCHAR(50),
    error_message TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Settings (Migration 010_email_provider_settings.sql)

All email configuration is stored in `system_settings`:

| Setting Key | Type | Description |
|-------------|------|-------------|
| `email.provider` | string | Active provider (smtp, sendgrid, resend, brevo, mailgun) |
| `email.from_email` | string | Sender email address |
| `email.from_name` | string | Sender display name |
| `email.sendgrid_api_key` | string | SendGrid API key |
| `email.resend_api_key` | string | Resend API key |
| `email.brevo_api_key` | string | Brevo API key |
| `email.mailgun_api_key` | string | Mailgun API key |
| `email.mailgun_domain` | string | Mailgun verified domain |
| `email.smtp_host` | string | SMTP server hostname |
| `email.smtp_port` | integer | SMTP port (25, 465, 587) |
| `email.smtp_user` | string | SMTP username |
| `email.smtp_password` | string | SMTP password |
| `email.smtp_use_tls` | boolean | Enable TLS/SSL |

---

## Configuration

### Step 1: Run SQL Migrations

```bash
# In Supabase SQL Editor or psql
\i backend/migrations/009_smtp_email.sql
\i backend/migrations/010_email_provider_settings.sql
```

### Step 2: Configure via Settings UI

1. Navigate to **Settings → Email / SMTP**
2. Select your **Email Provider** from dropdown:
   - SMTP (for Railway, VPS)
   - SendGrid (100/day free)
   - Resend (100/day free)
   - Brevo (300/day free - Recommended!)
   - Mailgun (5000/3mo trial)

3. Enter provider-specific credentials:
   - **For API providers:** Enter API key
   - **For SMTP:** Enter host, port, username, password

4. Set **From Email** (e.g., `noreply@yourfarm.com`)
5. Set **From Name** (e.g., `Farm Management System`)
6. Click **Save Changes**

### Step 3: Test Configuration

1. Go to **Communication → Email Management**
2. Click **Test Email** tab
3. Enter your test email address
4. Click **Send Test Email**
5. Check your inbox (and spam folder!)

---

## Email Templates

### Template Structure

Templates use **Jinja2** syntax for variable substitution:

```html
<!-- HTML Body -->
<h1>Welcome {{ user_name }}!</h1>
<p>Your account has been created at {{ farm_name }}.</p>

<!-- Plain Text Body -->
Welcome {{ user_name }}!
Your account has been created at {{ farm_name }}.
```

### Available Variables

Templates define their own variables in the `variables` JSONB field:

**Welcome Template:**
- `user_name` - New user's name
- `farm_name` - Farm organization name
- `login_url` - Link to login page

**Ticket Created:**
- `ticket_id` - Support ticket number
- `ticket_subject` - Ticket subject
- `customer_name` - Customer name

**Low Stock Alert:**
- `product_name` - Product running low
- `current_stock` - Current quantity
- `threshold` - Reorder threshold

### Managing Templates

**Via UI:**
1. Go to **Communication → Email Management**
2. Click **Templates** tab
3. Edit template subject, HTML body, plain text body
4. Templates auto-render on save

**Via Database:**
```sql
UPDATE email_templates
SET subject = 'New subject',
    html_body = '<h1>New HTML</h1>',
    plain_body = 'New plain text'
WHERE template_key = 'welcome';
```

### Creating New Templates

```sql
INSERT INTO email_templates (
    template_key, name, subject, html_body, plain_body, variables
) VALUES (
    'password_reset',
    'Password Reset',
    'Reset your password - {{ farm_name }}',
    '<h1>Password Reset</h1><p>Click here: {{ reset_link }}</p>',
    'Password Reset\n\nClick here: {{ reset_link }}',
    '["farm_name", "reset_link"]'::jsonb
);
```

---

## Email Queue System

### How It Works

1. **Email Queuing:** Emails are added to `email_queue` table
2. **Background Processing:** APScheduler runs `process_email_queue()` every 5 minutes
3. **Batch Processing:** Processes up to 20 pending emails per run
4. **Retry Logic:** Failed emails retry up to 3 times (configurable)
5. **Logging:** All attempts logged to `email_send_log`

### Queue Processing Schedule

```python
# In backend/app/scheduler.py
scheduler.add_job(
    process_email_queue,
    trigger=IntervalTrigger(minutes=5),
    id="process_email_queue",
    name="Process email queue",
)
```

**Runs:** Every 5 minutes
**Batch Size:** 20 emails per run
**Priority Order:** Priority 1 (high) → 10 (low), then oldest first

### Manually Queue an Email

**Via API:**
```bash
POST /api/v1/email/queue
{
  "to_email": "customer@example.com",
  "subject": "Your order is ready",
  "plain_body": "Your order #123 is ready for pickup.",
  "html_body": "<p>Your order #123 is ready for pickup.</p>",
  "priority": 5
}
```

**Via Database:**
```sql
INSERT INTO email_queue (to_email, subject, plain_body, html_body, priority)
VALUES (
    'customer@example.com',
    'Your order is ready',
    'Your order #123 is ready for pickup.',
    '<p>Your order #123 is ready for pickup.</p>',
    5
);
```

### Monitoring Queue Status

**Via UI:**
1. Go to **Communication → Email Management**
2. View **Email Queue** tab
3. See pending, sent, failed emails

**Via Database:**
```sql
-- Queue summary
SELECT status, COUNT(*)
FROM email_queue
GROUP BY status;

-- Recent failures
SELECT * FROM email_queue
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 10;

-- Pending emails
SELECT * FROM email_queue
WHERE status = 'pending'
ORDER BY priority ASC, created_at ASC;
```

---

## API Endpoints

All endpoints require **admin authentication** (`require_admin` dependency).

### 1. Test Email Connection

**Endpoint:** `POST /api/v1/email/test`

**Request:**
```json
{
  "test_email": "admin@example.com"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Test email sent successfully to admin@example.com"
}
```

**Response (Error):**
```json
{
  "success": false,
  "message": "SendGrid API error: 401 - Unauthorized"
}
```

### 2. Queue Email

**Endpoint:** `POST /api/v1/email/queue`

**Request:**
```json
{
  "to_email": "customer@example.com",
  "cc_emails": ["manager@example.com"],
  "subject": "Order Confirmation",
  "plain_body": "Your order has been confirmed.",
  "html_body": "<h1>Order Confirmed</h1><p>Thank you!</p>",
  "priority": 3
}
```

**Response:**
```json
{
  "id": 42,
  "status": "pending",
  "message": "Email queued successfully"
}
```

### 3. Send from Template

**Endpoint:** `POST /api/v1/email/send-template`

**Request:**
```json
{
  "template_key": "welcome",
  "to_email": "newuser@example.com",
  "variables": {
    "user_name": "John Doe",
    "farm_name": "Green Acres Farm",
    "login_url": "https://farm.example.com/login"
  },
  "priority": 5
}
```

**Response:**
```json
{
  "id": 43,
  "status": "pending",
  "message": "Email queued from template 'welcome'"
}
```

### 4. Get Templates

**Endpoint:** `GET /api/v1/email/templates`

**Response:**
```json
[
  {
    "id": 1,
    "template_key": "welcome",
    "name": "Welcome Email",
    "subject": "Welcome to {{ farm_name }}!",
    "variables": ["user_name", "farm_name", "login_url"],
    "is_active": true
  }
]
```

### 5. Get Email Queue

**Endpoint:** `GET /api/v1/email/queue?limit=50`

**Response:**
```json
[
  {
    "id": 42,
    "to_email": "customer@example.com",
    "subject": "Order Confirmation",
    "status": "pending",
    "priority": 3,
    "attempts": 0,
    "created_at": "2025-11-23T12:00:00Z"
  }
]
```

### 6. Get Recipients

**Endpoint:** `GET /api/v1/email/recipients`

**Response:**
```json
[
  {
    "id": 1,
    "notification_type": "low_stock",
    "email": "manager@farm.com",
    "name": "Farm Manager",
    "is_active": true
  }
]
```

### 7. Add Recipient

**Endpoint:** `POST /api/v1/email/recipients`

**Request:**
```json
{
  "notification_type": "low_stock",
  "email": "inventory@farm.com",
  "name": "Inventory Manager"
}
```

---

## Setup Guide

### For SendGrid (Recommended for Testing)

1. **Sign up:** https://sendgrid.com
2. **Create API Key:**
   - Settings → API Keys → Create API Key
   - Name: "Farm Management System"
   - Permissions: **Full Access** (or "Mail Send")
   - Copy the key (starts with `SG.`)

3. **Configure in UI:**
   - Settings → Email / SMTP
   - Provider: **SendGrid**
   - Paste API key
   - Set From Email and From Name
   - Save Changes

4. **Test:** Send test email from Email Management page

### For Brevo (Best Free Tier)

1. **Sign up:** https://brevo.com
2. **Get API Key:**
   - Settings → SMTP & API → API Keys → Generate
   - Copy the API key

3. **Configure in UI:**
   - Settings → Email / SMTP
   - Provider: **Brevo**
   - Paste API key
   - Set From Email and From Name
   - Save Changes

### For SMTP (Railway/VPS Only)

**Example: Zoho Mail**

1. **Enable IMAP/SMTP in Zoho:**
   - Settings → Mail Accounts → IMAP Access → Enable

2. **Generate App Password:**
   - Settings → Security → App Passwords → Generate

3. **Configure in UI:**
   - Settings → Email / SMTP
   - Provider: **SMTP**
   - SMTP Host: `smtp.zoho.com`
   - SMTP Port: `587`
   - SMTP User: `your-email@zoho.com`
   - SMTP Password: `[app password]`
   - Use TLS: **Yes**
   - Set From Email and From Name
   - Save Changes

**Note:** SMTP will NOT work on Render due to port blocking!

---

## Testing

### Test Checklist

- [ ] **Configuration Test:** Send test email from Settings UI
- [ ] **Template Test:** Queue email from template
- [ ] **Queue Processing:** Wait 5 minutes, verify email sent
- [ ] **Retry Logic:** Simulate failure, verify retry
- [ ] **Multiple Recipients:** Test CC/BCC
- [ ] **Priority:** Queue high/low priority, verify order
- [ ] **Error Handling:** Test with invalid API key

### Test Email Endpoint

```bash
curl -X POST "https://your-api.com/api/v1/email/test" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"test_email": "your-email@example.com"}'
```

### Check Queue Status

```sql
SELECT
    status,
    COUNT(*) as count,
    MIN(created_at) as oldest,
    MAX(created_at) as newest
FROM email_queue
GROUP BY status;
```

### View Recent Logs

```sql
SELECT
    to_email,
    subject,
    status,
    provider,
    error_message,
    sent_at
FROM email_send_log
ORDER BY sent_at DESC
LIMIT 10;
```

---

## Troubleshooting

### SendGrid: 401 Unauthorized

**Problem:** API key is invalid or lacks permissions.

**Solutions:**
1. Verify API key starts with `SG.` and is 69 characters
2. Check key has "Mail Send" or "Full Access" permission
3. Create new API key if original was lost
4. Ensure no spaces/quotes when copying key

### SMTP: Connection Timeout

**Problem:** SMTP ports (25, 465, 587) blocked by hosting platform.

**Solutions:**
1. **If on Render:** Use API provider (SendGrid, Brevo, Resend)
2. **If on Railway/VPS:** Check firewall rules
3. **Try different port:** 587 instead of 465
4. **Verify credentials:** Test with email client first

### Emails Not Sending (Queue Stuck)

**Problem:** Background scheduler not running or errors in processing.

**Solutions:**
1. Check backend logs for scheduler errors
2. Verify scheduler is registered in `main.py`
3. Check database connection pool
4. Manually trigger: Call `process_email_queue()` in Python shell
5. Check `email_queue.status` for failed emails

### Template Variables Not Rendering

**Problem:** Jinja2 template syntax errors or missing variables.

**Solutions:**
1. Verify variable names match exactly (case-sensitive)
2. Use `{{ variable }}` not `{ variable }`
3. Check template in database has correct syntax
4. Pass all required variables when calling `send_from_template()`

### Emails Going to Spam

**Problem:** Poor sender reputation or missing authentication.

**Solutions:**
1. **Use API provider** (SendGrid, Brevo) - better deliverability
2. **Verify sender domain** with SPF/DKIM/DMARC
3. **Don't use generic domains** like Gmail for sending
4. **Include unsubscribe link** in email footer
5. **Warm up IP** if using SMTP - start with low volume

### High Priority Emails Not Sending First

**Problem:** Queue processing not respecting priority.

**Check:**
```sql
SELECT * FROM email_queue
WHERE status = 'pending'
ORDER BY priority ASC, created_at ASC
LIMIT 10;
```

If high priority (1-3) emails are oldest, scheduler might be down.

### Provider Switch Not Working

**Problem:** Changed provider in UI but still using old one.

**Solutions:**
1. Verify setting saved: Check `system_settings` table
2. Restart backend to clear any cached settings
3. Check logs for provider being used
4. Ensure new provider credentials are valid

---

## Best Practices

### 1. Provider Selection

- **Development/Testing:** SendGrid (easy setup, good docs)
- **Production (< 300/day):** Brevo (best free tier)
- **Production (> 300/day):** Paid plan on any provider
- **Self-hosted:** SMTP on Railway/VPS (not Render)

### 2. Email Content

- **Always include plain text version** - required by some email clients
- **Keep HTML simple** - avoid complex CSS, use inline styles
- **Test on multiple clients** - Gmail, Outlook, Apple Mail
- **Include unsubscribe link** - legal requirement in many countries
- **Use clear subject lines** - avoid spam trigger words

### 3. Queue Management

- **Use priorities wisely:**
  - 1-3: Critical (password resets, alerts)
  - 4-6: Normal (confirmations, receipts)
  - 7-10: Low (newsletters, promotions)

- **Set appropriate retry limits:**
  - Transactional emails: 3 attempts
  - Marketing emails: 1 attempt (to avoid spam)

- **Monitor queue regularly:**
  - Alert if queue size > 100
  - Review failed emails weekly

### 4. Security

- **Never log email content** - may contain sensitive data
- **Store API keys encrypted** - use environment variables in production
- **Limit admin access** - only admins can send emails
- **Validate email addresses** - use EmailStr type from Pydantic
- **Rate limit API endpoints** - prevent abuse

### 5. Performance

- **Batch size:** 20 emails per 5-minute run = 240/hour (well under limits)
- **For higher volume:** Decrease interval to 1 minute or increase batch size
- **Use templates:** Faster than generating HTML in code
- **Monitor provider quotas:** Track daily/monthly usage

---

## File Reference

### Backend Files

```
backend/
├── app/
│   ├── models/
│   │   └── email.py                 # Pydantic schemas
│   ├── routes/
│   │   └── email.py                 # API endpoints
│   ├── services/
│   │   └── email_service.py         # Core email logic
│   ├── scheduler.py                 # Background job scheduler
│   └── main.py                      # App initialization
├── migrations/
│   ├── 009_smtp_email.sql          # Tables creation
│   └── 010_email_provider_settings.sql  # Settings
└── requirements.txt                 # Dependencies (aiosmtplib, jinja2)
```

### Frontend Files

```
frontend/
└── src/
    ├── api/
    │   └── email.js                 # Email API client
    ├── pages/
    │   ├── EmailManagementPage.jsx  # Email management UI
    │   └── SettingsPage.jsx         # Provider configuration
    └── App.jsx                      # Route: /communication/smtp
```

### Documentation Files

```
docs/
├── framework/
│   └── communication/
│       ├── email-smtp.md            # This file
│       └── README.md                # Communication module overview
└── EMAIL_SETUP_GUIDE.md             # Quick setup guide (root)
```

---

## Version History

### v1.0.0 (2025-11-23) - Initial Release

**Features:**
- Multi-provider support (SMTP, SendGrid, Resend, Brevo, Mailgun)
- Email templates with Jinja2 rendering
- Email queue with priority and retry logic
- Recipient management
- Background processing every 5 minutes
- Complete REST API
- Frontend management UI
- Settings UI with provider dropdown
- Comprehensive testing and documentation

**Migrations:**
- 009_smtp_email.sql - Database tables
- 010_email_provider_settings.sql - Provider settings

**Testing:**
- ✅ SendGrid verified working
- ✅ Settings UI provider dropdown functional
- ✅ Test email delivery successful
- ✅ Queue processing validated

---

## Support & Contribution

### Getting Help

1. Check this documentation
2. Review `EMAIL_SETUP_GUIDE.md` in project root
3. Check backend logs for detailed errors
4. Test with `curl` to isolate frontend vs backend issues

### Known Limitations

1. **Render SMTP Blocking:** Ports 25, 465, 587 blocked - use API providers
2. **Free Tier Limits:** Max 300/day (Brevo) - monitor usage
3. **No HTML Email Builder:** Templates edited as raw HTML
4. **No Email Analytics:** No open/click tracking (add via provider dashboard)
5. **No Attachment Support:** Not implemented (future enhancement)

### Future Enhancements

- [ ] Attachment support
- [ ] HTML email template builder
- [ ] Email analytics dashboard
- [ ] Scheduled sending (specific date/time)
- [ ] A/B testing for email templates
- [ ] Email preview before sending
- [ ] Webhook callbacks for delivery status
- [ ] Multi-language template support

---

## License & Credits

**Part of:** Farm Management System
**Module:** Communication / Email & SMTP
**License:** [Your License]
**Author:** Farm2 Development Team
**Last Updated:** 2025-11-23

---

**End of Documentation**
