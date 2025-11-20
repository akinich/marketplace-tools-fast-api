# Telegram Notifications Module

**Version:** 1.0.0
**Last Updated:** 2025-11-20
**Status:** Production Ready ✅

## Overview

The Telegram Notifications Module provides real-time messaging capabilities to your Farm Management System through Telegram Bot API integration. It sends automated notifications for tickets, purchase orders, and inventory alerts to designated Telegram channels, ensuring your team stays informed about critical events as they happen.

### Key Capabilities

- **Multi-Channel Notifications** - Separate channels for tickets, purchase orders, and inventory
- **Ticket Lifecycle Notifications** - Alerts for creation, updates, comments, priority changes, and closure
- **Purchase Order Notifications** - Real-time updates on PO creation and status changes
- **Intelligent Low Stock Alerts** - First alert + daily summaries until items are restocked
- **User Account Linking** - Connect Telegram accounts for future personal DMs
- **Admin Configuration Interface** - Easy-to-use settings page with test functionality
- **Bot Health Monitoring** - Real-time status indicator and error tracking
- **Non-Blocking Architecture** - Notifications don't impact application performance
- **Auto-Resolution** - Low stock alerts resolve automatically when items are restocked

## Quick Start

### Prerequisites

- PostgreSQL database (>= 12)
- Python 3.8+ with `python-telegram-bot` library
- Telegram account
- Farm Management System core installed
- Active Telegram bot (created via @BotFather)

### Installation

#### 1. Run Database Migration

```bash
cd backend
python run_migration.py migrations/telegram_notifications_v1.0.0.sql
```

This creates:
- `notification_settings` table (bot configuration)
- `telegram_link_codes` table (user linking)
- `low_stock_notifications` table (alert tracking)
- `user_profiles.telegram_chat_id` column (personal DM support)

#### 2. Install Python Dependencies

```bash
pip install python-telegram-bot==20.8
```

Or update from requirements.txt:
```bash
pip install -r requirements.txt
```

#### 3. Create Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Choose bot name: `Farm Notifications Bot`
4. Choose username: `farm_notify_bot` (must be unique)
5. Copy the bot token provided

#### 4. Configure Environment

Add the bot token to your `.env` file:
```bash
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
```

#### 5. Create Telegram Channels

1. Create 3 Telegram channels (or groups):
   - **Farm Tickets** (for ticket notifications)
   - **Farm Purchase Orders** (for PO notifications)
   - **Farm Inventory Alerts** (for low stock alerts)

2. Add your bot as administrator to each channel:
   - Channel Settings → Administrators → Add Administrator
   - Search for your bot username
   - Grant "Post Messages" permission

3. Get Channel IDs:
   - Forward a message from the channel to `@userinfobot`
   - Note the channel ID (e.g., `-1001234567890`)
   - Channel IDs are always negative numbers

#### 6. Configure Settings

Navigate to `/admin/telegram` in your application and:
- Enter channel IDs for each notification type
- Enable notifications for desired modules
- Click "Test" buttons to verify connectivity
- Save settings

#### 7. Verify Setup

Create a test ticket or purchase order and confirm the notification appears in your Telegram channel!

## Module Structure

```
telegram/
├── Settings Dashboard     # Admin configuration interface
│   ├── Bot Status        # Health monitoring with real-time indicator
│   ├── Channel Config    # Channel IDs and enable/disable toggles
│   ├── Test Functions    # Send test notifications per channel
│   └── User Linking      # Personal DM account linking
├── Ticket Notifications
│   ├── Created           # New ticket alerts
│   ├── Updated           # Status/priority/field changes
│   ├── Commented         # New comment alerts
│   └── Closed            # Ticket closure notifications
├── Purchase Order Notifications
│   ├── Created           # New PO with details
│   └── Status Changed    # PO status updates (received/cancelled)
└── Inventory Notifications
    ├── First Alert       # Immediate alert when item goes low stock
    └── Daily Summary     # 9 AM recap of all low stock items
```

## Core Concepts

### Notification Channels

A **notification channel** is a Telegram channel or group where the bot posts messages. Each module has its dedicated channel:

- **Tickets Channel:** Receives all ticket-related notifications
- **PO Channel:** Receives purchase order updates
- **Inventory Channel:** Receives low stock alerts and summaries

**Channel ID Format:**
```
-1001234567890  (Always negative for channels/groups)
```

**Example Configuration:**
```javascript
{
  tickets_channel_id: -1001234567890,
  po_channel_id: -1001234567891,
  inventory_channel_id: -1001234567892,
  enable_ticket_notifications: true,
  enable_po_notifications: true,
  enable_inventory_notifications: true
}
```

### Notification Types

#### Ticket Notifications

**1. Ticket Created**
```
🎫 New Ticket Created
━━━━━━━━━━━━━━━━
Title: Database connection timeout
Type: Issue
Created by: John Doe
Status: Open
Priority: Not set

📝 Description:
The database connection times out after 30 seconds...

Ticket ID: #123
```

**2. Ticket Updated**
```
🔄 Ticket Updated
━━━━━━━━━━━━━━━━
Ticket: Database connection timeout
Updated fields: status, priority
Status: In Progress
Priority: High

Ticket ID: #123
```

**3. Priority Changed**
```
⚠️ Ticket Priority Changed
━━━━━━━━━━━━━━━━
Ticket: Database connection timeout
Old Priority: Medium
New Priority: 🔴 CRITICAL

Ticket ID: #123
```

**4. Comment Added**
```
💬 New Comment on Ticket
━━━━━━━━━━━━━━━━
Ticket: Database connection timeout
Commented by: Jane Smith

Comment:
I've increased the connection pool size...

Ticket ID: #123
```

**5. Ticket Closed**
```
✅ Ticket Closed
━━━━━━━━━━━━━━━━
Title: Database connection timeout
Closed by: Admin User
Created by: John Doe

Ticket ID: #123
```

#### Purchase Order Notifications

**1. PO Created**
```
📦 Purchase Order Created
━━━━━━━━━━━━━━━━
PO Number: PO-2025-001
Supplier: ABC Supplies Ltd
PO Date: 2025-11-20
Expected Delivery: 2025-11-25
Total Cost: $1,250.00

Items: 3 item(s)
Status: Pending

PO ID: #45
```

**2. PO Status Changed**
```
🔄 Purchase Order Status Changed
━━━━━━━━━━━━━━━━
PO Number: PO-2025-001
Supplier: ABC Supplies Ltd
Old Status: 🕐 Pending
New Status: ✅ Received
Total Cost: $1,250.00

PO ID: #45
```

#### Inventory Notifications

**1. Low Stock First Alert**
```
⚠️ Low Stock Alert
━━━━━━━━━━━━━━━━
Item: Fish Feed Premium
Category: Feed
Current Quantity: 5 kg
Reorder Threshold: 10 kg
Deficit: 5 kg

Supplier: Feed Corp

Action Required: Restock this item
```

**2. Daily Summary (9 AM)**
```
📊 Daily Low Stock Summary
━━━━━━━━━━━━━━━━
Date: 2025-11-20
Total Low Stock Items: 7

Items Needing Restock:
• Fish Feed Premium: 5/10 kg (deficit: 5 kg)
• Water Treatment Powder: 2/15 kg (deficit: 13 kg)
• Probiotics Mix: 8/20 L (deficit: 12 L)
• Oxygen Tablets: 3/25 pieces (deficit: 22 pieces)
...and 3 more items

⚠️ Action Required: Review and place purchase orders
```

### Low Stock Alert Logic

The system uses a **smart alerting strategy** to prevent notification spam while keeping you informed:

#### Phase 1: First Alert
- **Trigger:** Item drops to or below `reorder_threshold`
- **Frequency:** Once per incident
- **Action:** Immediate notification sent to inventory channel
- **Tracking:** Records alert in `low_stock_notifications` table

#### Phase 2: Daily Summary
- **Trigger:** Daily at 9:00 AM
- **Frequency:** Once per day while items remain low
- **Content:** Summary of ALL currently low stock items
- **Purpose:** Persistent reminder without spam

#### Phase 3: Auto-Resolution
- **Trigger:** Item restocked above `reorder_threshold`
- **Action:** Alert marked as resolved automatically
- **Result:** No more notifications for that item until it goes low again

**Example Timeline:**
```
Monday 10:00 AM  - Item drops to 5kg (threshold: 10kg)
                   → First Alert sent immediately ⚠️

Tuesday 9:00 AM  - Daily Summary includes this item 📊
Wednesday 9:00 AM - Daily Summary includes this item 📊
Thursday 9:00 AM - Daily Summary includes this item 📊

Thursday 2:00 PM - Item restocked to 50kg
                   → Alert auto-resolved ✅

Friday 9:00 AM   - Item NOT in daily summary (resolved)
```

### User Account Linking

**User linking** enables future personal DM notifications. The system uses a secure one-time code approach:

#### How It Works

1. **Code Generation**
   - User clicks "Link Telegram Account" in frontend
   - System generates unique code: `LINK-A8F3`
   - Code expires in 15 minutes

2. **Telegram Verification**
   - User opens Telegram
   - Sends `/start LINK-A8F3` to the bot
   - Bot verifies code and links account

3. **Account Linked**
   - `telegram_chat_id` saved to user profile
   - User can now receive personal DMs (when enabled)

4. **Future Use**
   - When personal notifications are enabled
   - User receives DMs for their own tickets/POs
   - Central channels still receive all notifications

**Security Features:**
- 15-minute expiration
- One-time use only
- Cannot link to multiple accounts simultaneously
- Secure verification process

### Bot Health Monitoring

The system continuously monitors bot connectivity:

**Status Indicators:**
- 🟢 **Active:** Bot connected and operational
- 🔴 **Inactive:** Bot not initialized or token missing
- 🔴 **Error:** Bot has errors (check error message)

**Health Check Process:**
1. Auto-refresh every 30 seconds
2. Verifies bot token validity
3. Checks Telegram API connectivity
4. Updates status in database
5. Displays in admin interface

**Manual Refresh:**
Click the refresh icon in the admin interface to check status immediately.

## Architecture Overview

### Backend Components

```
Backend
├── services/telegram_service.py
│   ├── Bot initialization & health checks
│   ├── Message formatting & sending
│   ├── Settings management
│   ├── User account linking
│   └── Notification handlers (tickets/PO/inventory)
│
├── routes/telegram.py
│   ├── GET  /telegram/settings (admin)
│   ├── PUT  /telegram/settings (admin)
│   ├── GET  /telegram/status (admin)
│   ├── POST /telegram/test (admin)
│   ├── POST /telegram/link/create (user)
│   ├── GET  /telegram/link/status (user)
│   └── POST /telegram/link/unlink (user)
│
├── schemas/telegram.py
│   ├── Request schemas (settings, test, linking)
│   └── Response schemas (status, settings, codes)
│
├── scheduler.py
│   ├── Hourly: check_low_stock_first_alerts()
│   └── Daily 9 AM: send_low_stock_daily_summary()
│
└── Database
    ├── notification_settings (config storage)
    ├── telegram_link_codes (user linking)
    ├── low_stock_notifications (alert history)
    └── user_profiles.telegram_chat_id (personal DMs)
```

### Frontend Components

```
Frontend
├── pages/TelegramSettings.jsx
│   ├── Bot Status Card (health indicator)
│   ├── Channel Configuration (3 channels)
│   ├── Enable/Disable Toggles (per module)
│   ├── Test Notification Buttons
│   ├── Personal Notifications (user linking)
│   └── Setup Instructions
│
└── api/index.js
    └── telegramAPI (all endpoints)
```

### Integration Points

The module integrates with existing services:

**Tickets Service:**
```python
# In tickets_service.py
async def create_ticket(...):
    ticket = await get_ticket_by_id(ticket_id)
    asyncio.create_task(telegram_service.notify_ticket_created(ticket))
    return ticket
```

**Inventory Service:**
```python
# In inventory_service.py
async def create_purchase_order(...):
    po = await fetch_one(...)
    asyncio.create_task(telegram_service.notify_po_created(po))
    return po
```

**Scheduler:**
```python
# In scheduler.py
scheduler.add_job(
    check_low_stock_first_alerts,
    trigger=IntervalTrigger(hours=1),
    max_instances=1
)
```

## Configuration Reference

### Environment Variables

```bash
# Required
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Optional (defaults shown)
LOG_LEVEL=INFO
```

### Database Settings

Stored in `notification_settings` table:

```sql
-- Channel IDs (bigint)
tickets_channel_id: -1001234567890
po_channel_id: -1001234567891
inventory_channel_id: -1001234567892

-- Enable/Disable Toggles (boolean)
enable_ticket_notifications: true
enable_po_notifications: true
enable_inventory_notifications: true
enable_personal_notifications: false  -- Future feature

-- Bot Status (string)
bot_status: 'active'  -- 'active', 'inactive', 'error'
last_health_check: '2025-11-20T10:30:00Z'
last_error: null
```

### Admin Access

Access the configuration interface:
```
URL: /admin/telegram
Required Role: Admin
Permissions: Full access to all settings
```

## Usage Examples

### Example 1: Ticket Workflow

**Scenario:** Developer reports a bug

```
1. Developer creates ticket:
   Title: "Login page not loading"
   Type: Issue
   Description: "Users unable to access login page"

   → Notification sent to #tickets channel ✅

2. Admin sets priority to "High"

   → Priority change notification sent ✅

3. Developer comments:
   "It's affecting all mobile users"

   → Comment notification sent ✅

4. Admin closes ticket with comment:
   "Fixed in production deployment"

   → Ticket closed notification sent ✅
```

**Result:** Team informed at every step of the ticket lifecycle.

### Example 2: Purchase Order Workflow

**Scenario:** Manager creates PO for feed

```
1. Manager creates PO:
   PO Number: PO-2025-045
   Supplier: Premium Feed Corp
   Items: 500kg Fish Feed Premium @ $5/kg
   Total: $2,500
   Expected: 2025-11-25

   → PO created notification sent to #purchase-orders ✅

2. Supplier ships order (3 days later)

   (No notification - manual tracking)

3. Warehouse receives shipment
   Admin updates PO status to "Received"

   → Status change notification sent ✅
```

**Result:** Procurement team and stakeholders notified of PO lifecycle events.

### Example 3: Low Stock Management

**Scenario:** Fish feed inventory drops below threshold

```
Monday 10:30 AM:
  Fish Feed Premium drops to 45kg (threshold: 50kg)
  → First Alert sent immediately to #inventory ⚠️

  Manager acknowledges but cannot order yet (budget approval pending)

Tuesday 9:00 AM:
  Daily Summary includes Fish Feed Premium 📊
  Still 45kg, still below threshold

Wednesday 9:00 AM:
  Daily Summary includes Fish Feed Premium 📊

  Later that day: Budget approved
  Manager creates PO-2025-046 for 500kg feed
  → PO created notification sent to #purchase-orders ✅

Friday (shipment arrives):
  Warehouse adds 500kg to inventory
  Fish Feed Premium now at 545kg (above 50kg threshold)
  → Alert auto-resolved ✅

Saturday 9:00 AM:
  Daily Summary does NOT include Fish Feed Premium
  (No longer low stock)
```

**Result:** Continuous visibility until issue resolved, without notification spam.

## Best Practices

### Channel Organization

✅ **Do:**
- Create separate channels for different notification types
- Use descriptive channel names (`Farm Tickets`, not `Channel 1`)
- Add relevant team members to appropriate channels
- Pin important messages (e.g., emergency procedures)
- Mute channels during off-hours if desired

❌ **Don't:**
- Mix notification types in one channel (hard to filter)
- Use personal chats for team notifications (not scalable)
- Forget to add bot as admin (notifications will fail)
- Share bot token publicly (security risk)

### Notification Management

✅ **Do:**
- Test notifications after initial setup
- Regularly review low stock thresholds
- Adjust daily summary time to match team schedule
- Enable only notifications your team needs
- Use test function before changing channel IDs

❌ **Don't:**
- Set all thresholds too high (alert fatigue)
- Disable all notifications (defeats purpose)
- Ignore test failures (indicates misconfiguration)
- Forget to update channel IDs after channel changes

### Bot Security

✅ **Do:**
- Keep bot token in `.env` file (never commit to git)
- Restrict admin access to trusted users only
- Regularly check bot status for errors
- Use proper channel permissions

❌ **Don't:**
- Share bot token in chat messages or documents
- Give bot admin rights beyond "Post Messages"
- Ignore bot status errors for extended periods
- Hard-code bot token in source code

## Troubleshooting

### Bot Status Shows "Error"

**Symptoms:**
- Red indicator in admin interface
- Error message displayed
- Test notifications fail

**Causes & Solutions:**

1. **Invalid Bot Token**
   ```
   Error: "Bot token is invalid or revoked"

   Solution:
   - Verify TELEGRAM_BOT_TOKEN in .env
   - Check for typos or extra spaces
   - Regenerate token via @BotFather if needed
   ```

2. **Network Issues**
   ```
   Error: "Telegram API error: Connection timeout"

   Solution:
   - Check internet connectivity
   - Verify firewall allows HTTPS to api.telegram.org
   - Check proxy settings if behind corporate firewall
   ```

3. **Bot Deleted**
   ```
   Error: "Unauthorized: bot was stopped by user"

   Solution:
   - Bot may have been deleted in Telegram
   - Create new bot via @BotFather
   - Update TELEGRAM_BOT_TOKEN
   ```

### Notifications Not Received

**Symptoms:**
- Bot status shows "Active"
- No error messages
- Notifications not appearing in channel

**Causes & Solutions:**

1. **Bot Not Admin in Channel**
   ```
   Solution:
   - Go to channel settings
   - Administrators → Add Administrator
   - Search for your bot
   - Grant "Post Messages" permission
   ```

2. **Wrong Channel ID**
   ```
   Solution:
   - Forward message from channel to @userinfobot
   - Copy correct channel ID (should be negative)
   - Update in /admin/telegram settings
   - Click "Test" to verify
   ```

3. **Notifications Disabled**
   ```
   Solution:
   - Check /admin/telegram settings
   - Ensure module toggle is ON (green)
   - Verify channel ID is configured
   - Save settings
   ```

### Daily Summary Not Sending

**Symptoms:**
- Hourly alerts work fine
- No daily summary at 9 AM

**Causes & Solutions:**

1. **No Low Stock Items**
   ```
   This is normal behavior
   Daily summary only sends if items are below threshold
   ```

2. **Scheduler Not Running**
   ```
   Check: GET /health endpoint
   Look for: scheduled_jobs array
   Should include: "low_stock_daily_summary"

   Solution:
   - Restart backend server
   - Check logs for scheduler errors
   ```

3. **Timezone Issue**
   ```
   Daily summary runs at 9 AM server time

   Solution:
   - Check server timezone: date
   - Adjust cron trigger in scheduler.py if needed
   ```

### Test Notification Fails

**Symptoms:**
- Click "Test" button
- Receive error message
- No message in channel

**Causes & Solutions:**

1. **Channel Not Configured**
   ```
   Error: "Channel ID not configured"

   Solution:
   - Enter channel ID in settings
   - Save settings
   - Try test again
   ```

2. **Bot Not in Channel**
   ```
   Error: "Chat not found"

   Solution:
   - Verify bot is added to channel
   - Check bot has admin rights
   - Verify channel ID is correct (negative number)
   ```

## Performance Considerations

### Non-Blocking Architecture

All Telegram notifications use `asyncio.create_task()` to send messages asynchronously:

```python
# Notifications don't block the main operation
ticket = await create_ticket_in_db(...)
asyncio.create_task(telegram_service.notify_ticket_created(ticket))
return ticket  # Returns immediately, notification sends in background
```

**Benefits:**
- API responses remain fast (~50-100ms)
- Telegram failures don't break app functionality
- Multiple notifications can send concurrently

### Resource Usage

**Database Queries:**
- Settings fetched once, cached for 30 seconds
- Low stock check runs hourly (minimal impact)
- Alert tracking adds 1 insert per notification

**Network Traffic:**
- Average message size: ~500 bytes
- Typical daily volume: 20-50 notifications
- Bandwidth: <5 KB/day (negligible)

**Memory:**
- Bot instance: ~5 MB RAM
- Message queue: ~1 MB per 100 pending messages
- Total overhead: <10 MB

### Scaling Considerations

**Current Limits:**
- Telegram Bot API: 30 messages/second
- Module handles: ~100 notifications/hour easily
- Database can store: Millions of notification records

**If Scaling Needed:**
- Implement message batching
- Use message queue (Redis/RabbitMQ)
- Shard by notification type

## API Reference

See [technical-guide.md](./technical-guide.md) for complete API documentation.

## User Guide

See [user-guide.md](./user-guide.md) for end-user instructions and workflows.

## FAQ

**Q: Can I use existing Telegram channels?**
A: Yes! You can use any channel or group. Just add the bot as admin and use that channel's ID.

**Q: Do users need Telegram accounts?**
A: No. Only admins need to configure the bot. Channel members just receive notifications.

**Q: Can I customize notification messages?**
A: Currently no. Messages use predefined templates. Custom templates may be added in future versions.

**Q: What happens if Telegram is down?**
A: Notifications fail silently. Your app continues working normally. Bot status shows error.

**Q: Can I send notifications to multiple channels?**
A: Currently one channel per module. You can manually forward messages or use Telegram's channel forwarding.

**Q: Is there a notification history?**
A: Not currently. Consider enabling Telegram's message history in channel settings.

**Q: Can I disable specific notification types?**
A: Yes! Use the module toggles in /admin/telegram to enable/disable per module.

**Q: How do I change bot name or username?**
A: Use @BotFather's `/mybots` command. This doesn't affect functionality.

## Support & Resources

- **Technical Documentation:** [technical-guide.md](./technical-guide.md)
- **User Guide:** [user-guide.md](./user-guide.md)
- **Backend Code:** `backend/app/services/telegram_service.py`
- **Frontend Code:** `frontend/src/pages/TelegramSettings.jsx`
- **Database Schema:** `backend/migrations/telegram_notifications_v1.0.0.sql`

## Version History

### v1.0.0 (2025-11-20)
- Initial release
- Multi-channel notification support
- Ticket lifecycle notifications
- Purchase order notifications
- Intelligent low stock alerting
- User account linking infrastructure
- Admin configuration interface
- Bot health monitoring
- Scheduled jobs (hourly + daily)
- Complete documentation

---

**Need Help?** Check the [technical-guide.md](./technical-guide.md) for detailed API documentation or [user-guide.md](./user-guide.md) for step-by-step instructions.
