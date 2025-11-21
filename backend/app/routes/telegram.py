"""
Telegram Notification Routes
Version: 1.0.0
Created: 2025-11-20

Changelog:
----------
v1.0.0 (2025-11-20):
  - Initial telegram notification routes
  - Admin endpoints for settings management
  - Bot health check endpoint
  - Test notification endpoint
  - User linking endpoints (create code, verify, unlink, status)
  - Admin-only access control for settings
  - User-level access for personal linking

API Endpoints:
--------------
  GET    /api/v1/telegram/settings          - Get notification settings (Admin)
  PUT    /api/v1/telegram/settings          - Update notification settings (Admin)
  GET    /api/v1/telegram/status            - Get bot health status (Admin)
  POST   /api/v1/telegram/test              - Send test notification (Admin)
  POST   /api/v1/telegram/link/create       - Create link code for user (User)
  GET    /api/v1/telegram/link/status       - Get user's link status (User)
  POST   /api/v1/telegram/link/unlink       - Unlink user's Telegram (User)

Description:
  API routes for managing Telegram bot notifications and user account linking.
"""

import logging
from fastapi import APIRouter, Depends, status, HTTPException

from app.schemas.auth import CurrentUser
from app.schemas.telegram import (
    UpdateSettingsRequest,
    NotificationSettingsResponse,
    BotStatusResponse,
    TestNotificationRequest,
    TestNotificationResponse,
    LinkCodeResponse,
    UserLinkStatusResponse,
    UnlinkTelegramResponse,
)
from app.auth.dependencies import get_current_user, require_admin
from app.services import telegram_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# ADMIN ENDPOINTS - Settings Management
# ============================================================================

@router.get("/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    admin: CurrentUser = Depends(require_admin)
):
    """
    Get current notification settings.

    **Admin only**

    Returns all notification configuration including:
    - Channel IDs for tickets, POs, inventory
    - Enable/disable toggles for each notification type
    - Bot status and health information
    """
    settings = await telegram_service.get_all_settings()
    return settings


@router.put("/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    request: UpdateSettingsRequest,
    admin: CurrentUser = Depends(require_admin)
):
    """
    Update notification settings.

    **Admin only**

    Update any of the following:
    - Channel IDs (provide negative numbers for Telegram channels/groups)
    - Enable/disable toggles for notifications
    - Bot automatically checks health after settings update
    """
    # Convert request to dict, filter out None values
    updates = {}

    if request.tickets_channel_id is not None:
        updates["tickets_channel_id"] = request.tickets_channel_id

    if request.po_channel_id is not None:
        updates["po_channel_id"] = request.po_channel_id

    if request.inventory_channel_id is not None:
        updates["inventory_channel_id"] = request.inventory_channel_id

    if request.enable_ticket_notifications is not None:
        updates["enable_ticket_notifications"] = request.enable_ticket_notifications

    if request.enable_po_notifications is not None:
        updates["enable_po_notifications"] = request.enable_po_notifications

    if request.enable_inventory_notifications is not None:
        updates["enable_inventory_notifications"] = request.enable_inventory_notifications

    if request.enable_personal_notifications is not None:
        updates["enable_personal_notifications"] = request.enable_personal_notifications

    # Granular ticket notification settings
    if request.notify_ticket_created is not None:
        updates["notify_ticket_created"] = request.notify_ticket_created
    if request.notify_ticket_updated is not None:
        updates["notify_ticket_updated"] = request.notify_ticket_updated
    if request.notify_ticket_closed is not None:
        updates["notify_ticket_closed"] = request.notify_ticket_closed
    if request.notify_ticket_comment is not None:
        updates["notify_ticket_comment"] = request.notify_ticket_comment
    if request.notify_ticket_priority_changed is not None:
        updates["notify_ticket_priority_changed"] = request.notify_ticket_priority_changed

    # Granular PO notification settings
    if request.notify_po_created is not None:
        updates["notify_po_created"] = request.notify_po_created
    if request.notify_po_status_changed is not None:
        updates["notify_po_status_changed"] = request.notify_po_status_changed

    # Granular inventory notification settings
    if request.notify_low_stock_first_alert is not None:
        updates["notify_low_stock_first_alert"] = request.notify_low_stock_first_alert
    if request.notify_low_stock_daily_summary is not None:
        updates["notify_low_stock_daily_summary"] = request.notify_low_stock_daily_summary

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No settings provided to update"
        )

    updated_settings = await telegram_service.update_settings_bulk(updates, admin.id)

    logger.info(f"Admin {admin.email} updated notification settings: {list(updates.keys())}")

    return updated_settings


# ============================================================================
# ADMIN ENDPOINTS - Bot Management
# ============================================================================

@router.get("/status", response_model=BotStatusResponse)
async def get_bot_status(
    admin: CurrentUser = Depends(require_admin)
):
    """
    Check Telegram bot health status.

    **Admin only**

    Performs a live health check by connecting to Telegram API.
    Returns bot status, name, username, and any error messages.

    Status values:
    - `active`: Bot is operational
    - `inactive`: Bot not initialized
    - `error`: Bot has errors (check last_error field)
    """
    status_info = await telegram_service.check_bot_health()
    return status_info


@router.post("/test", response_model=TestNotificationResponse, status_code=status.HTTP_200_OK)
async def send_test_notification(
    request: TestNotificationRequest,
    admin: CurrentUser = Depends(require_admin)
):
    """
    Send a test notification to verify channel setup.

    **Admin only**

    Sends a test message to the specified channel (tickets, po, or inventory).
    Use this to verify that:
    - Bot token is valid
    - Channel ID is correct
    - Bot has permission to post in the channel

    **Request Body:**
    ```json
    {
        "channel_type": "tickets"  // or "po" or "inventory"
    }
    ```
    """
    success = await telegram_service.send_test_notification(request.channel_type)

    if success:
        logger.info(f"Admin {admin.email} sent test notification to {request.channel_type} channel")
        return {
            "success": True,
            "message": f"Test notification sent successfully to {request.channel_type} channel",
            "channel_type": request.channel_type
        }
    else:
        logger.error(f"Failed to send test notification to {request.channel_type} channel")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test notification. Check bot token and channel ID."
        )


# ============================================================================
# USER ENDPOINTS - Account Linking
# ============================================================================

@router.post("/link/create", response_model=LinkCodeResponse, status_code=status.HTTP_201_CREATED)
async def create_link_code(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Create a one-time code to link Telegram account.

    **Authenticated users**

    Generates a unique code (e.g., LINK-A8F3) that expires in 15 minutes.
    User should send `/start <code>` to the bot in Telegram to complete linking.

    **Response:**
    ```json
    {
        "link_code": "LINK-A8F3",
        "expires_at": "2025-11-20T10:45:00Z",
        "instructions": "Open Telegram and send '/start LINK-A8F3' to the bot"
    }
    ```
    """
    link_code_info = await telegram_service.create_link_code(current_user.id)

    logger.info(f"User {current_user.email} created Telegram link code")

    return link_code_info


@router.get("/link/status", response_model=UserLinkStatusResponse)
async def get_link_status(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Check if current user has Telegram account linked.

    **Authenticated users**

    Returns whether the user has linked their Telegram account and the chat ID if linked.
    """
    status_info = await telegram_service.get_user_link_status(current_user.id)
    return status_info


@router.post("/link/unlink", response_model=UnlinkTelegramResponse)
async def unlink_telegram(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Unlink Telegram account from current user.

    **Authenticated users**

    Removes the Telegram link. User can re-link later by creating a new code.
    """
    success = await telegram_service.unlink_telegram(current_user.id)

    if success:
        logger.info(f"User {current_user.email} unlinked Telegram account")
        return {
            "success": True,
            "message": "Telegram account unlinked successfully"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlink Telegram account"
        )
