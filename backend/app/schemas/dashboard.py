"""
================================================================================
Marketplace ERP - Dashboard Schemas
================================================================================
Version: 1.1.0
Last Updated: 2025-11-17

Changelog:
----------
v1.1.0 (2025-11-17):
  - Added parent_module_id to ModuleAccess for hierarchical navigation
  - Supports nested module structure in sidebar

v1.0.0 (2025-11-17):
  - Initial dashboard Pydantic models
  - Farm-wide KPI schemas
  - Module summaries

================================================================================
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal


# ============================================================================
# DASHBOARD SUMMARY
# ============================================================================


class DashboardSummaryResponse(BaseModel):
    """Main dashboard summary with farm-wide KPIs"""



    # User metrics
    total_users: int = Field(..., description="Total users in system")
    active_users: int = Field(..., description="Active users")

    # Activity metrics
    recent_logins_24h: int = Field(..., description="Logins in last 24 hours")
    total_activities_7d: int = Field(..., description="Total activities in last 7 days")

    class Config:
        json_schema_extra = {
            "example": {
                "total_users": 25,
                "active_users": 23,
                "recent_logins_24h": 15,
                "total_activities_7d": 1250,
            }
        }


# ============================================================================
# MODULE ACCESS
# ============================================================================


class ModuleAccess(BaseModel):
    """User's accessible modules"""

    module_id: int
    module_key: str
    module_name: str
    icon: str
    display_order: int
    parent_module_id: Optional[int] = Field(None, description="Parent module ID (NULL for top-level modules)")


class UserModulesResponse(BaseModel):
    """User's accessible modules response"""

    modules: List[ModuleAccess]


# ============================================================================
# QUICK STATS
# ============================================================================


class QuickStats(BaseModel):
    """Quick statistics for widgets"""

    label: str
    value: str
    trend: Optional[str] = None  # "up", "down", "neutral"
    icon: Optional[str] = None


class QuickStatsResponse(BaseModel):
    """Quick stats response"""

    stats: List[QuickStats]
