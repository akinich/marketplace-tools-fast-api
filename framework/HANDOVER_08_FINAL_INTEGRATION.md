# HANDOVER MESSAGE #8: Final Integration Testing & Complete Documentation

## 📋 MISSION
Perform **end-to-end integration testing** of all Communication features and Settings Management. Create comprehensive documentation for admins, users, and developers.

## 🎯 SCOPE

This handover covers:
1. **Integration Testing** - Test all features working together
2. **Admin Documentation** - How to configure and manage the system
3. **User Documentation** - How to use the features
4. **Developer Documentation** - Architecture and API docs
5. **Final Deployment** - Production deployment checklist

---

## PART 1: INTEGRATION TESTING

### Test Plan

#### 1. Settings Management Integration Tests

**Test 1.1: Settings affect SMTP**
1. Go to Settings → Email
2. Configure SMTP (use Gmail for testing)
3. Save settings
4. Go to Communication → Email (SMTP)
5. Send test email
6. Verify email received
✅ PASS / ❌ FAIL: __________

**Test 1.2: Settings affect Auth**
1. Go to Settings → Authentication
2. Change "JWT Expiry" to 60 minutes
3. Save
4. Logout and login
5. Check JWT token expiry (use jwt.io)
✅ PASS / ❌ FAIL: __________

**Test 1.3: Settings Audit Log**
1. Change any setting
2. Go to Settings → Audit Log
3. Verify change logged with user and timestamp
✅ PASS / ❌ FAIL: __________

---

#### 2. SMTP Email Integration Tests

**Test 2.1: Ticket Email Notification**
1. Configure email recipients for "tickets_all"
2. Create a critical ticket
3. Verify email sent to recipients
4. Check email queue shows "sent" status
✅ PASS / ❌ FAIL: __________

**Test 2.2: Low Stock Email Alert**
1. Configure email recipients for "low_stock"
2. Create inventory item with stock below reorder level
3. Wait for scheduled job (or trigger manually)
4. Verify low stock email received
✅ PASS / ❌ FAIL: __________

**Test 2.3: Welcome Email**
1. Create new user as admin
2. Verify welcome email sent to user
3. Check email contains temporary password
✅ PASS / ❌ FAIL: __________

**Test 2.4: Email Queue Retry**
1. Create webhook with invalid SMTP settings
2. Queue an email
3. Verify status shows "failed" after max attempts
4. Fix SMTP settings
5. Retry should not re-send (already failed)
✅ PASS / ❌ FAIL: __________

---

#### 3. Webhook Integration Tests

**Test 3.1: Ticket Created Webhook**
1. Create webhook pointing to webhook.site
2. Subscribe to "ticket.created" event
3. Create a ticket
4. Verify webhook received at webhook.site
5. Check signature is valid
✅ PASS / ❌ FAIL: __________

**Test 3.2: Webhook Retry Logic**
1. Create webhook with invalid URL
2. Create ticket (triggers webhook)
3. Check delivery log shows "retrying"
4. Wait for retry attempts
5. Verify final status is "failed" after max attempts
✅ PASS / ❌ FAIL: __________

**Test 3.3: Multiple Webhooks Same Event**
1. Create 2 webhooks for "ticket.created"
2. Create a ticket
3. Verify both webhooks received the event
✅ PASS / ❌ FAIL: __________

---

#### 4. API Key Integration Tests

**Test 4.1: API Key Authentication**
1. Create API key with scope "inventory:read"
2. Use curl to access inventory endpoint:
   ```bash
   curl -H "X-API-Key: YOUR_KEY" http://localhost:8000/api/v1/inventory
   ```
3. Verify success (200)
✅ PASS / ❌ FAIL: __________

**Test 4.2: Scope Restriction**
1. Use same API key to create ticket (needs "tickets:write")
   ```bash
   curl -H "X-API-Key: YOUR_KEY" -X POST http://localhost:8000/api/v1/tickets -d '{...}'
   ```
2. Verify 403 Forbidden
✅ PASS / ❌ FAIL: __________

**Test 4.3: API Key Revocation**
1. Revoke the API key
2. Try to use it
3. Verify 401 Unauthorized
✅ PASS / ❌ FAIL: __________

**Test 4.4: API Key Usage Logging**
1. Make several requests with API key
2. Go to API Keys → View Usage
3. Verify all requests logged with endpoints and timestamps
✅ PASS / ❌ FAIL: __________

---

#### 5. WebSocket Integration Tests

**Test 5.1: WebSocket Connection**
1. Login to app
2. Open browser console
3. Verify "WebSocket connected" message
✅ PASS / ❌ FAIL: __________

**Test 5.2: Real-time Ticket Notification**
1. Open app in two browser tabs (same user)
2. In tab 1, create a ticket
3. In tab 2, verify toast notification appears
✅ PASS / ❌ FAIL: __________

**Test 5.3: Dashboard Real-time Update**
1. Open dashboard
2. Wait 30 seconds
3. Verify dashboard stats refresh automatically (check console for "dashboard.update" event)
✅ PASS / ❌ FAIL: __________

**Test 5.4: User Presence**
1. Open app in two tabs with different users
2. Verify "user.online" events in console
3. Close one tab
4. Verify "user.offline" event in other tab
✅ PASS / ❌ FAIL: __________

**Test 5.5: WebSocket Reconnect**
1. Login and verify connected
2. Stop backend server
3. Verify "WebSocket disconnected" in console
4. Start backend server
5. Verify automatic reconnection within 30 seconds
✅ PASS / ❌ FAIL: __________

---

#### 6. Cross-Feature Integration Tests

**Test 6.1: Ticket → Email + Webhook + WebSocket**
1. Configure:
   - Email recipients for tickets
   - Webhook for ticket.created
   - WebSocket connected
2. Create a critical ticket
3. Verify ALL THREE triggered:
   - Email received
   - Webhook delivery log shows success
   - WebSocket real-time notification shown
✅ PASS / ❌ FAIL: __________

**Test 6.2: Settings → Email Template → Send**
1. Update email template in database (change subject)
2. Clear settings cache (restart server or wait 60s)
3. Trigger email (create ticket)
4. Verify new template used
✅ PASS / ❌ FAIL: __________

**Test 6.3: API Key → Trigger Webhook**
1. Create API key with "tickets:write" scope
2. Use API key to create ticket via API
3. Verify webhook triggered
4. Verify API key usage logged
✅ PASS / ❌ FAIL: __________

---

#### 7. Permission & Security Tests

**Test 7.1: Module Permission Enforcement**
1. Create non-admin user with only "com_smtp" permission
2. Login as that user
3. Verify can access `/communication/smtp`
4. Verify cannot access `/communication/webhooks` (403)
✅ PASS / ❌ FAIL: __________

**Test 7.2: Admin-Only Settings**
1. Login as non-admin user
2. Try to access `/settings`
3. Verify 403 Forbidden or redirect
✅ PASS / ❌ FAIL: __________

**Test 7.3: API Key Scope Wildcard**
1. Create API key with "admin:*" scope
2. Verify can access all admin endpoints
3. Create API key with "inventory:*" scope
4. Verify can read, write, delete inventory
✅ PASS / ❌ FAIL: __________

---

## PART 2: ADMIN DOCUMENTATION

### Admin Guide: Communication Module

Save this as: `docs/admin-guide-communication.md`

```markdown
# Communication Module - Admin Guide

## Overview

The Communication module provides multiple channels for notifications and integrations:

1. **Telegram** - Bot notifications to Telegram
2. **Email (SMTP)** - Email notifications
3. **Webhooks** - HTTP callbacks for event-driven integrations
4. **API Keys** - Programmatic API access
5. **Real-time (WebSocket)** - Live dashboard updates

---

## SMTP Email Setup

### Step 1: Configure SMTP Settings

1. Navigate to **Settings → Email**
2. Enter SMTP details:
   - **SMTP Host**: `smtp.gmail.com` (for Gmail)
   - **SMTP Port**: `587`
   - **SMTP User**: Your email address
   - **SMTP Password**: App-specific password (not your regular password)
   - **From Email**: Email address to send from
   - **From Name**: Display name (e.g., "Farm Management System")
3. Enable **Use TLS**: Yes
4. Click **Save Changes**

### Step 2: Test SMTP

1. Navigate to **Communication → Email (SMTP)**
2. Click **Test SMTP**
3. Enter your email address
4. Click **Send Test Email**
5. Check your inbox - you should receive a test email

### Step 3: Configure Email Recipients

1. Go to **Communication → Email (SMTP) → Recipients tab**
2. Configure recipient lists:
   - **Tickets Critical**: Emails for critical priority tickets
   - **Tickets All**: Emails for all ticket notifications
   - **Low Stock**: Emails for inventory low stock alerts
   - **User Created**: Emails when new users are created

Example: `admin@company.com, manager@company.com`

---

## Webhook Setup

### Creating a Webhook

1. Navigate to **Communication → Webhooks**
2. Click **Add Webhook**
3. Fill in details:
   - **Name**: Descriptive name (e.g., "Slack Ticket Notifications")
   - **URL**: Webhook endpoint URL
   - **Events**: Select events to subscribe to
   - **Description**: Optional notes
4. Click **Create**
5. Copy the **secret** (used for signature verification)

### Testing a Webhook

1. Use webhook.site to get a test URL
2. Create webhook with that URL
3. Select an event (e.g., "ticket.created")
4. Click **Test** icon
5. Check webhook.site - you should see the test payload

### Webhook Security

All webhook requests include a signature header:
```
X-Webhook-Signature: sha256=<hmac_signature>
```

Verify signatures in your webhook receiver to ensure authenticity.

### Delivery Logs

1. Click **History** icon on any webhook
2. View delivery attempts, status codes, and error messages
3. Failed deliveries retry automatically (up to 3 attempts)

---

## API Key Management

### Creating an API Key

1. Navigate to **Communication → API Keys**
2. Click **Create API Key**
3. Fill in details:
   - **Name**: Descriptive name (e.g., "CI/CD Pipeline")
   - **Description**: What this key is used for
   - **Scopes**: Select permissions (e.g., `inventory:read`)
   - **Expires in**: Days until expiration (1-365)
4. Click **Create**
5. **IMPORTANT**: Copy the API key NOW - you won't see it again!

### Using an API Key

Include in HTTP requests:
```bash
curl -H "X-API-Key: sk_live_..." https://your-app.com/api/v1/inventory
```

### Revoking an API Key

1. Find the key in the list
2. Click **Delete** icon
3. Confirm revocation
4. The key is immediately invalidated

### Viewing API Key Usage

1. Click on an API key
2. View recent requests (endpoint, timestamp, IP address)
3. Monitor for suspicious activity

---

## Real-time Notifications

WebSocket connections are established automatically when users log in.

### Features:
- Live dashboard updates (every 30 seconds)
- Instant ticket notifications
- User presence indicators
- Low stock alerts

### Troubleshooting:

**WebSocket not connecting:**
1. Check browser console for errors
2. Verify WebSocket URL in environment config
3. Check firewall allows WebSocket connections
4. For production, ensure `wss://` (secure WebSocket) is configured

---

## Email Templates

Email templates are stored in the database. To customize:

1. Access Supabase
2. Go to `email_templates` table
3. Edit `html_body` and `plain_body` fields
4. Available variables shown in `variables` column
5. Use `{{variable_name}}` syntax

Example:
```html
<p>Hi {{user_name}},</p>
<p>Your ticket "{{ticket_title}}" has been created.</p>
```

---

## Best Practices

1. **Email:** Use a dedicated email account for system notifications
2. **Webhooks:** Always verify signatures for security
3. **API Keys:** Grant minimum required scopes (principle of least privilege)
4. **Monitoring:** Regularly check delivery logs for failures

---

## Troubleshooting

### Emails not sending
- Check SMTP settings are correct
- Verify email queue (`email_queue` table)
- Check error messages in queue
- Ensure scheduler is running (check logs)

### Webhooks failing
- Check webhook URL is accessible
- View delivery logs for error details
- Verify endpoint accepts POST requests
- Check for timeout issues (increase timeout in webhook settings)

### API Keys not working
- Verify key hasn't expired
- Check key hasn't been revoked
- Ensure required scopes are granted
- Check API key usage logs for errors
```

---

## PART 3: USER DOCUMENTATION

Save as: `docs/user-guide-communication.md`

```markdown
# Communication Features - User Guide

## Email Notifications

You'll receive email notifications for:
- Ticket updates (if you're involved)
- Low stock alerts (admins only)
- System announcements

### Managing Email Preferences

1. Go to **Profile → Notification Settings**
2. Toggle email notifications on/off
3. Update your email address if needed

---

## API Keys (Advanced Users)

API keys allow you to access the system programmatically.

### When to use API Keys

- Automation scripts
- CI/CD pipelines
- External integrations
- Mobile/desktop apps

### Creating an API Key

1. Go to **Communication → API Keys**
2. Click **Create API Key**
3. Choose scopes (permissions)
4. Set expiration date
5. Copy the key immediately

### Example Usage

```python
import requests

API_KEY = "sk_live_your_key_here"
headers = {"X-API-Key": API_KEY}

response = requests.get(
    "https://your-app.com/api/v1/inventory",
    headers=headers
)

print(response.json())
```

### Security Tips

- Never share your API keys
- Store keys in environment variables, not code
- Use minimum required scopes
- Revoke unused keys
- Set expiration dates

---

## Real-time Updates

The app automatically receives real-time updates:
- New tickets appear instantly
- Dashboard refreshes automatically
- Notifications pop up in real-time

No configuration needed - it just works!
```

---

## PART 4: DEVELOPER DOCUMENTATION

Save as: `docs/developer-guide-communication.md`

```markdown
# Communication Module - Developer Guide

## Architecture

### Components

1. **Settings Service**: Centralized configuration with caching
2. **Email Service**: SMTP with template rendering and queue
3. **Webhook Service**: HTTP callbacks with retry logic
4. **API Key Service**: Scoped authentication
5. **WebSocket Manager**: Real-time event broadcasting

### Data Flow

```
Event Occurs (e.g., ticket created)
    ↓
Trigger Notifications:
    ├─ Email Service → Queue → SMTP
    ├─ Webhook Service → Queue → HTTP POST
    └─ WebSocket Manager → Broadcast to clients
```

---

## Adding New Email Templates

1. Insert into `email_templates` table:

```sql
INSERT INTO email_templates (
    template_key,
    name,
    subject,
    html_body,
    plain_body,
    variables
) VALUES (
    'my_template',
    'My Template',
    'Subject: {{variable}}',
    '<p>HTML body: {{variable}}</p>',
    'Plain body: {{variable}}',
    '["variable"]'::jsonb
);
```

2. Use in code:

```python
await email_service.send_template_email(
    conn,
    to_email="user@example.com",
    template_key="my_template",
    variables={"variable": "value"}
)
```

---

## Adding New Webhook Events

1. Add to `AVAILABLE_EVENTS` in `webhook_service.py`:

```python
AVAILABLE_EVENTS = [
    'ticket.created',
    'my.new.event',  # Add here
]
```

2. Trigger in your code:

```python
from app.services import webhook_service

await webhook_service.trigger_event(
    conn,
    'my.new.event',
    {"key": "value"}
)
```

---

## Adding New API Scopes

1. Add to `AVAILABLE_SCOPES` in `api_key_service.py`:

```python
AVAILABLE_SCOPES = [
    # ...
    "mymodule:read",
    "mymodule:write",
]
```

2. Use in route:

```python
from app.dependencies import require_api_key_scope

@router.get("/mymodule")
async def get_data(
    user: dict = Depends(require_api_key_scope("mymodule:read"))
):
    # ...
```

---

## WebSocket Event Broadcasting

```python
from app.websocket import events as ws_events

# Broadcast to all users
await ws_events.emit_dashboard_update(stats)

# Send to specific user
await ws_events.emit_notification(user_id, notification)

# Emit custom event
from app.websocket.connection_manager import manager

await manager.broadcast({
    "type": "custom.event",
    "data": {"message": "Hello"}
})
```

---

## Testing

Run integration tests:

```bash
pytest tests/integration/test_communication.py -v
```

Test email sending:

```bash
python scripts/test_email.py --to your@email.com
```

Test webhooks:

```bash
python scripts/test_webhook.py --url https://webhook.site/...
```
```

---

## PART 5: PRODUCTION DEPLOYMENT CHECKLIST

### Pre-Deployment

- [ ] All migrations run successfully
- [ ] All integration tests pass
- [ ] SMTP configured with production credentials
- [ ] WebSocket URL configured for production (wss://)
- [ ] Environment variables set:
  ```
  VITE_API_BASE_URL=https://api.yourapp.com
  VITE_WS_URL=wss://api.yourapp.com
  ```
- [ ] Settings configured via UI (not just env vars)
- [ ] Email templates customized
- [ ] Email recipients configured
- [ ] Default API key scopes reviewed

### Deployment Steps

1. **Database:**
   ```bash
   # Run all migrations in order
   psql $DATABASE_URL < backend/migrations/007_communication_module.sql
   psql $DATABASE_URL < backend/migrations/008_system_settings.sql
   psql $DATABASE_URL < backend/migrations/009_smtp_email.sql
   psql $DATABASE_URL < backend/migrations/010_webhooks.sql
   psql $DATABASE_URL < backend/migrations/011_api_keys.sql
   ```

2. **Backend:**
   ```bash
   pip install -r requirements.txt
   # Restart backend server
   systemctl restart farmapp-backend
   ```

3. **Frontend:**
   ```bash
   npm run build
   # Deploy dist/ folder
   ```

4. **Scheduler:**
   Verify background jobs running:
   - Email queue processing (every 5 min)
   - Webhook queue processing (every 2 min)
   - Dashboard WebSocket broadcast (every 30 sec)

### Post-Deployment Verification

- [ ] Can login successfully
- [ ] WebSocket connects automatically
- [ ] Send test email successfully
- [ ] Create test webhook and verify delivery
- [ ] Create test API key and use it
- [ ] Create ticket → verify all notifications work
- [ ] Check logs for errors

### Monitoring

Set up monitoring for:
- Email queue size (alert if > 100 pending)
- Webhook delivery failure rate (alert if > 10%)
- WebSocket connection count
- API key usage spikes

---

## 🎯 SUCCESS CRITERIA

This project is complete when:

1. ✅ All integration tests pass
2. ✅ Documentation complete (admin, user, developer)
3. ✅ Production deployment successful
4. ✅ All features verified working in production
5. ✅ Team trained on new features

---

## 📦 DELIVERABLES

1. **Code:**
   - All migrations (007-011)
   - Backend services and routes
   - Frontend pages and components
   - WebSocket implementation

2. **Documentation:**
   - Admin guide
   - User guide
   - Developer guide
   - API documentation

3. **Tests:**
   - Integration test results
   - Production verification checklist

4. **Deployment:**
   - Production deployment completed
   - Monitoring configured

---

**CONGRATULATIONS! 🎉**

You've successfully built a complete Communication framework with:
- Advanced Settings Management
- SMTP Email System
- Webhook Integration
- API Key Authentication
- Real-time WebSocket Updates

The system is production-ready and fully documented!
