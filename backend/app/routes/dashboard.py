"""
================================================================================
Farm Management System - Dashboard Routes
================================================================================
Version: 1.1.0
Last Updated: 2025-11-22

Changelog:
----------
v1.1.0 (2025-11-22):
  - Added /widgets endpoint for role-based dashboard widgets
  - Dynamic widget rendering based on user's module access
  - Separate widget data for inventory, biofloc, admin, tickets modules

v1.0.0 (2025-11-17):
  - Initial dashboard endpoints
  - Farm-wide KPI summary
  - User accessible modules
  - Quick statistics

================================================================================
"""

from fastapi import APIRouter, Depends
from typing import List, Dict, Any

from app.schemas.dashboard import *
from app.schemas.auth import CurrentUser
from app.auth.dependencies import get_current_user
from app.services import admin_service, inventory_service, biofloc_service, tickets_service

router = APIRouter()


# ============================================================================
# DASHBOARD SUMMARY
# ============================================================================


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Dashboard Summary",
    description="Get farm-wide KPIs and metrics",
)
async def get_dashboard_summary(user: CurrentUser = Depends(get_current_user)):
    """
    Get main dashboard summary with farm-wide metrics.
    Aggregates data from inventory and admin modules.
    """
    # Get inventory metrics
    inventory_stats = await inventory_service.get_inventory_dashboard()

    # Get admin metrics
    admin_stats = await admin_service.get_admin_statistics()

    # Combine into dashboard summary
    return DashboardSummaryResponse(
        total_inventory_items=inventory_stats["total_items"],
        low_stock_items=inventory_stats["low_stock_items"],
        expiring_soon_items=inventory_stats["expiring_soon_items"],
        total_inventory_value=inventory_stats["total_stock_value"],
        pending_pos=inventory_stats["pending_pos"],
        total_users=admin_stats["total_users"],
        active_users=admin_stats["active_users"],
        recent_logins_24h=admin_stats["recent_logins_24h"],
        total_activities_7d=admin_stats["total_activities_7d"],
    )


# ============================================================================
# USER MODULES
# ============================================================================


@router.get(
    "/modules",
    response_model=UserModulesResponse,
    summary="User Accessible Modules",
    description="Get modules accessible to current user",
)
async def get_user_modules(user: CurrentUser = Depends(get_current_user)):
    """
    Get modules accessible to the current authenticated user.
    Used to build sidebar navigation in frontend.
    """
    modules = await admin_service.get_user_accessible_modules(user.id)

    return UserModulesResponse(modules=modules)


# ============================================================================
# DASHBOARD WIDGETS (ROLE-BASED)
# ============================================================================


@router.get(
    "/widgets",
    summary="Dashboard Widgets",
    description="Get dashboard widgets based on user's module access",
)
async def get_dashboard_widgets(user: CurrentUser = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get dashboard widgets based on user's accessible modules.
    Returns only widgets for modules the user has access to.

    Returns a dictionary with module keys as top-level keys:
    {
        "inventory": { ... inventory stats ... },
        "biofloc": { ... biofloc stats ... },
        "admin": { ... admin stats ... },
        "tickets": { ... tickets stats ... }
    }
    """
    # Get user's accessible modules
    modules = await admin_service.get_user_accessible_modules(user.id)
    module_keys = {m["module_key"] for m in modules}

    widgets = {}

    # Inventory widgets
    if "inventory" in module_keys:
        inventory_stats = await inventory_service.get_inventory_dashboard()
        widgets["inventory"] = {
            "total_items": inventory_stats["total_items"],
            "low_stock_items": inventory_stats["low_stock_items"],
            "expiring_soon_items": inventory_stats["expiring_soon_items"],
            "total_stock_value": float(inventory_stats["total_stock_value"]),
            "pending_pos": inventory_stats["pending_pos"],
        }

    # Biofloc widgets
    if "biofloc" in module_keys:
        biofloc_stats = await biofloc_service.get_dashboard_stats()
        # Calculate tanks needing attention (water quality alerts)
        tanks_needing_attention = (
            biofloc_stats.get("low_do_alerts", 0) +
            biofloc_stats.get("high_ammonia_alerts", 0)
        )
        widgets["biofloc"] = {
            "active_tanks": biofloc_stats.get("active_tanks", 0),
            "active_batches": biofloc_stats.get("active_batches", 0),
            "total_stock": biofloc_stats.get("total_fish_count", 0),
            "tanks_needing_attention": tanks_needing_attention,
        }

    # Admin widgets
    if "admin" in module_keys:
        admin_stats = await admin_service.get_admin_statistics()
        widgets["admin"] = {
            "total_users": admin_stats["total_users"],
            "active_users": admin_stats["active_users"],
            "recent_logins_24h": admin_stats["recent_logins_24h"],
            "total_activities_7d": admin_stats["total_activities_7d"],
        }

    # Tickets widgets
    if "tickets" in module_keys:
        tickets_stats = await tickets_service.get_ticket_stats()
        widgets["tickets"] = {
            "open_tickets": tickets_stats.get("open_tickets", 0),
            "in_progress_tickets": tickets_stats.get("in_progress_tickets", 0),
            "resolved_tickets": tickets_stats.get("resolved_tickets", 0),
            "closed_tickets": tickets_stats.get("closed_tickets", 0),
        }

    return widgets
