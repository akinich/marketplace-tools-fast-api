# Communication Module - Administrator Guide

**Version:** 1.0.0
**Last Updated:** 2025-11-23
**Module:** Communication & Integration Framework

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [SMTP Email Setup](#smtp-email-setup)
3. [Webhook Management](#webhook-management)
4. [API Key Administration](#api-key-administration)
5. [Real-time Notifications (WebSocket)](#real-time-notifications-websocket)
6. [Settings Management](#settings-management)
7. [Email Templates](#email-templates)
8. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
9. [Security Best Practices](#security-best-practices)
10. [FAQ](#faq)

---

## Overview

The Communication Module provides multiple channels for notifications, integrations, and real-time updates:

| Feature | Purpose | Use Case |
|---------|---------|----------|
| **SMTP Email** | Send automated email notifications | Ticket alerts, low stock warnings, user onboarding |
| **Webhooks** | HTTP callbacks for event-driven integrations | Integrate with Slack, Discord, external systems |
| **API Keys** | Programmatic API access | CI/CD pipelines, automation scripts, mobile apps |
| **WebSocket** | Real-time bidirectional communication | Live dashboard updates, instant notifications |
| **Telegram** | Bot notifications to Telegram | Mobile alerts, team notifications |

### Key Benefits

- **Centralized Configuration**: All settings managed in one place
- **Template-based Emails**: Customizable HTML email templates
- **Retry Logic**: Automatic retry for failed deliveries
- **Audit Trail**: Complete logging of all activities
- **Security**: Signature verification, scoped permissions, encryption

---

## SMTP Email Setup

### Step 1: Configure SMTP Settings

1. Navigate to **Settings → Email** in the admin panel
2. Enter your SMTP server details:

   | Field | Example (Gmail) | Description |
   |-------|-----------------|-------------|
   | SMTP Host | `smtp.gmail.com` | Your email provider's SMTP server |
   | SMTP Port | `587` | Port for TLS (or `465` for SSL) |
   | SMTP User | `your-email@gmail.com` | Email account username |
   | SMTP Password | `your-app-password` | App-specific password (not regular password) |
   | From Email | `notifications@yourfarm.com` | Sender email address |
   | From Name | `Marketplace ERP Tools` | Display name for emails |
   | Use TLS | ✅ Yes | Enable TLS encryption |

3. Click **Save Changes**

> **⚠️ Important for Gmail Users:**
> - Enable 2-Factor Authentication on your Google account
> - Generate an App Password: [Google App Passwords](https://myaccount.google.com/apppasswords)
> - Use the 16-character app password (not your regular password)

### Step 2: Test SMTP Configuration

1. Go to **Communication → Email (SMTP)**
2. Click **"Test SMTP Connection"** button
3. Enter your email address in the dialog
4. Click **"Send Test Email"**
5. Check your inbox - you should receive a test email within 60 seconds

✅ **Success**: Email received
❌ **Failure**: Check error message and verify settings

### Step 3: Configure Email Recipients

Configure who receives automated emails for different event types:

1. Navigate to **Communication → Email (SMTP) → Recipients**
2. Configure recipient lists:

   | Recipient List | Description | Format |
   |----------------|-------------|--------|
   | **Tickets - Critical** | Notified for critical priority tickets | `admin@farm.com, manager@farm.com` |
   | **Tickets - All** | Notified for all ticket events | `support@farm.com` |
   | **Low Stock Alerts** | Inventory items below reorder level | `inventory@farm.com, purchasing@farm.com` |
   | **User Created** | New user account notifications | `hr@farm.com, admin@farm.com` |
   | **System Alerts** | Critical system notifications | `admin@farm.com, tech@farm.com` |

3. Enter emails separated by commas
4. Click **"Save Recipients"**

### Step 4: Monitor Email Queue

1. Go to **Communication → Email (SMTP) → Queue**
2. View pending, sent, and failed emails
3. Check delivery status and timestamps

**Email Queue Statuses:**
- 🟡 **Pending**: Queued for sending
- 🟢 **Sent**: Successfully delivered
- 🔴 **Failed**: Delivery failed after max retries
- 🔵 **Retrying**: Temporary failure, will retry

### Troubleshooting SMTP Issues

| Issue | Solution |
|-------|----------|
| **"Authentication failed"** | 1. Verify SMTP username/password<br>2. For Gmail, use App Password<br>3. Check if 2FA is enabled |
| **"Connection timeout"** | 1. Verify SMTP host and port<br>2. Check firewall allows outbound connections<br>3. Try different port (587/465) |
| **"TLS/SSL error"** | 1. Ensure "Use TLS" matches port<br>2. Port 587 = TLS, Port 465 = SSL |
| **Emails not arriving** | 1. Check spam folder<br>2. Verify email queue shows "sent"<br>3. Check recipient email is valid |
| **"Sender domain not allowed"** | 1. Some providers require matching sender domain<br>2. Use email from same domain as SMTP server |

---

## Webhook Management

Webhooks allow external systems to receive real-time notifications when events occur in your farm management system.

### Creating a Webhook

1. Navigate to **Communication → Webhooks**
2. Click **"Create Webhook"** button
3. Fill in the webhook details:

   | Field | Example | Description |
   |-------|---------|-------------|
   | **Name** | `Slack Ticket Notifications` | Descriptive name for reference |
   | **URL** | `https://hooks.slack.com/services/...` | Endpoint to receive webhook POSTs |
   | **Events** | `ticket.created`, `ticket.updated` | Select events to trigger this webhook |
   | **Description** | `Sends ticket alerts to #operations` | Optional notes |
   | **Active** | ✅ Enabled | Enable/disable without deleting |

4. Click **"Create Webhook"**
5. **⚠️ IMPORTANT**: Copy the **Secret Key** shown - you won't see it again!

### Available Webhook Events

| Event Name | Triggered When | Payload Includes |
|------------|----------------|------------------|
| `ticket.created` | New ticket is created | ticket ID, title, priority, creator |
| `ticket.updated` | Ticket status/details change | ticket ID, changes made, updater |
| `ticket.comment` | Comment added to ticket | comment text, author, timestamp |
| `inventory.low_stock` | Item stock below reorder level | item name, current stock, reorder level |
| `user.created` | New user account created | username, email, role |
| `user.login` | User logs into system | username, IP address, timestamp |
| `dashboard.update` | Dashboard stats change | updated statistics |

### Testing a Webhook

**Method 1: Built-in Test**
1. Find the webhook in the list
2. Click the **"Test"** icon (🧪)
3. System sends a test payload
4. Check your endpoint received the request

**Method 2: Use webhook.site**
1. Go to [webhook.site](https://webhook.site)
2. Copy the unique URL provided
3. Create a webhook with that URL
4. Subscribe to an event (e.g., `ticket.created`)
5. Create a test ticket in the system
6. Refresh webhook.site - you should see the payload

### Webhook Payload Format

All webhook requests are sent as HTTP POST with JSON payload:

```json
{
  "event": "ticket.created",
  "timestamp": "2025-11-23T10:30:00Z",
  "webhook_id": "wh_1234567890",
  "data": {
    "ticket_id": 42,
    "title": "Critical system error",
    "priority": "critical",
    "created_by": "john.doe",
    "created_at": "2025-11-23T10:29:55Z"
  }
}
```

### Verifying Webhook Signatures

Every webhook request includes a signature header for security:

```
X-Webhook-Signature: sha256=abc123def456...
```

**To verify (Python example):**
```python
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(
        f"sha256={expected}",
        signature
    )

# In your webhook receiver:
signature = request.headers.get('X-Webhook-Signature')
payload = request.body.decode('utf-8')
secret = "your_webhook_secret"

if not verify_signature(payload, signature, secret):
    return {"error": "Invalid signature"}, 403
```

### Webhook Delivery Logs

1. Click **"History"** icon on any webhook
2. View delivery attempts with:
   - Timestamp
   - HTTP status code
   - Response body
   - Retry attempts
   - Error messages

**Delivery Statuses:**
- ✅ **Success** (200-299): Delivered successfully
- 🔄 **Retrying** (4xx/5xx): Failed, will retry
- ❌ **Failed**: Max retries exceeded

### Retry Logic

- **Max Attempts**: 3
- **Retry Interval**: Exponential backoff (1min, 5min, 15min)
- **Timeout**: 30 seconds per request
- **Retry Triggers**: Network errors, 5xx responses, timeouts

### Managing Webhooks

**Edit Webhook:**
1. Click **"Edit"** icon
2. Update name, URL, or events
3. Save changes

**Disable Webhook:**
1. Click **"Edit"** icon
2. Toggle "Active" to disabled
3. Webhook stops receiving events but history is preserved

**Delete Webhook:**
1. Click **"Delete"** icon
2. Confirm deletion
3. ⚠️ This permanently deletes delivery history

**Rotate Secret:**
1. Click **"Regenerate Secret"**
2. Copy the new secret
3. Update your webhook receiver with new secret
4. Old secret invalidated immediately

---

## API Key Administration

API Keys allow programmatic access to the Marketplace ERP Tools API without user credentials.

### Creating an API Key

1. Navigate to **Communication → API Keys**
2. Click **"Create API Key"**
3. Configure the key:

   | Field | Example | Description |
   |-------|---------|-------------|
   | **Name** | `CI/CD Pipeline` | Descriptive name for tracking |
   | **Description** | `Automated deployments` | What this key is used for |
   | **Scopes** | `inventory:read`, `inventory:write` | Permissions (see scope list below) |
   | **Expires In** | `90 days` | Days until expiration (1-365) |

4. Click **"Create"**
5. **⚠️ CRITICAL**: Copy the API key NOW - it's shown only once!

   ```
   your-api-key-will-appear-here-copy-it-now
   ```

### Available API Scopes

API keys use scope-based permissions for fine-grained access control:

#### Admin Scopes
| Scope | Permissions | Use Case |
|-------|------------|----------|
| `admin:*` | Full admin access | System administration |
| `admin:read` | View admin panels | Monitoring dashboards |
| `admin:write` | Modify admin settings | Configuration management |

#### Inventory Scopes
| Scope | Permissions | Use Case |
|-------|------------|----------|
| `inventory:*` | Full inventory access | Complete inventory management |
| `inventory:read` | View inventory items | Reporting, analytics |
| `inventory:write` | Create/update items | Automated stock updates |
| `inventory:delete` | Delete items | Cleanup scripts |

#### Ticket Scopes
| Scope | Permissions | Use Case |
|-------|------------|----------|
| `tickets:*` | Full ticket access | Complete ticket management |
| `tickets:read` | View tickets | Support dashboards |
| `tickets:write` | Create/update tickets | Automated ticket creation |
| `tickets:delete` | Delete tickets | Maintenance scripts |

#### Biofloc Scopes
| Scope | Permissions | Use Case |
|-------|------------|----------|
| `biofloc:*` | Full biofloc access | Complete biofloc management |
| `biofloc:read` | View biofloc data | Monitoring systems |
| `biofloc:write` | Update readings | IoT sensor integration |

#### Communication Scopes
| Scope | Permissions | Use Case |
|-------|------------|----------|
| `webhooks:*` | Manage webhooks | Webhook administration |
| `apikeys:*` | Manage API keys | API key administration |
| `email:*` | Manage email system | Email configuration |

### Using API Keys

Include the API key in the `X-API-Key` header:

**cURL Example:**
```bash
curl -H "X-API-Key: your_api_key_here" \
     https://your-farm-api.com/api/v1/inventory
```

**Python Example:**
```python
import requests

API_KEY = "your_api_key_here"
headers = {"X-API-Key": API_KEY}

response = requests.get(
    "https://your-farm-api.com/api/v1/inventory",
    headers=headers
)

print(response.json())
```

**JavaScript Example:**
```javascript
const API_KEY = "your_api_key_here";

fetch("https://your-farm-api.com/api/v1/inventory", {
  headers: {
    "X-API-Key": API_KEY
  }
})
.then(res => res.json())
.then(data => console.log(data));
```

### API Key Usage Analytics

1. Click on an API key in the list
2. View usage statistics:
   - Total requests
   - Requests per endpoint
   - Recent activity log
   - Error rate
   - Last used timestamp

**Usage Log Includes:**
- Timestamp
- HTTP method (GET, POST, etc.)
- Endpoint accessed
- Response status
- IP address

### Revoking API Keys

**Immediate Revocation:**
1. Find the key in the list
2. Click **"Delete"** icon
3. Confirm revocation
4. Key is immediately invalidated

**All requests with this key will return:**
```json
{
  "detail": "Invalid or revoked API key"
}
```

### API Key Security Best Practices

1. ✅ **Use minimum required scopes** - Grant only necessary permissions
2. ✅ **Set expiration dates** - Don't create permanent keys
3. ✅ **Rotate keys regularly** - Refresh keys every 90 days
4. ✅ **One key per application** - Don't share keys across systems
5. ✅ **Monitor usage** - Check logs for unexpected activity
6. ✅ **Revoke unused keys** - Delete keys no longer in use
7. ✅ **Store securely** - Use environment variables, never hardcode
8. ❌ **Never commit to git** - Add to `.gitignore`
9. ❌ **Never share publicly** - Don't post in forums/tickets
10. ❌ **Never reuse keys** - Create separate keys for each purpose

---

## Real-time Notifications (WebSocket)

WebSocket provides bidirectional, real-time communication between the server and connected clients.

### How It Works

1. **User logs in** → WebSocket connection established automatically
2. **Event occurs** → Server broadcasts to connected clients
3. **Client receives** → UI updates instantly without refresh

### Features Powered by WebSocket

| Feature | Description | Update Frequency |
|---------|-------------|------------------|
| **Dashboard Stats** | Live metrics updates | Every 30 seconds |
| **Ticket Notifications** | Instant ticket alerts | Real-time |
| **Low Stock Alerts** | Inventory warnings | Real-time |
| **User Presence** | Online/offline indicators | Real-time |
| **System Notifications** | Admin broadcasts | Real-time |

### WebSocket Events

#### Server → Client Events

| Event Type | When Sent | Payload |
|------------|-----------|---------|
| `dashboard.update` | Every 30 seconds | `{stats: {...}}` |
| `ticket.created` | New ticket created | `{ticket: {...}}` |
| `ticket.updated` | Ticket modified | `{ticket_id, changes}` |
| `notification` | System notification | `{message, type, priority}` |
| `user.online` | User connects | `{user_id, username}` |
| `user.offline` | User disconnects | `{user_id, username}` |

#### Client → Server Events

| Event Type | Purpose | Payload |
|------------|---------|---------|
| `ping` | Keep connection alive | `{}` |
| `subscribe` | Subscribe to specific events | `{events: [...]}` |
| `unsubscribe` | Unsubscribe from events | `{events: [...]}` |

### Connection Management

**Automatic Reconnection:**
- If connection drops, client auto-reconnects
- Exponential backoff: 1s, 2s, 4s, 8s, max 30s
- Max reconnection attempts: Unlimited
- Shows connection status in UI

**Connection States:**
- 🟢 **Connected**: Real-time updates active
- 🟡 **Connecting**: Attempting to connect
- 🔴 **Disconnected**: No real-time updates

### Troubleshooting WebSocket

| Issue | Solution |
|-------|----------|
| **Not connecting** | 1. Check WebSocket URL in config<br>2. Verify firewall allows WebSocket (port 8000)<br>3. For production, ensure WSS (secure WebSocket) |
| **Frequent disconnects** | 1. Check server logs for errors<br>2. Verify network stability<br>3. Check for reverse proxy timeout settings |
| **No updates received** | 1. Open browser console, check for WebSocket messages<br>2. Verify user has permissions for event type<br>3. Check server is broadcasting events |
| **"WebSocket failed"** | 1. Check browser supports WebSocket (all modern browsers do)<br>2. Verify URL format: `ws://` or `wss://`<br>3. Check CORS settings |

**For Production (HTTPS sites):**
- Must use `wss://` (secure WebSocket)
- HTTP sites cannot use WebSocket on HTTPS pages
- Configure reverse proxy (nginx) for WebSocket passthrough

**Nginx WebSocket Configuration:**
```nginx
location /ws {
    proxy_pass http://backend:8000/ws;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400;
}
```

---

## Settings Management

Centralized configuration for all communication features.

### Accessing Settings

1. Navigate to **Settings** (admin only)
2. Select category from sidebar:
   - **Email (SMTP)**
   - **Telegram**
   - **Authentication**
   - **Security**
   - **General**

### Settings Categories

#### Email Settings
- SMTP server configuration
- Email templates
- Recipient lists
- Queue processing interval

#### Telegram Settings
- Bot token
- Default chat ID
- Notification preferences
- Message templates

#### Authentication Settings
- JWT expiry time
- Password requirements
- Session timeout
- 2FA settings

#### Security Settings
- API rate limiting
- IP whitelist/blacklist
- Webhook signature verification
- API key expiration policies

### Settings Audit Log

Every settings change is logged:

1. Go to **Settings → Audit Log**
2. View history with:
   - **Who** changed the setting
   - **What** was changed (old → new value)
   - **When** the change occurred
   - **Why** (optional change reason)

### Settings Caching

- Settings cached for **60 seconds** for performance
- Changes take effect within 1 minute
- Force refresh: Restart backend server
- Clear cache: Call `/api/v1/settings/clear-cache` (admin only)

---

## Email Templates

Customize email appearance and content with HTML templates.

### Available Templates

| Template Key | Purpose | Triggers When |
|--------------|---------|---------------|
| `ticket_created` | Ticket notification | New ticket created |
| `ticket_updated` | Ticket status change | Ticket modified |
| `low_stock_alert` | Inventory warning | Stock below reorder level |
| `user_welcome` | User onboarding | New user account created |
| `password_reset` | Password recovery | User requests password reset |
| `system_alert` | Critical notifications | System events, errors |

### Editing Templates

Templates are stored in the database. To customize:

1. **Access Database**: Connect to PostgreSQL
2. **Navigate to Table**: `email_templates`
3. **Edit Template**: Update `html_body` or `plain_body`

**Template Variables:**

Use `{{variable_name}}` syntax in templates:

```html
<h1>Hello {{user_name}},</h1>
<p>Your ticket <strong>{{ticket_title}}</strong> has been created.</p>
<p>Priority: <span style="color: red;">{{priority}}</span></p>
<a href="{{ticket_url}}">View Ticket</a>
```

**Available Variables by Template:**

**Ticket Templates:**
- `{{user_name}}` - Recipient name
- `{{ticket_id}}` - Ticket ID
- `{{ticket_title}}` - Ticket title
- `{{priority}}` - Priority level
- `{{status}}` - Current status
- `{{ticket_url}}` - Direct link to ticket
- `{{created_at}}` - Creation timestamp

**Low Stock Template:**
- `{{item_name}}` - Inventory item name
- `{{current_stock}}` - Current quantity
- `{{reorder_level}}` - Minimum stock level
- `{{category}}` - Item category
- `{{unit}}` - Unit of measurement

**User Welcome Template:**
- `{{user_name}}` - New user's name
- `{{username}}` - Login username
- `{{email}}` - User email
- `{{temp_password}}` - Temporary password
- `{{login_url}}` - Login page URL
- `{{role}}` - User role

### Template Best Practices

1. ✅ **Include plain text version** - For email clients without HTML
2. ✅ **Test before deploying** - Send test emails to verify rendering
3. ✅ **Keep it simple** - Avoid complex CSS (limited email client support)
4. ✅ **Mobile responsive** - Use tables for layout, max-width 600px
5. ✅ **Include unsubscribe** - For bulk notifications
6. ❌ **Avoid JavaScript** - Email clients block it
7. ❌ **Avoid external CSS** - Use inline styles instead

**Example Template:**

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto;">
        <tr>
            <td style="background: #4CAF50; padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">Marketplace ERP Tools</h1>
            </td>
        </tr>
        <tr>
            <td style="padding: 20px;">
                <h2>Hi {{user_name}},</h2>
                <p>A new ticket has been created:</p>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Title:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{{ticket_title}}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Priority:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{{priority}}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Created:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{{created_at}}</td>
                    </tr>
                </table>
                <p style="text-align: center; margin-top: 20px;">
                    <a href="{{ticket_url}}"
                       style="background: #4CAF50; color: white; padding: 12px 24px;
                              text-decoration: none; border-radius: 4px; display: inline-block;">
                        View Ticket
                    </a>
                </p>
            </td>
        </tr>
        <tr>
            <td style="background: #f4f4f4; padding: 10px; text-align: center; font-size: 12px; color: #666;">
                <p>© 2025 Marketplace ERP Tools. All rights reserved.</p>
            </td>
        </tr>
    </table>
</body>
</html>
```

---

## Monitoring & Troubleshooting

### System Health Dashboard

1. Navigate to **Admin → System Health**
2. View communication module status:
   - Email queue size
   - Webhook delivery rate
   - API key active count
   - WebSocket connections
   - Recent errors

### Email Queue Monitoring

**Check Queue Status:**
```bash
# Access database
psql $DATABASE_URL

# Count pending emails
SELECT status, COUNT(*)
FROM email_queue
GROUP BY status;

# View failed emails
SELECT * FROM email_queue
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 10;
```

**Clear Stuck Emails:**
```sql
-- Reset failed emails to retry
UPDATE email_queue
SET status = 'pending',
    attempts = 0
WHERE status = 'failed'
  AND created_at > NOW() - INTERVAL '1 day';
```

### Webhook Monitoring

**Check Delivery Success Rate:**
```sql
SELECT
    w.name,
    COUNT(CASE WHEN wd.status = 'success' THEN 1 END) as successful,
    COUNT(CASE WHEN wd.status = 'failed' THEN 1 END) as failed,
    ROUND(COUNT(CASE WHEN wd.status = 'success' THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate
FROM webhooks w
LEFT JOIN webhook_deliveries wd ON w.id = wd.webhook_id
WHERE wd.created_at > NOW() - INTERVAL '7 days'
GROUP BY w.name;
```

### API Key Usage Monitoring

**Check Top API Keys by Usage:**
```sql
SELECT
    ak.name,
    COUNT(*) as request_count,
    COUNT(DISTINCT DATE(akl.created_at)) as active_days,
    MAX(akl.created_at) as last_used
FROM api_keys ak
JOIN api_key_logs akl ON ak.id = akl.api_key_id
WHERE akl.created_at > NOW() - INTERVAL '30 days'
GROUP BY ak.name
ORDER BY request_count DESC
LIMIT 10;
```

### Common Issues & Solutions

#### Email Issues

**Problem: Emails stuck in pending**
```bash
# Check scheduler is running
curl http://localhost:8000/health

# Check email queue processing job
# Should show: "process_email_queue" in scheduled_jobs
```

**Solution:**
- Restart backend server
- Check SMTP settings are correct
- Verify scheduler is running

**Problem: All emails failing**
```sql
-- Check error messages
SELECT error_message, COUNT(*)
FROM email_queue
WHERE status = 'failed'
GROUP BY error_message;
```

**Solution:**
- If "Authentication failed": Check SMTP password
- If "Connection timeout": Check SMTP host/port
- If "Sender not allowed": Use matching email domain

#### Webhook Issues

**Problem: Webhooks timing out**
```sql
-- Check average response time
SELECT
    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_seconds
FROM webhook_deliveries
WHERE created_at > NOW() - INTERVAL '1 hour';
```

**Solution:**
- If > 30 seconds: Optimize receiving endpoint
- Increase timeout in webhook settings
- Use asynchronous processing on receiver

**Problem: Webhooks not triggering**
```sql
-- Check if webhooks are active
SELECT name, active, events
FROM webhooks;
```

**Solution:**
- Verify webhook is active
- Check correct events are subscribed
- Verify event is actually occurring

#### API Key Issues

**Problem: API key not working**
```sql
-- Check key status
SELECT name, active, expires_at, scopes
FROM api_keys
WHERE key_prefix = 'your_key_prefix';  -- Replace with first 15 chars of your key
```

**Solution:**
- If `active = false`: Key was revoked
- If `expires_at < NOW()`: Key expired
- If missing scope: Recreate with correct scopes

---

## Security Best Practices

### Email Security

1. ✅ **Use App Passwords** - Never use account password for SMTP
2. ✅ **Enable TLS** - Encrypt email transmission
3. ✅ **Validate Recipients** - Only send to verified email addresses
4. ✅ **Rate Limit** - Prevent email bombing
5. ❌ **Don't log passwords** - Email service doesn't log SMTP password

### Webhook Security

1. ✅ **Verify Signatures** - Always validate `X-Webhook-Signature`
2. ✅ **Use HTTPS** - Webhook URLs must use HTTPS in production
3. ✅ **Rotate Secrets** - Refresh webhook secrets every 90 days
4. ✅ **Whitelist IPs** - Restrict webhook receiver to known IPs
5. ✅ **Rate Limit** - Prevent webhook flooding
6. ❌ **Don't expose secrets** - Never commit secrets to git

### API Key Security

1. ✅ **Minimum Scopes** - Grant only necessary permissions
2. ✅ **Short Expiration** - Max 90 days for production keys
3. ✅ **Monitor Usage** - Alert on unusual activity
4. ✅ **Rotate Regularly** - Refresh keys quarterly
5. ✅ **Revoke Unused** - Delete inactive keys
6. ❌ **Never share keys** - One key per application
7. ❌ **Never commit** - Use environment variables

### WebSocket Security

1. ✅ **Authentication Required** - Only authenticated users connect
2. ✅ **Validate Events** - Verify user has permission for events
3. ✅ **Rate Limit** - Prevent event flooding
4. ✅ **Use WSS** - Secure WebSocket in production
5. ❌ **Don't broadcast sensitive data** - Filter based on permissions

### General Security

1. ✅ **Regular Audits** - Review audit logs weekly
2. ✅ **Update Dependencies** - Keep libraries up to date
3. ✅ **Monitor Errors** - Check logs for security issues
4. ✅ **Backup Configuration** - Export settings regularly
5. ✅ **Test Recovery** - Verify backups can be restored

---

## FAQ

### General

**Q: How do I know if communication features are working?**
A: Check the System Health dashboard - all services should show "operational".

**Q: Can I use multiple email providers?**
A: Currently, one SMTP provider at a time. Switch providers in Settings → Email.

**Q: Are there rate limits?**
A: Yes - 100 emails/hour, 1000 webhooks/hour, 10000 API requests/hour (configurable).

### SMTP Email

**Q: Why aren't emails sending?**
A: Check: 1) SMTP settings correct, 2) Scheduler running, 3) Email queue not stuck, 4) Recipient emails valid.

**Q: Can I use Outlook/Office365?**
A: Yes. Use `smtp.office365.com`, port `587`, enable TLS.

**Q: How do I customize email templates?**
A: Edit templates directly in the `email_templates` database table.

**Q: What's the email sending limit?**
A: Depends on your SMTP provider. Gmail free: 500/day, G Suite: 2000/day.

### Webhooks

**Q: What happens if my endpoint is down?**
A: System retries 3 times with exponential backoff, then marks as failed.

**Q: Can I test webhooks without a public URL?**
A: Yes! Use [webhook.site](https://webhook.site) for testing.

**Q: How do I debug webhook delivery?**
A: Check delivery logs - shows request/response details and errors.

**Q: Can multiple webhooks subscribe to same event?**
A: Yes! All subscribed webhooks receive the event.

### API Keys

**Q: I lost my API key, can I recover it?**
A: No. API keys are hashed and cannot be recovered. Create a new one and revoke the old.

**Q: Can I have unlimited API keys?**
A: No limit per se, but recommended max 10 active keys per environment.

**Q: How do I know which key is being used?**
A: Check API key logs - shows all requests with timestamps and endpoints.

**Q: What's the difference between `inventory:*` and `inventory:read` + `inventory:write`?**
A: `inventory:*` includes delete permissions. Specific scopes exclude delete.

### WebSocket

**Q: Do I need to configure WebSocket?**
A: No, it works automatically once users log in.

**Q: Why does WebSocket keep disconnecting?**
A: Check: 1) Network stability, 2) Reverse proxy timeout settings, 3) Server logs for errors.

**Q: Can I disable WebSocket?**
A: Yes, set `WEBSOCKET_ENABLED=false` in environment config.

**Q: Does WebSocket work on mobile?**
A: Yes, all modern mobile browsers support WebSocket.

---

## Appendix: Quick Reference

### Email Configuration (Gmail)

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
FROM_EMAIL=notifications@yourfarm.com
FROM_NAME=Marketplace ERP Tools
USE_TLS=true
```

### Common SMTP Providers

| Provider | Host | Port | TLS |
|----------|------|------|-----|
| Gmail | smtp.gmail.com | 587 | Yes |
| Outlook | smtp.office365.com | 587 | Yes |
| SendGrid | smtp.sendgrid.net | 587 | Yes |
| Mailgun | smtp.mailgun.org | 587 | Yes |
| Amazon SES | email-smtp.us-east-1.amazonaws.com | 587 | Yes |

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/email/test` | POST | Send test email |
| `/api/v1/webhooks` | GET | List webhooks |
| `/api/v1/webhooks` | POST | Create webhook |
| `/api/v1/webhooks/{id}/test` | POST | Test webhook |
| `/api/v1/api-keys` | GET | List API keys |
| `/api/v1/api-keys` | POST | Create API key |
| `/api/v1/settings` | GET | Get settings |
| `/api/v1/settings` | PUT | Update settings |

---

**Document Version History:**

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-23 | Initial admin guide created |

---

**Need Help?**

- 📧 Email: support@yourfarm.com
- 📚 Developer Guide: See `developer-guide-communication.md`
- 🧪 Testing Guide: See `integration-testing-guide.md`

---

*End of Administrator Guide*
