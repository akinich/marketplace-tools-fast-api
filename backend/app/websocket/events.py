"""
================================================================================
Farm Management System - WebSocket Event Emitters
================================================================================
Version: 1.0.0
Last Updated: 2025-11-22

Description:
  Event emitters for broadcasting real-time updates to connected clients.
  Provides convenience functions for common event types.

Event Types:
  - ticket.created: New ticket created
  - ticket.updated: Ticket updated
  - dashboard.update: Dashboard statistics updated
  - notification: User-specific notification
  - inventory.low_stock: Low stock alert for admins

================================================================================
"""
from typing import Dict, Any
from .connection_manager import manager


async def emit_ticket_created(ticket: Dict[str, Any]):
    """Emit ticket created event"""
    await manager.broadcast({
        "type": "ticket.created",
        "data": ticket
    })


async def emit_ticket_updated(ticket: Dict[str, Any]):
    """Emit ticket updated event"""
    await manager.broadcast({
        "type": "ticket.updated",
        "data": ticket
    })


async def emit_dashboard_update(stats: Dict[str, Any]):
    """Emit dashboard stats update"""
    await manager.broadcast({
        "type": "dashboard.update",
        "data": stats
    })


async def emit_notification(user_id: str, notification: Dict[str, Any]):
    """Emit notification to specific user"""
    await manager.send_to_user(user_id, {
        "type": "notification",
        "data": notification
    })


async def emit_low_stock_alert(items: list):
    """Emit low stock alert to admins"""
    await manager.broadcast_to_admins({
        "type": "inventory.low_stock",
        "data": {"items": items}
    })
