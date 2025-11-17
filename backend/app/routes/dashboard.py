"""
================================================================================
Farm Management System - Dashboard Routes
================================================================================
Version: 1.0.0
Last Updated: 2025-11-17

Changelog:
----------
v1.0.0 (2025-11-17):
  - Initial dashboard endpoints
  - Farm-wide KPI summary
  - User accessible modules
  - Quick statistics

================================================================================
"""

from fastapi import APIRouter, Depends

from app.schemas.dashboard import *
from app.schemas.auth import CurrentUser
from app.auth.dependencies import get_current_user
from app.services import admin_service, inventory_service

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
