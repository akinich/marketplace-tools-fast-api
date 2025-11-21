"""
Telegram Notification Service
Version: 1.1.0
Created: 2025-11-20
Updated: 2025-11-21

Changelog:
----------
v1.1.0 (2025-11-21):
  - BREAKING: Replaced python-telegram-bot library with direct HTTP API calls
  - Uses httpx for async HTTP requests to Telegram Bot API
  - More reliable deployment on Render and other platforms
  - No external library dependency for Telegram functionality

v1.0.1 (2025-11-21):
  - Fix: Changed update_setting to accept Optional[str] for updated_by parameter
  - Fix: System-initiated updates now pass None instead of "system" string
  - Fix: Resolves UUID validation error in bot health checks

v1.0.0 (2025-11-20):
  - Initial telegram notification service
  - Bot initialization and health checks
  - Channel message sending for tickets, POs, inventory
  - User account linking with one-time codes
  - Settings management (get/update)
  - Notification formatting utilities
  - Error handling with status tracking

Description:
  Handles all Telegram bot operations including sending notifications,
  managing user links, and maintaining bot health status.
  Uses direct HTTP calls to Telegram Bot API via httpx.
"""

import logging
import secrets
import string
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal

from fastapi import HTTPException, status

from app.database import fetch_one, fetch_all, execute_query
from app.config import settings

logger = logging.getLogger(__name__)

# Telegram Bot API base URL
TELEGRAM_API_BASE = "https://api.telegram.org/bot"


# ============================================================================
# BOT INITIALIZATION
# ============================================================================

def get_bot_token() -> Optional[str]:
    """Get the bot token from settings"""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not configured")
        return None
    return token


def get_api_url(method: str) -> Optional[str]:
    """Get the full API URL for a Telegram method"""
    token = get_bot_token()
    if not token:
        return None
    return f"{TELEGRAM_API_BASE}{token}/{method}"


# ============================================================================
# SETTINGS MANAGEMENT
# ============================================================================

async def get_all_settings() -> Dict:
    """Get all notification settings"""
    settings_rows = await fetch_all(
        """
        SELECT setting_key, setting_value, setting_type, description, updated_at
        FROM notification_settings
        ORDER BY setting_key
        """
    )

    settings_dict = {}
    for row in settings_rows:
        key = row["setting_key"]
        value = row["setting_value"]
        setting_type = row["setting_type"]

        # Type casting
        if value is None:
            settings_dict[key] = None
        elif setting_type == "boolean":
            settings_dict[key] = value.lower() == "true"
        elif setting_type == "integer":
            settings_dict[key] = int(value)
        elif setting_type == "bigint":
            settings_dict[key] = int(value) if value else None
        else:
            settings_dict[key] = value

    return settings_dict


async def get_setting(setting_key: str) -> Optional[str]:
    """Get a single setting value"""
    result = await fetch_one(
        "SELECT setting_value FROM notification_settings WHERE setting_key = $1",
        setting_key
    )
    return result["setting_value"] if result else None


async def update_setting(setting_key: str, setting_value: str, updated_by: Optional[str]) -> bool:
    """Update a single setting"""
    await execute_query(
        """
        UPDATE notification_settings
        SET setting_value = $1, updated_by = $2, updated_at = NOW()
        WHERE setting_key = $3
        """,
        setting_value,
        updated_by,
        setting_key
    )
    return True


async def update_settings_bulk(updates: Dict, updated_by: str) -> Dict:
    """Update multiple settings at once"""
    for key, value in updates.items():
        # Convert value to string for storage
        if isinstance(value, bool):
            str_value = "true" if value else "false"
        elif value is None:
            str_value = None
        else:
            str_value = str(value)

        await update_setting(key, str_value, updated_by)

    # Update bot status
    await update_bot_status("active", None)

    return await get_all_settings()


# ============================================================================
# BOT HEALTH CHECK
# ============================================================================

async def check_bot_health() -> Dict:
    """Check if bot is operational using direct HTTP call"""
    api_url = get_api_url("getMe")

    if api_url is None:
        await update_bot_status("error", "Bot token not configured")
        return {
            "status": "error",
            "message": "Bot token not configured",
            "last_check": datetime.utcnow().isoformat()
        }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(api_url)
            data = response.json()

            if response.status_code == 200 and data.get("ok"):
                bot_info = data.get("result", {})
                await update_bot_status("active", None)

                return {
                    "status": "active",
                    "message": f"Bot @{bot_info.get('username', 'unknown')} is operational",
                    "bot_name": bot_info.get("first_name", "Unknown"),
                    "bot_username": bot_info.get("username", "unknown"),
                    "last_check": datetime.utcnow().isoformat()
                }
            elif response.status_code == 401:
                error_msg = "Bot token is invalid or revoked"
                await update_bot_status("error", error_msg)
                return {
                    "status": "error",
                    "message": error_msg,
                    "last_check": datetime.utcnow().isoformat()
                }
            else:
                error_msg = data.get("description", f"API error: {response.status_code}")
                await update_bot_status("error", error_msg)
                return {
                    "status": "error",
                    "message": error_msg,
                    "last_check": datetime.utcnow().isoformat()
                }

    except httpx.TimeoutException:
        error_msg = "Telegram API request timed out"
        await update_bot_status("error", error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "last_check": datetime.utcnow().isoformat()
        }

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        await update_bot_status("error", error_msg)
        logger.error(f"Bot health check failed: {e}")
        return {
            "status": "error",
            "message": error_msg,
            "last_check": datetime.utcnow().isoformat()
        }


async def update_bot_status(status: str, error_message: Optional[str]) -> None:
    """Update bot status in settings"""
    await update_setting("bot_status", status, None)
    await update_setting("last_health_check", datetime.utcnow().isoformat(), None)

    if error_message:
        await update_setting("last_error", error_message, None)


# ============================================================================
# MESSAGE SENDING
# ============================================================================

async def send_message(chat_id: int, message: str, parse_mode: str = "Markdown") -> bool:
    """Send message to a Telegram chat using direct HTTP call"""
    api_url = get_api_url("sendMessage")

    if api_url is None:
        logger.error("Cannot send message: Bot token not configured")
        return False

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": parse_mode
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            logger.info(f"Sending message to chat_id: {chat_id}")
            response = await client.post(api_url, json=payload)
            data = response.json()
            logger.info(f"Telegram API response: {data}")

            if response.status_code == 200 and data.get("ok"):
                logger.info(f"Message sent successfully to chat {chat_id}")
                return True
            elif response.status_code == 401:
                logger.error(f"Bot not authorized to send to chat {chat_id}")
                await update_bot_status("error", f"Unauthorized for chat {chat_id}")
                return False
            elif response.status_code == 400:
                error_desc = data.get("description", "Bad request")
                logger.error(f"Bad request sending to chat {chat_id}: {error_desc}")
                return False
            else:
                error_desc = data.get("description", f"API error: {response.status_code}")
                logger.error(f"Telegram error sending to chat {chat_id}: {error_desc}")
                await update_bot_status("error", error_desc)
                return False

    except httpx.TimeoutException:
        logger.error(f"Timeout sending message to chat {chat_id}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error sending message: {e}")
        return False


async def send_to_channel(channel_setting_key: str, message: str) -> bool:
    """Send message to configured channel"""
    # Check if notifications are enabled
    channel_id_str = await get_setting(channel_setting_key)

    if not channel_id_str:
        logger.warning(f"Channel not configured: {channel_setting_key}")
        return False

    try:
        channel_id = int(channel_id_str)
    except ValueError:
        logger.error(f"Invalid channel ID for {channel_setting_key}: {channel_id_str}")
        return False

    return await send_message(channel_id, message)


# ============================================================================
# TICKET NOTIFICATIONS
# ============================================================================

async def notify_ticket_created(ticket: Dict) -> bool:
    """Notify when a new ticket is created"""
    # Check channel-level toggle
    enabled = await get_setting("enable_ticket_notifications")
    if enabled != "true":
        return False
    # Check event-level toggle
    event_enabled = await get_setting("notify_ticket_created")
    if event_enabled == "false":
        return False

    message = f"""🎫 *New Ticket Created*
━━━━━━━━━━━━━━━━
*Title:* {ticket['title']}
*Type:* {ticket['ticket_type'].replace('_', ' ').title()}
*Created by:* {ticket['created_by_name']}
*Status:* {ticket['status'].replace('_', ' ').title()}
*Priority:* {ticket.get('priority') or 'Not set'}

📝 *Description:*
{ticket['description'][:200]}{"..." if len(ticket['description']) > 200 else ""}

*Ticket ID:* #{ticket['id']}
"""

    return await send_to_channel("tickets_channel_id", message)


async def notify_ticket_updated(ticket: Dict, updated_fields: List[str]) -> bool:
    """Notify when ticket is updated"""
    enabled = await get_setting("enable_ticket_notifications")
    if enabled != "true":
        return False
    event_enabled = await get_setting("notify_ticket_updated")
    if event_enabled == "false":
        return False

    fields_str = ", ".join(updated_fields)

    message = f"""🔄 *Ticket Updated*
━━━━━━━━━━━━━━━━
*Ticket:* {ticket['title']}
*Updated fields:* {fields_str}
*Status:* {ticket['status'].replace('_', ' ').title()}
*Priority:* {ticket.get('priority') or 'Not set'}

*Ticket ID:* #{ticket['id']}
"""

    return await send_to_channel("tickets_channel_id", message)


async def notify_ticket_closed(ticket: Dict, closed_by_name: str) -> bool:
    """Notify when ticket is closed"""
    enabled = await get_setting("enable_ticket_notifications")
    if enabled != "true":
        return False
    event_enabled = await get_setting("notify_ticket_closed")
    if event_enabled == "false":
        return False

    message = f"""✅ *Ticket Closed*
━━━━━━━━━━━━━━━━
*Title:* {ticket['title']}
*Closed by:* {closed_by_name}
*Created by:* {ticket['created_by_name']}

*Ticket ID:* #{ticket['id']}
"""

    return await send_to_channel("tickets_channel_id", message)


async def notify_ticket_comment(ticket: Dict, comment: str, commenter_name: str) -> bool:
    """Notify when a comment is added"""
    enabled = await get_setting("enable_ticket_notifications")
    if enabled != "true":
        return False
    event_enabled = await get_setting("notify_ticket_comment")
    if event_enabled == "false":
        return False

    message = f"""💬 *New Comment on Ticket*
━━━━━━━━━━━━━━━━
*Ticket:* {ticket['title']}
*Commented by:* {commenter_name}

*Comment:*
{comment[:300]}{"..." if len(comment) > 300 else ""}

*Ticket ID:* #{ticket['id']}
"""

    return await send_to_channel("tickets_channel_id", message)


async def notify_ticket_priority_changed(ticket: Dict, old_priority: Optional[str], new_priority: str) -> bool:
    """Notify when ticket priority changes"""
    enabled = await get_setting("enable_ticket_notifications")
    if enabled != "true":
        return False
    event_enabled = await get_setting("notify_ticket_priority_changed")
    if event_enabled == "false":
        return False

    priority_emoji = {
        "low": "🟢",
        "medium": "🟡",
        "high": "🟠",
        "critical": "🔴"
    }

    message = f"""⚠️ *Ticket Priority Changed*
━━━━━━━━━━━━━━━━
*Ticket:* {ticket['title']}
*Old Priority:* {old_priority or 'Not set'}
*New Priority:* {priority_emoji.get(new_priority, '')} {new_priority.upper()}

*Ticket ID:* #{ticket['id']}
"""

    return await send_to_channel("tickets_channel_id", message)


# ============================================================================
# PURCHASE ORDER NOTIFICATIONS
# ============================================================================

async def notify_po_created(po: Dict) -> bool:
    """Notify when a purchase order is created"""
    enabled = await get_setting("enable_po_notifications")
    if enabled != "true":
        return False
    event_enabled = await get_setting("notify_po_created")
    if event_enabled == "false":
        return False

    message = f"""📦 *Purchase Order Created*
━━━━━━━━━━━━━━━━
*PO Number:* {po['po_number']}
*Supplier:* {po['supplier_name']}
*PO Date:* {po['po_date']}
*Expected Delivery:* {po.get('expected_delivery') or 'Not specified'}
*Total Cost:* ${po['total_cost']:,.2f}

*Items:* {po.get('item_count', '?')} item(s)
*Status:* {po['status'].title()}

*PO ID:* #{po['id']}
"""

    return await send_to_channel("po_channel_id", message)


async def notify_po_status_changed(po: Dict, old_status: str, new_status: str) -> bool:
    """Notify when PO status changes"""
    enabled = await get_setting("enable_po_notifications")
    if enabled != "true":
        return False
    event_enabled = await get_setting("notify_po_status_changed")
    if event_enabled == "false":
        return False

    status_emoji = {
        "pending": "🕐",
        "received": "✅",
        "cancelled": "❌"
    }

    message = f"""🔄 *Purchase Order Status Changed*
━━━━━━━━━━━━━━━━
*PO Number:* {po['po_number']}
*Supplier:* {po['supplier_name']}
*Old Status:* {status_emoji.get(old_status, '')} {old_status.title()}
*New Status:* {status_emoji.get(new_status, '')} {new_status.title()}
*Total Cost:* ${po['total_cost']:,.2f}

*PO ID:* #{po['id']}
"""

    return await send_to_channel("po_channel_id", message)


# ============================================================================
# INVENTORY LOW STOCK NOTIFICATIONS
# ============================================================================

async def notify_low_stock_first_alert(item: Dict) -> bool:
    """First alert when item goes below threshold"""
    enabled = await get_setting("enable_inventory_notifications")
    if enabled != "true":
        return False
    event_enabled = await get_setting("notify_low_stock_first_alert")
    if event_enabled == "false":
        return False

    # Check if already alerted
    existing_alert = await fetch_one(
        """
        SELECT id FROM low_stock_notifications
        WHERE item_master_id = $1 AND is_resolved = FALSE AND notification_type = 'first_alert'
        """,
        item["id"]
    )

    if existing_alert:
        logger.info(f"Item {item['id']} already has active alert, skipping")
        return False

    deficit = Decimal(str(item["reorder_threshold"])) - Decimal(str(item["current_qty"]))

    message = f"""⚠️ *Low Stock Alert*
━━━━━━━━━━━━━━━━
*Item:* {item['item_name']}
*Category:* {item['category']}
*Current Quantity:* {item['current_qty']} {item['unit']}
*Reorder Threshold:* {item['reorder_threshold']} {item['unit']}
*Deficit:* {deficit} {item['unit']}

{'*Supplier:* ' + item['default_supplier_name'] if item.get('default_supplier_name') else ''}

*Action Required:* Restock this item
"""

    success = await send_to_channel("inventory_channel_id", message)

    if success:
        # Record notification
        await execute_query(
            """
            INSERT INTO low_stock_notifications
            (item_master_id, notification_type, current_qty, reorder_threshold)
            VALUES ($1, 'first_alert', $2, $3)
            """,
            item["id"],
            item["current_qty"],
            item["reorder_threshold"]
        )

    return success


async def notify_low_stock_daily_summary() -> bool:
    """Send daily summary of all low stock items"""
    enabled = await get_setting("enable_inventory_notifications")
    if enabled != "true":
        return False
    event_enabled = await get_setting("notify_low_stock_daily_summary")
    if event_enabled == "false":
        return False

    # Get all currently low stock items
    low_stock_items = await fetch_all(
        """
        SELECT
            im.id,
            im.item_name,
            im.category,
            im.unit,
            im.current_qty,
            im.reorder_threshold,
            (im.reorder_threshold - im.current_qty) as deficit,
            s.supplier_name as default_supplier_name
        FROM item_master im
        LEFT JOIN suppliers s ON s.id = im.default_supplier_id
        WHERE im.is_active = TRUE
          AND im.current_qty <= im.reorder_threshold
        ORDER BY (im.reorder_threshold - im.current_qty) DESC
        LIMIT 20
        """
    )

    if not low_stock_items:
        logger.info("No low stock items for daily summary")
        return False

    # Build summary message
    items_list = "\n".join([
        f"• *{item['item_name']}*: {item['current_qty']}/{item['reorder_threshold']} {item['unit']} "
        f"(deficit: {item['deficit']} {item['unit']})"
        for item in low_stock_items[:10]  # Show top 10
    ])

    more_items = len(low_stock_items) - 10
    if more_items > 0:
        items_list += f"\n_...and {more_items} more items_"

    message = f"""📊 *Daily Low Stock Summary*
━━━━━━━━━━━━━━━━
*Date:* {datetime.utcnow().strftime('%Y-%m-%d')}
*Total Low Stock Items:* {len(low_stock_items)}

*Items Needing Restock:*
{items_list}

⚠️ *Action Required:* Review and place purchase orders
"""

    success = await send_to_channel("inventory_channel_id", message)

    if success:
        # Record daily summary notification
        for item in low_stock_items:
            await execute_query(
                """
                INSERT INTO low_stock_notifications
                (item_master_id, notification_type, current_qty, reorder_threshold)
                VALUES ($1, 'daily_summary', $2, $3)
                """,
                item["id"],
                item["current_qty"],
                item["reorder_threshold"]
            )

    return success


# ============================================================================
# USER LINKING (ONE-TIME CODES)
# ============================================================================

def generate_link_code() -> str:
    """Generate a unique 8-character link code"""
    # Format: LINK-XXXX (4 random uppercase alphanumeric)
    chars = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(chars) for _ in range(4))
    return f"LINK-{code}"


async def create_link_code(user_id: str) -> Dict:
    """Create a one-time code for user to link Telegram"""
    # Check if user already has Telegram linked
    user = await fetch_one(
        "SELECT telegram_chat_id FROM user_profiles WHERE id = $1",
        user_id
    )

    if user and user["telegram_chat_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has Telegram account linked"
        )

    # Invalidate any existing unused codes
    await execute_query(
        """
        UPDATE telegram_link_codes
        SET used = TRUE
        WHERE user_id = $1 AND used = FALSE
        """,
        user_id
    )

    # Generate unique code
    attempts = 0
    while attempts < 5:
        code = generate_link_code()

        # Check if code exists
        existing = await fetch_one(
            "SELECT id FROM telegram_link_codes WHERE link_code = $1",
            code
        )

        if not existing:
            break

        attempts += 1

    if attempts >= 5:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate unique code"
        )

    # Create code with 15-minute expiry
    expires_at = datetime.utcnow() + timedelta(minutes=15)

    await execute_query(
        """
        INSERT INTO telegram_link_codes (user_id, link_code, expires_at)
        VALUES ($1, $2, $3)
        """,
        user_id,
        code,
        expires_at
    )

    return {
        "link_code": code,
        "expires_at": expires_at.isoformat(),
        "instructions": f"Open Telegram and send '/start {code}' to the bot"
    }


async def verify_link_code(code: str, telegram_chat_id: int) -> Dict:
    """Verify and use a link code"""
    # Find unused code
    link = await fetch_one(
        """
        SELECT id, user_id, expires_at
        FROM telegram_link_codes
        WHERE link_code = $1 AND used = FALSE
        """,
        code
    )

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or already used code"
        )

    # Check expiry
    if datetime.utcnow() > link["expires_at"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link code has expired"
        )

    # Check if chat_id already linked to another user
    existing_user = await fetch_one(
        "SELECT id, full_name FROM user_profiles WHERE telegram_chat_id = $1",
        telegram_chat_id
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This Telegram account is already linked to user: {existing_user['full_name']}"
        )

    # Mark code as used
    await execute_query(
        """
        UPDATE telegram_link_codes
        SET used = TRUE, used_at = NOW(), telegram_chat_id = $1
        WHERE id = $2
        """,
        telegram_chat_id,
        link["id"]
    )

    # Link Telegram to user profile
    await execute_query(
        "UPDATE user_profiles SET telegram_chat_id = $1 WHERE id = $2",
        telegram_chat_id,
        link["user_id"]
    )

    # Get user info
    user = await fetch_one(
        """
        SELECT up.id, up.full_name, au.email
        FROM user_profiles up
        JOIN auth.users au ON au.id = up.id
        WHERE up.id = $1
        """,
        link["user_id"]
    )

    logger.info(f"User {user['email']} linked Telegram chat {telegram_chat_id}")

    return {
        "success": True,
        "user_id": str(user["id"]),
        "full_name": user["full_name"],
        "email": user["email"]
    }


async def unlink_telegram(user_id: str) -> bool:
    """Unlink user's Telegram account"""
    await execute_query(
        "UPDATE user_profiles SET telegram_chat_id = NULL WHERE id = $1",
        user_id
    )
    return True


async def get_user_link_status(user_id: str) -> Dict:
    """Check if user has Telegram linked"""
    user = await fetch_one(
        "SELECT telegram_chat_id FROM user_profiles WHERE id = $1",
        user_id
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "is_linked": user["telegram_chat_id"] is not None,
        "telegram_chat_id": user["telegram_chat_id"]
    }


# ============================================================================
# TEST NOTIFICATION
# ============================================================================

async def send_test_notification(channel_type: str) -> bool:
    """Send a test notification to verify channel setup"""
    channel_map = {
        "tickets": "tickets_channel_id",
        "po": "po_channel_id",
        "inventory": "inventory_channel_id"
    }

    channel_key = channel_map.get(channel_type)
    if not channel_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid channel type: {channel_type}"
        )

    message = f"""🧪 *Test Notification*
━━━━━━━━━━━━━━━━
*Channel:* {channel_type.upper()}
*Time:* {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
*Status:* Bot is working correctly! ✅

This is a test message to verify your Telegram bot configuration.
"""

    return await send_to_channel(channel_key, message)
