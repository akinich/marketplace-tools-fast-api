# Communication Features - User Guide

**Version:** 1.0.0
**Last Updated:** 2025-11-23
**Audience:** End Users

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Email Notifications](#email-notifications)
3. [Real-time Updates](#real-time-updates)
4. [Telegram Notifications](#telegram-notifications)
5. [API Keys (Advanced)](#api-keys-advanced)
6. [Notification Settings](#notification-settings)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

---

## Overview

The Farm Management System keeps you informed through multiple communication channels:

| Feature | What It Does | When You'll See It |
|---------|-------------|-------------------|
| 📧 **Email Notifications** | Important updates sent to your email | Ticket assignments, low stock, system alerts |
| ⚡ **Real-time Updates** | Instant updates without page refresh | Dashboard changes, new tickets, notifications |
| 📱 **Telegram Notifications** | Messages to your Telegram app | Critical alerts, urgent tickets |
| 🔑 **API Keys** | For developers/automation | When integrating with external tools |

---

## Email Notifications

### What Emails Will I Receive?

You'll automatically receive emails for:

#### Ticket Notifications
- **New ticket assigned to you**: When a ticket is assigned to you
- **Ticket status changed**: When ticket status updates
- **New comments**: When someone comments on your ticket
- **Priority changed**: When ticket priority is escalated

#### Inventory Alerts
- **Low stock warnings**: When items drop below minimum level
- **Out of stock**: When critical items run out
- **Reorder reminders**: When it's time to restock

#### Account Notifications
- **Welcome email**: When your account is created
- **Password reset**: When you request password change
- **Security alerts**: Login from new device/location

#### System Notifications
- **Maintenance windows**: Scheduled downtime
- **Feature updates**: New features available
- **Important announcements**: From administrators

### Email Format

Emails include:
- **Clear subject line**: What the email is about
- **Summary**: Quick overview at the top
- **Details**: All relevant information
- **Action buttons**: Direct links to tickets, items, etc.
- **Timestamp**: When the event occurred

**Example Email:**

```
Subject: [CRITICAL] New Ticket Assigned: Broken Water Pump

Hi John Doe,

A critical priority ticket has been assigned to you:

┌─────────────────────────────────────┐
│ Title: Broken Water Pump            │
│ Priority: CRITICAL                  │
│ Category: Equipment                 │
│ Created: 2025-11-23 10:30 AM        │
│ Created By: Jane Smith              │
└─────────────────────────────────────┘

Description:
The main water pump in Pond A has stopped working.
Immediate attention required.

[View Ticket] [Add Comment]

---
Farm Management System
© 2025 All Rights Reserved
```

### Managing Email Notifications

#### Change Your Email Address

1. Click your **profile icon** (top right)
2. Select **"Profile Settings"**
3. Update **"Email Address"**
4. Click **"Save Changes"**
5. Verify the new email (check inbox)

#### Turn Email Notifications On/Off

1. Go to **Profile → Notification Preferences**
2. Toggle categories:
   - ☑️ Ticket notifications
   - ☑️ Inventory alerts
   - ☑️ System announcements
   - ☐ Weekly summary email
3. Click **"Save Preferences"**

> **Note:** Critical security emails cannot be disabled (password resets, login alerts).

### Email Delivery

- **Delivery time**: Within 5 minutes
- **Retry**: If delivery fails, system retries automatically
- **Spam folder**: Check spam if emails don't arrive
- **Unsubscribe**: Use link at bottom of emails (for non-critical notifications)

---

## Real-time Updates

### What Are Real-time Updates?

Real-time updates mean you see changes **instantly** without refreshing the page.

### Features with Real-time Updates

#### 1. Dashboard Metrics
**What updates:** All dashboard statistics
**How often:** Every 30 seconds
**What you see:** Numbers change automatically

Example:
```
Active Tickets: 12 → 13 (someone created a ticket)
Low Stock Items: 3 → 2 (item was restocked)
```

#### 2. Ticket Notifications
**What updates:** New tickets, status changes, comments
**How often:** Instantly
**What you see:** Toast notification in top-right corner

Example:
```
┌─────────────────────────────────────┐
│ 🎫 New Ticket Created               │
│ "Fix fence in Sector B"             │
│ Priority: Medium                    │
│                          [View] [×] │
└─────────────────────────────────────┘
```

#### 3. Inventory Alerts
**What updates:** Stock level changes
**How often:** Instantly
**What you see:** Alert badge + notification

Example:
```
🔔 Low Stock Alert
Fish Feed (Pellets) is below minimum level
Current: 45kg | Minimum: 50kg
[Reorder Now]
```

#### 4. User Presence
**What updates:** Who's online
**How often:** Instantly
**What you see:** Green dot next to user names

Example:
```
👤 John Doe    🟢 Online
👤 Jane Smith  ⚪ Offline
👤 Bob Wilson  🟢 Online
```

### Connection Status

Look for the connection indicator in the top-right corner:

- 🟢 **Green dot**: Connected - real-time updates active
- 🟡 **Yellow dot**: Connecting - attempting to reconnect
- 🔴 **Red dot**: Disconnected - updates paused (page will auto-reconnect)

### How It Works

1. **You log in** → Connection established automatically
2. **Event happens** → Server sends update to you
3. **You see update** → No need to refresh page

**Behind the scenes:** Uses WebSocket technology for instant bidirectional communication.

### Troubleshooting Real-time Updates

**Updates not appearing?**

1. Check connection status (top-right corner)
2. If red/yellow, wait 30 seconds for reconnection
3. If still not working, refresh the page
4. Check your internet connection

**Too many notifications?**

1. Go to **Profile → Notification Preferences**
2. Disable specific notification types
3. Set "Do Not Disturb" mode

---

## Telegram Notifications

### Setting Up Telegram Notifications

#### Step 1: Find the Bot

1. Open Telegram app
2. Search for: **@YourFarmBot** (ask admin for bot name)
3. Click **"Start"** to activate

#### Step 2: Link Your Account

1. In Farm Management System, go to **Profile → Integrations**
2. Click **"Connect Telegram"**
3. Copy the code shown (e.g., `LINK-ABC123`)
4. In Telegram, send the code to the bot:
   ```
   /link LINK-ABC123
   ```
5. Bot confirms: ✅ "Account linked successfully!"

#### Step 3: Configure Notifications

In Telegram, send commands to the bot:

```
/settings - View current settings
/enable tickets - Enable ticket notifications
/disable inventory - Disable inventory alerts
/help - See all commands
```

### What Notifications You'll Get

#### Critical Alerts (Always Sent)
- 🔴 Critical priority tickets
- 🔴 System down/errors
- 🔴 Security alerts

#### Optional Notifications
- 🎫 All ticket updates
- 📦 Inventory low stock
- 📊 Daily summary report
- 👥 User activity

### Telegram Commands

| Command | What It Does |
|---------|-------------|
| `/start` | Activate the bot |
| `/link <code>` | Link your account |
| `/unlink` | Disconnect account |
| `/settings` | View notification preferences |
| `/enable <type>` | Turn on notification type |
| `/disable <type>` | Turn off notification type |
| `/status` | Check system status |
| `/help` | Show all commands |

### Sample Telegram Message

```
🔴 CRITICAL TICKET #127

Title: Water Quality Issue - Pond C
Priority: Critical
Created: Just now
Assigned: You

Description:
pH levels dropping rapidly in Pond C.
Immediate action needed.

[View Ticket]
```

---

## API Keys (Advanced)

> **Note:** This section is for advanced users who need programmatic access to the system.

### What Are API Keys?

API keys let you access the Farm Management System from:
- Custom scripts
- Mobile apps
- External tools
- Automation workflows

Think of it as a "robot password" that lets programs use your account.

### When to Use API Keys

**Good Use Cases:**
- ✅ Automated data export scripts
- ✅ IoT sensor integration (submit readings automatically)
- ✅ Custom mobile app
- ✅ Integration with other farm software

**Not Recommended:**
- ❌ Regular manual access (just use the web interface)
- ❌ Sharing with other people (create separate accounts)

### Creating Your First API Key

1. Navigate to **Profile → API Keys**
2. Click **"Create API Key"**
3. Fill in the form:
   - **Name**: Descriptive name (e.g., "Sensor Integration Script")
   - **What it's for**: Brief description
   - **Permissions**: Select what this key can access
   - **Expires in**: How long until it stops working (1-365 days)
4. Click **"Create"**
5. **⚠️ IMPORTANT**: Copy the key immediately - you won't see it again!

**Example API Key:**
```
your-api-key-will-appear-here-copy-it-now
```

### Using Your API Key

Include the key in your requests:

**Python Example:**
```python
import requests

API_KEY = "your_api_key_here"
headers = {"X-API-Key": API_KEY}

# Get inventory data
response = requests.get(
    "https://your-farm.com/api/v1/inventory",
    headers=headers
)

items = response.json()
print(f"Found {len(items)} items")
```

**cURL Example:**
```bash
curl -H "X-API-Key: your_api_key_here" \
     https://your-farm.com/api/v1/inventory
```

**JavaScript Example:**
```javascript
const API_KEY = "your_api_key_here";

fetch("https://your-farm.com/api/v1/inventory", {
  headers: {
    "X-API-Key": API_KEY
  }
})
.then(res => res.json())
.then(data => console.log(data));
```

### API Key Permissions (Scopes)

Choose what your key can access:

| Permission | What It Allows | Example Use |
|------------|----------------|-------------|
| `inventory:read` | View inventory only | Reporting dashboard |
| `inventory:write` | Add/update inventory | IoT sensor updates |
| `tickets:read` | View tickets | Mobile app viewer |
| `tickets:write` | Create/update tickets | Automated ticket creation |
| `biofloc:write` | Submit biofloc readings | Sensor integration |

**Best Practice:** Grant only the permissions you need. Don't give `write` access if you only need to read.

### Managing API Keys

**View Your Keys:**
1. Go to **Profile → API Keys**
2. See list of all your keys
3. Check last used date

**View Usage:**
1. Click on a key
2. See recent activity:
   - When it was used
   - What endpoints were accessed
   - Any errors

**Revoke a Key:**
1. Find the key in the list
2. Click **"Delete"** icon
3. Confirm - key stops working immediately

### API Key Security

🔒 **Keep Your Keys Safe:**

1. ✅ **Store in environment variables**, not in code:
   ```bash
   # In .env file
   API_KEY=your_api_key_here
   ```

2. ✅ **Never commit to Git**:
   ```bash
   # In .gitignore
   .env
   *.key
   ```

3. ✅ **Rotate regularly**: Create new keys every 90 days

4. ✅ **Use separate keys**: One per script/app

5. ❌ **Never share**: Don't give your key to others

6. ❌ **Never post publicly**: Don't share in forums, Stack Overflow, etc.

**If Your Key Is Compromised:**
1. Go to **Profile → API Keys**
2. Delete the compromised key immediately
3. Create a new key
4. Update your scripts with the new key

### API Documentation

Full API documentation available at:
```
https://your-farm.com/docs
```

Or ask your administrator for the developer guide.

---

## Notification Settings

### Customizing Your Notifications

1. Click your **profile icon** (top right)
2. Select **"Notification Preferences"**
3. Configure:

#### Email Preferences
```
☑️ Ticket Notifications
   ☑️ Assigned to me
   ☑️ Status changes
   ☑️ New comments
   ☐ All tickets (admin only)

☑️ Inventory Alerts
   ☑️ Low stock warnings
   ☑️ Out of stock
   ☐ Restocking suggestions

☑️ System Notifications
   ☑️ Security alerts
   ☑️ Maintenance windows
   ☐ Feature announcements
```

#### Real-time Notification Preferences
```
☑️ Show toast notifications
☑️ Play sound
☑️ Desktop notifications (requires browser permission)
Sound: [Bell ▼]
Duration: [5 seconds ▼]
```

#### Telegram Preferences
```
☑️ Enable Telegram notifications
☑️ Critical tickets only
☐ All tickets
☐ Daily summary (9:00 AM)
```

### Quiet Hours (Do Not Disturb)

Set times when you don't want non-critical notifications:

```
Enable Quiet Hours: ☑️
From: [10:00 PM ▼]
To: [7:00 AM ▼]
Days: ☑️ Mon ☑️ Tue ☑️ Wed ☑️ Thu ☑️ Fri ☐ Sat ☐ Sun

During quiet hours:
☑️ Still send critical alerts
☐ Mute all notifications
☑️ Batch notifications (send summary when quiet hours end)
```

### Notification History

View all notifications you've received:

1. Click **bell icon** 🔔 (top right)
2. See recent notifications
3. Click **"View All"** for complete history
4. Filter by:
   - Type (tickets, inventory, system)
   - Date range
   - Read/unread

---

## Troubleshooting

### Email Issues

**Not receiving emails?**

1. ✅ Check spam/junk folder
2. ✅ Verify email address in profile is correct
3. ✅ Check notification preferences are enabled
4. ✅ Ask admin if email system is working
5. ✅ Try adding sender to contacts: `noreply@your-farm.com`

**Emails delayed?**

- Normal delay: Up to 5 minutes
- If > 30 minutes: Contact administrator

### Real-time Update Issues

**Not seeing live updates?**

1. ✅ Check connection indicator (should be green 🟢)
2. ✅ Refresh the page
3. ✅ Check internet connection
4. ✅ Try a different browser
5. ✅ Clear browser cache

**Connection keeps dropping?**

1. ✅ Check network stability
2. ✅ Disable VPN temporarily
3. ✅ Contact IT/admin if persistent

### Telegram Issues

**Bot not responding?**

1. ✅ Make sure you clicked "Start" in Telegram
2. ✅ Verify you sent the correct link code
3. ✅ Try `/unlink` then link again
4. ✅ Ask admin for new bot link code

**Not getting messages?**

1. ✅ Send `/settings` to check preferences
2. ✅ Make sure notification types are enabled
3. ✅ Check Telegram notification settings (app settings)

### API Key Issues

**Key not working?**

1. ✅ Check key hasn't expired
2. ✅ Verify key wasn't revoked
3. ✅ Make sure you copied the entire key
4. ✅ Check you have the right permissions

**Getting "403 Forbidden"?**

- Your key doesn't have permission for that action
- Create a new key with the required scope

---

## FAQ

### General

**Q: Do I need to configure anything?**
A: No! Email and real-time updates work automatically. Telegram and API keys are optional.

**Q: Can I turn off all notifications?**
A: You can disable most notifications, but critical security alerts always send.

**Q: Who can see my notifications?**
A: Only you. Notifications are private to your account.

### Email

**Q: Why am I getting so many emails?**
A: Go to Notification Preferences and disable categories you don't need.

**Q: Can I get a daily summary instead of individual emails?**
A: Yes! Enable "Daily Summary" in Notification Preferences.

**Q: How do I unsubscribe?**
A: Use the unsubscribe link at the bottom of emails, or disable in Notification Preferences.

### Real-time Updates

**Q: Do I need to do anything to enable real-time updates?**
A: No, they work automatically when you log in.

**Q: Will it drain my battery on mobile?**
A: No, WebSocket connections are very efficient and use minimal battery.

**Q: Does it work offline?**
A: No, you need an internet connection for real-time updates.

### Telegram

**Q: Do I need Telegram to use the system?**
A: No, it's completely optional. Email works without Telegram.

**Q: Can I use multiple Telegram accounts?**
A: No, one Telegram account per system account.

**Q: Is it secure?**
A: Yes, all messages are encrypted by Telegram, and bot uses secure authentication.

### API Keys

**Q: I lost my API key. Can I recover it?**
A: No. API keys cannot be recovered. Delete the old one and create a new key.

**Q: How many API keys can I have?**
A: Up to 10 active keys per account (contact admin for more).

**Q: Can I share my API key with a coworker?**
A: No, never share keys. Each person should create their own.

**Q: What happens when a key expires?**
A: It stops working immediately. Create a new key before expiration.

---

## Quick Tips

### 📧 Email
- Add `noreply@your-farm.com` to contacts to avoid spam
- Set up filters to organize farm emails into a folder
- Enable "Daily Summary" to reduce email volume

### ⚡ Real-time
- Keep browser tab open for live updates
- Green dot 🟢 = all good
- Enable desktop notifications for important alerts

### 📱 Telegram
- Use `/help` command to see all options
- Set up custom keywords for alerts
- Enable "Critical Only" mode to reduce noise

### 🔑 API Keys
- Use environment variables, never hardcode
- Rotate keys every 3 months
- Monitor usage logs for suspicious activity

---

## Getting Help

**Need assistance?**

1. **Check this guide** - Most questions answered here
2. **Ask your admin** - They can check system settings
3. **Contact support** - support@your-farm.com
4. **View tutorials** - Video guides available in Help Center

**Report a bug:**
- Go to **Help → Report Issue**
- Include screenshots if possible
- Describe what you expected vs. what happened

---

**Document Version History:**

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-23 | Initial user guide created |

---

*Happy Farming! 🌾*
