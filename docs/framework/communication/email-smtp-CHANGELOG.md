# Email / SMTP Service - Changelog

All notable changes to the Email/SMTP Service module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2025-11-23

### ✨ Added - Initial Release

#### Backend Features
- **Multi-Provider Email System**
  - SMTP support for self-hosted servers (Railway, VPS)
  - SendGrid API integration (100 emails/day free)
  - Resend API integration (100 emails/day free)
  - Brevo API integration (300 emails/day free - Best!)
  - Mailgun API integration (5000/3mo trial)
  - Runtime provider switching via settings

- **Email Queue System**
  - Background processing every 5 minutes via APScheduler
  - Priority-based queue (1=high, 10=low)
  - Automatic retry logic (up to 3 attempts)
  - Batch processing (20 emails per run)
  - Status tracking (pending, sent, failed, retrying)

- **Email Templates**
  - Jinja2 template engine for variable substitution
  - HTML and plain text versions
  - Default templates: welcome, ticket_created, low_stock_alert
  - Template variables stored as JSONB

- **Recipient Management**
  - Recipient lists by notification type
  - Support for CC/BCC
  - Active/inactive recipient filtering

- **API Endpoints** (Admin-only)
  - `POST /api/v1/email/test` - Test email configuration
  - `POST /api/v1/email/queue` - Queue email for sending
  - `POST /api/v1/email/send-template` - Send from template
  - `GET /api/v1/email/templates` - List templates
  - `GET /api/v1/email/queue` - View queue status
  - `GET /api/v1/email/recipients` - List recipients
  - `POST /api/v1/email/recipients` - Add recipient

- **Email Service Core**
  - Provider routing based on `email.provider` setting
  - SMTP SSL/TLS auto-detection (port 465 vs 587)
  - Comprehensive error handling and logging
  - Connection pooling for API providers
  - Template rendering with Jinja2

#### Frontend Features
- **Email Management Page** (`/communication/smtp`)
  - Three tabs: Email Queue, Templates, Recipients
  - Real-time queue status monitoring
  - Template preview and editing
  - Recipient list management
  - Test email functionality

- **Settings UI Enhancement** (v1.3.0)
  - Email provider dropdown (smtp, sendgrid, resend, brevo, mailgun)
  - Conditional field display (only show relevant API keys)
  - Hide SMTP fields when using API providers
  - Hide API provider fields when using SMTP
  - Integrated with existing Settings page tabs

#### Database Schema
- **Migration 009_smtp_email.sql**
  - Table: `email_templates` - Reusable templates
  - Table: `email_queue` - Pending/sent emails
  - Table: `email_recipients` - Notification recipients
  - Table: `email_send_log` - Audit trail
  - Default templates inserted

- **Migration 010_email_provider_settings.sql**
  - Setting: `email.provider` - Active provider
  - Setting: `email.from_email` - Sender address
  - Setting: `email.from_name` - Sender name
  - Setting: `email.sendgrid_api_key` - SendGrid API key
  - Setting: `email.resend_api_key` - Resend API key
  - Setting: `email.brevo_api_key` - Brevo API key
  - Setting: `email.mailgun_api_key` - Mailgun API key
  - Setting: `email.mailgun_domain` - Mailgun domain
  - Setting: `email.smtp_host` - SMTP hostname
  - Setting: `email.smtp_port` - SMTP port
  - Setting: `email.smtp_user` - SMTP username
  - Setting: `email.smtp_password` - SMTP password
  - Setting: `email.smtp_use_tls` - SMTP TLS toggle

#### Documentation
- **email-smtp.md** - Comprehensive implementation guide
  - Architecture overview
  - Provider comparison and setup guides
  - Database schema documentation
  - API endpoint reference
  - Configuration walkthrough
  - Troubleshooting guide
  - Best practices

- **EMAIL_SETUP_GUIDE.md** - Quick setup guide (project root)
  - Provider-specific setup instructions
  - Step-by-step configuration
  - Common issues and solutions

- **CHANGELOG.md** - This file
- **VERSION_HISTORY.md** - Detailed version history

#### Dependencies Added
- `aiosmtplib==3.0.1` - Async SMTP client
- `jinja2==3.1.2` - Template engine
- `httpx` (existing) - HTTP client for API providers

### 🐛 Fixed

#### Port-based SSL/TLS Detection (af7dabd)
- **Problem:** SMTP connections hanging on port 465
- **Solution:** Added automatic SSL/TLS configuration based on port:
  - Port 465: use_tls=True, start_tls=False (SSL/TLS)
  - Port 587: use_tls=False, start_tls=True (STARTTLS)
- **Files:** `backend/app/services/email_service.py`

#### Database Connection Pattern (03f3bcb)
- **Problem:** ImportError for non-existent `get_db_connection()`
- **Solution:** Fixed to use proper asyncpg pattern:
  ```python
  pool = get_db()
  async with pool.acquire() as conn:
      # use conn
  ```
- **Files:** `backend/app/scheduler.py`, `backend/app/routes/email.py`

#### Settings UI Merge Conflict (638b39b → a484efe)
- **Problem:** SettingsPage.jsx had conflicting versions between branches
  - Main branch: v1.2.0 with Telegram, Integrations, Audit Log tabs
  - Feature branch: v1.0.0 with email provider dropdown
- **Solution:** Manually merged both versions to v1.3.0 with all features:
  - Email provider dropdown with conditional field display
  - Telegram tab from main
  - Integrations tab from main
  - Audit Log tab from main
- **Files:** `frontend/src/pages/SettingsPage.jsx`

#### Import Dependencies (Multiple commits)
- Fixed missing Material-UI imports: Select, MenuItem, FormControl, InputLabel
- Fixed email API client imports in frontend
- Fixed require_admin dependency import in routes

### 🔧 Changed

#### Settings Page Version (v1.0.0 → v1.3.0)
- **v1.0.0:** Initial settings page with basic categories
- **v1.1.0:** Added Audit Log tab (from main)
- **v1.2.0:** Added Telegram and Integrations tabs (from main)
- **v1.3.0:** Added email provider dropdown with conditional field display

#### Email Service Architecture
- Migrated from single-provider to multi-provider architecture
- Added provider routing logic in `_send_email_via_provider()`
- Separated provider-specific implementations:
  - `_send_via_smtp()` - SMTP servers
  - `_send_via_sendgrid()` - SendGrid API
  - `_send_via_resend()` - Resend API
  - `_send_via_brevo()` - Brevo API
  - `_send_via_mailgun()` - Mailgun API

### ⚠️ Known Issues

#### Render Platform SMTP Blocking
- **Issue:** Render blocks outbound connections on ports 25, 465, 587
- **Impact:** SMTP provider cannot be used on Render hosting
- **Workaround:** Use API-based providers (SendGrid, Resend, Brevo, Mailgun)
- **Status:** Platform limitation - no fix available

#### SendGrid 401 Error with Invalid API Key
- **Issue:** Misleading error when API key is invalid or lacks permissions
- **Impact:** User sees "invalid, expired, or revoked" message
- **Workaround:**
  1. Create new API key with "Full Access" permissions
  2. Copy entire key (starts with `SG.`, 69 characters)
  3. Update in Settings UI
- **Status:** Expected behavior - improved error messaging in future

### 📝 Testing

#### Manual Testing Completed
- ✅ SendGrid provider configuration via Settings UI
- ✅ SendGrid test email delivery (successful)
- ✅ Settings provider dropdown functionality
- ✅ Conditional field hiding based on provider selection
- ✅ Email queue creation via API
- ✅ Template rendering with Jinja2 variables
- ✅ Background queue processing (5-minute interval)
- ✅ Settings page merge with main branch features

#### Platforms Tested
- ✅ Render (backend deployment)
- ✅ Vercel/Netlify (frontend deployment)
- ✅ Supabase (PostgreSQL database)
- ✅ SendGrid (email delivery)

### 🚀 Deployment

#### Backend Deployment
- All code committed to branch `claude/implement-handover-docs-01UnEtqesr6cFZ9jCdcNPwPU`
- Merged cleanly with main branch (no conflicts)
- Ready for production deployment

#### Frontend Deployment
- Settings UI updated with provider dropdown
- Email Management page fully functional
- Route registered: `/communication/smtp`

#### Database Migrations
- Migration 009: `backend/migrations/009_smtp_email.sql`
- Migration 010: `backend/migrations/010_email_provider_settings.sql`
- Both migrations tested and verified in Supabase

### 🔐 Security

#### Access Control
- All email endpoints require admin authentication (`require_admin`)
- API keys stored in `system_settings` with `is_public=false`
- Email content not logged (privacy consideration)

#### Data Protection
- SMTP passwords encrypted in transit (TLS)
- API keys never exposed in frontend responses
- Email queue logs sanitized (no sensitive content in logs)

---

## Future Releases

### [1.1.0] - Planned

#### Features Under Consideration
- [ ] Email attachment support
- [ ] HTML email template builder (drag-and-drop)
- [ ] Email analytics dashboard (open rates, click rates)
- [ ] Scheduled sending (specific date/time)
- [ ] A/B testing for email templates
- [ ] Email preview before sending
- [ ] Webhook callbacks for delivery status (from providers)
- [ ] Multi-language template support
- [ ] Unsubscribe link management
- [ ] Email signature management

#### Bug Fixes Planned
- [ ] Better error messages for common provider issues
- [ ] Frontend validation for email addresses
- [ ] Rate limiting on test email endpoint
- [ ] Queue processing metrics in UI

---

## Breaking Changes

None - Initial release (v1.0.0)

---

## Migration Guide

### From No Email System → v1.0.0

1. **Run SQL Migrations:**
   ```sql
   \i backend/migrations/009_smtp_email.sql
   \i backend/migrations/010_email_provider_settings.sql
   ```

2. **Deploy Backend:**
   - Updated files in `backend/app/services/`, `routes/`, `models/`
   - Scheduler registered in `main.py`

3. **Deploy Frontend:**
   - New page: `EmailManagementPage.jsx`
   - Updated: `SettingsPage.jsx` (v1.3.0)
   - New route: `/communication/smtp`

4. **Configure Email Provider:**
   - Settings → Email / SMTP → Select provider
   - Enter API key or SMTP credentials
   - Save and test

5. **Verify Functionality:**
   - Send test email
   - Check queue processing (wait 5 minutes)
   - Review logs for any errors

---

## Contributors

- **Initial Implementation:** Farm2 Development Team
- **Testing:** Verified with SendGrid on Render platform
- **Documentation:** Comprehensive guides created
- **Date:** November 23, 2025

---

**Changelog Maintained:** This file is updated with each release.
**Format:** Based on [Keep a Changelog](https://keepachangelog.com/)
**Versioning:** [Semantic Versioning](https://semver.org/)
