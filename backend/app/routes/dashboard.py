"""
================================================================================
Marketplace ERP - Dashboard Routes
================================================================================
Version: 1.1.0
Last Updated: 2025-11-22

Changelog:
----------
v1.1.0 (2025-11-22):
  - Added /widgets endpoint for role-based dashboard widgets
  - Dynamic widget rendering based on user's module access
  - Separate widget data for admin, tickets modules

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
from app.auth.dependencies import get_current_user, get_current_user_or_api_key
from app.services import admin_service, tickets_service

router = APIRouter()


# ============================================================================
# DASHBOARD SUMMARY
# ============================================================================


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Dashboard Summary",
    description="Get farm-wide KPIs and metrics (supports JWT and API key auth)",
)
async def get_dashboard_summary(user: dict = Depends(get_current_user_or_api_key)):
    """
    Get main dashboard summary with farm-wide metrics.
    Aggregates data from admin modules.

    Authentication: Accepts both JWT tokens and API keys (X-API-Key header)
    Required scope (for API keys): dashboard:read
    """


    # Get admin metrics
    admin_stats = await admin_service.get_admin_statistics()

    # Combine into dashboard summary
    return DashboardSummaryResponse(

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

        "admin": { ... admin stats ... },
        "tickets": { ... tickets stats ... }
    }
    """
    # Get user's accessible modules
    modules = await admin_service.get_user_accessible_modules(user.id)
    module_keys = {m["module_key"] for m in modules}

    widgets = {}


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
