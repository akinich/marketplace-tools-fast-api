"""
Telegram Notification Schemas
Version: 1.1.0
Created: 2025-11-20
Updated: 2025-11-21

Changelog:
----------
v1.1.0 (2025-11-21):
  - Added granular notification toggle fields to UpdateSettingsRequest
  - Tickets: notify_ticket_created, updated, closed, comment, priority_changed
  - POs: notify_po_created, notify_po_status_changed
  - Inventory: notify_low_stock_first_alert, notify_low_stock_daily_summary

v1.0.0 (2025-11-20):
  - Initial telegram notification schemas
  - Request schemas for settings updates, tests, user linking
  - Response schemas for settings, status, link codes
  - Validation rules for channel IDs and codes

Description:
  Pydantic models for Telegram notification API requests and responses.
"""

from typing import Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class UpdateSettingsRequest(BaseModel):
    """Request to update notification settings"""
    tickets_channel_id: Optional[int] = Field(None, description="Telegram channel ID for ticket notifications")
    po_channel_id: Optional[int] = Field(None, description="Telegram channel ID for PO notifications")
    inventory_channel_id: Optional[int] = Field(None, description="Telegram channel ID for inventory notifications")
    enable_ticket_notifications: Optional[bool] = Field(None, description="Enable/disable ticket notifications")
    enable_po_notifications: Optional[bool] = Field(None, description="Enable/disable PO notifications")
    enable_inventory_notifications: Optional[bool] = Field(None, description="Enable/disable inventory notifications")
    enable_personal_notifications: Optional[bool] = Field(None, description="Enable/disable personal DM notifications")

    # Granular ticket notification settings
    notify_ticket_created: Optional[bool] = Field(None, description="Notify when ticket is created")
    notify_ticket_updated: Optional[bool] = Field(None, description="Notify when ticket is updated")
    notify_ticket_closed: Optional[bool] = Field(None, description="Notify when ticket is closed")
    notify_ticket_comment: Optional[bool] = Field(None, description="Notify when comment is added")
    notify_ticket_priority_changed: Optional[bool] = Field(None, description="Notify when priority changes")

    # Granular PO notification settings
    notify_po_created: Optional[bool] = Field(None, description="Notify when PO is created")
    notify_po_status_changed: Optional[bool] = Field(None, description="Notify when PO status changes")

    # Granular inventory notification settings
    notify_low_stock_first_alert: Optional[bool] = Field(None, description="Send first alert when item goes low")
    notify_low_stock_daily_summary: Optional[bool] = Field(None, description="Send daily summary of low stock")

    @validator('tickets_channel_id', 'po_channel_id', 'inventory_channel_id')
    def validate_channel_id(cls, v):
        """Validate channel ID is negative (for channels/groups)"""
        if v is not None and v >= 0:
            raise ValueError("Channel IDs should be negative numbers for Telegram channels/groups")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "tickets_channel_id": -1001234567890,
                "po_channel_id": -1001234567891,
                "inventory_channel_id": -1001234567892,
                "enable_ticket_notifications": True,
                "enable_po_notifications": True,
                "enable_inventory_notifications": True,
                "enable_personal_notifications": False,
                "notify_ticket_created": True,
                "notify_po_created": True,
                "notify_low_stock_first_alert": True
            }
        }


class TestNotificationRequest(BaseModel):
    """Request to send test notification"""
    channel_type: str = Field(..., description="Channel to test: 'tickets', 'po', or 'inventory'")

    @validator('channel_type')
    def validate_channel_type(cls, v):
        """Validate channel type"""
        allowed = ['tickets', 'po', 'inventory']
        if v not in allowed:
            raise ValueError(f"channel_type must be one of {allowed}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "channel_type": "tickets"
            }
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class NotificationSettingsResponse(BaseModel):
    """Response with all notification settings"""
    tickets_channel_id: Optional[int]
    po_channel_id: Optional[int]
    inventory_channel_id: Optional[int]
    enable_ticket_notifications: bool
    enable_po_notifications: bool
    enable_inventory_notifications: bool
    enable_personal_notifications: bool
    bot_status: str
    last_health_check: Optional[str]
    last_error: Optional[str]

    class Config:
        json_schema_extra = {
            "example": {
                "tickets_channel_id": -1001234567890,
                "po_channel_id": -1001234567891,
                "inventory_channel_id": -1001234567892,
                "enable_ticket_notifications": True,
                "enable_po_notifications": True,
                "enable_inventory_notifications": True,
                "enable_personal_notifications": False,
                "bot_status": "active",
                "last_health_check": "2025-11-20T10:30:00Z",
                "last_error": None
            }
        }


class BotStatusResponse(BaseModel):
    """Response with bot health status"""
    status: str = Field(..., description="Bot status: 'active', 'inactive', or 'error'")
    message: str = Field(..., description="Status message")
    bot_name: Optional[str] = Field(None, description="Bot display name")
    bot_username: Optional[str] = Field(None, description="Bot username")
    last_check: str = Field(..., description="ISO timestamp of last check")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "active",
                "message": "Bot @YourBot is operational",
                "bot_name": "Farm Notification Bot",
                "bot_username": "farm_notify_bot",
                "last_check": "2025-11-20T10:30:00Z"
            }
        }


class TestNotificationResponse(BaseModel):
    """Response from test notification"""
    success: bool
    message: str
    channel_type: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Test notification sent successfully",
                "channel_type": "tickets"
            }
        }


# ============================================================================
# USER LINKING SCHEMAS
# ============================================================================

class CreateLinkCodeRequest(BaseModel):
    """Request is empty - uses current user from auth"""
    pass


class LinkCodeResponse(BaseModel):
    """Response with link code for user"""
    link_code: str = Field(..., description="One-time code to use in Telegram")
    expires_at: str = Field(..., description="ISO timestamp when code expires")
    instructions: str = Field(..., description="Instructions for user")

    class Config:
        json_schema_extra = {
            "example": {
                "link_code": "LINK-A8F3",
                "expires_at": "2025-11-20T10:45:00Z",
                "instructions": "Open Telegram and send '/start LINK-A8F3' to the bot"
            }
        }


class VerifyLinkCodeRequest(BaseModel):
    """Request to verify link code (internal use by bot)"""
    code: str = Field(..., description="Link code from user")
    telegram_chat_id: int = Field(..., description="User's Telegram chat ID")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "LINK-A8F3",
                "telegram_chat_id": 123456789
            }
        }


class LinkVerificationResponse(BaseModel):
    """Response after successful link verification"""
    success: bool
    user_id: str
    full_name: str
    email: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "full_name": "John Doe",
                "email": "john@example.com"
            }
        }


class UserLinkStatusResponse(BaseModel):
    """Response with user's Telegram link status"""
    is_linked: bool = Field(..., description="Whether user has Telegram linked")
    telegram_chat_id: Optional[int] = Field(None, description="User's Telegram chat ID if linked")

    class Config:
        json_schema_extra = {
            "example": {
                "is_linked": True,
                "telegram_chat_id": 123456789
            }
        }


class UnlinkTelegramResponse(BaseModel):
    """Response after unlinking Telegram"""
    success: bool
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Telegram account unlinked successfully"
            }
        }


# ============================================================================
# LOW STOCK NOTIFICATION SCHEMAS
# ============================================================================

class LowStockNotificationResponse(BaseModel):
    """Response with low stock notification history"""
    id: int
    item_master_id: int
    item_name: Optional[str]
    notification_type: str
    current_qty: float
    reorder_threshold: float
    notified_at: datetime
    resolved_at: Optional[datetime]
    is_resolved: bool

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "item_master_id": 42,
                "item_name": "Fish Feed Premium",
                "notification_type": "first_alert",
                "current_qty": 5.0,
                "reorder_threshold": 10.0,
                "notified_at": "2025-11-20T10:00:00Z",
                "resolved_at": None,
                "is_resolved": False
            }
        }
