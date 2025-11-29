"""
================================================================================
Marketplace ERP - Units of Measurement Service
================================================================================
Version: 1.0.0
Last Updated: 2025-11-22

Changelog:
----------
v1.0.0 (2025-11-22):
  - Initial implementation of unit of measurements service
  - CRUD operations for units
  - Smart delete: Only allows deletion if unit is not in use
  - Deactivate functionality for units in use
  - Category-based organization

================================================================================
"""

from typing import Optional, List, Dict
from fastapi import HTTPException, status
import logging

from app.database import fetch_one, fetch_all, execute_query

logger = logging.getLogger(__name__)


# ============================================================================
# GET OPERATIONS
# ============================================================================


async def get_units_list(
    category: Optional[str] = None,
    include_inactive: bool = False
) -> List[Dict]:
    """
    Get list of units of measurement.

    Args:
        category: Filter by category (weight, volume, count, length, area)
        include_inactive: Include inactive units (default: False)

    Returns:
        List of unit dictionaries
    """
    where_conditions = []
    params = []
    param_count = 1

    if not include_inactive:
        where_conditions.append("is_active = TRUE")

    if category:
        where_conditions.append(f"category = ${param_count}")
        params.append(category)
        param_count += 1

    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

    query = f"""
        SELECT
            id,
            unit_name,
            abbreviation,
            category,
            is_active,
            created_at,
            updated_at,
            (SELECT COUNT(*) FROM item_master WHERE unit = unit_name) as item_count
        FROM unit_of_measurements
        {where_clause}
        ORDER BY category, unit_name
    """

    units = await fetch_all(query, *params)
    return units


async def get_unit(unit_id: int) -> Dict:
    """Get a single unit by ID"""
    query = """
        SELECT
            id,
            unit_name,
            abbreviation,
            category,
            is_active,
            created_at,
            updated_at,
            (SELECT COUNT(*) FROM item_master WHERE unit = unit_name) as item_count
        FROM unit_of_measurements
        WHERE id = $1
    """
    unit = await fetch_one(query, unit_id)

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unit with ID {unit_id} not found"
        )

    return unit


async def get_unit_categories() -> List[Dict]:
    """Get list of unit categories with counts"""
    query = """
        SELECT
            category,
            COUNT(*) as total_units,
            COUNT(*) FILTER (WHERE is_active = TRUE) as active_units
        FROM unit_of_measurements
        GROUP BY category
        ORDER BY category
    """
    categories = await fetch_all(query)
    return categories


# ============================================================================
# CREATE OPERATIONS
# ============================================================================


async def create_unit(
    unit_name: str,
    abbreviation: Optional[str] = None,
    category: Optional[str] = None
) -> Dict:
    """
    Create a new unit of measurement.

    Args:
        unit_name: Full name of the unit
        abbreviation: Short form (e.g., 'kg' for 'Kilogram')
        category: Category (weight, volume, count, length, area)

    Returns:
        Created unit dictionary
    """
    # Check if unit already exists
    existing = await fetch_one(
        "SELECT id FROM unit_of_measurements WHERE LOWER(unit_name) = LOWER($1)",
        unit_name
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unit '{unit_name}' already exists"
        )

    query = """
        INSERT INTO unit_of_measurements (unit_name, abbreviation, category)
        VALUES ($1, $2, $3)
        RETURNING id, unit_name, abbreviation, category, is_active, created_at, updated_at
    """

    unit = await fetch_one(query, unit_name, abbreviation, category)

    logger.info(f"Created unit: {unit_name}")
    return unit


# ============================================================================
# UPDATE OPERATIONS
# ============================================================================


async def update_unit(
    unit_id: int,
    unit_name: Optional[str] = None,
    abbreviation: Optional[str] = None,
    category: Optional[str] = None
) -> Dict:
    """
    Update a unit of measurement.

    Args:
        unit_id: Unit ID to update
        unit_name: New unit name
        abbreviation: New abbreviation
        category: New category

    Returns:
        Updated unit dictionary
    """
    # Check if unit exists
    existing = await fetch_one(
        "SELECT id, unit_name FROM unit_of_measurements WHERE id = $1",
        unit_id
    )

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unit with ID {unit_id} not found"
        )

    # Check if new name conflicts with another unit
    if unit_name and unit_name != existing["unit_name"]:
        conflict = await fetch_one(
            "SELECT id FROM unit_of_measurements WHERE LOWER(unit_name) = LOWER($1) AND id != $2",
            unit_name,
            unit_id
        )

        if conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unit '{unit_name}' already exists"
            )

    # Build update query dynamically
    updates = []
    params = []
    param_count = 1

    if unit_name is not None:
        updates.append(f"unit_name = ${param_count}")
        params.append(unit_name)
        param_count += 1

    if abbreviation is not None:
        updates.append(f"abbreviation = ${param_count}")
        params.append(abbreviation)
        param_count += 1

    if category is not None:
        updates.append(f"category = ${param_count}")
        params.append(category)
        param_count += 1

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    params.append(unit_id)

    query = f"""
        UPDATE unit_of_measurements
        SET {', '.join(updates)}
        WHERE id = ${param_count}
        RETURNING id, unit_name, abbreviation, category, is_active, created_at, updated_at
    """

    unit = await fetch_one(query, *params)

    # If unit name changed, update all item_master records
    if unit_name and unit_name != existing["unit_name"]:
        update_count = await execute_query(
            "UPDATE item_master SET unit = $1 WHERE unit = $2",
            unit_name,
            existing["unit_name"]
        )
        logger.info(f"Updated {update_count} items with new unit name: {existing['unit_name']} -> {unit_name}")

    logger.info(f"Updated unit ID {unit_id}")
    return unit


# ============================================================================
# DELETE OPERATIONS
# ============================================================================


async def deactivate_unit(unit_id: int) -> Dict:
    """
    Deactivate a unit (soft delete).
    Can always be done, even if unit is in use.

    Args:
        unit_id: Unit ID to deactivate

    Returns:
        Deactivated unit dictionary
    """
    query = """
        UPDATE unit_of_measurements
        SET is_active = FALSE
        WHERE id = $1
        RETURNING id, unit_name, abbreviation, category, is_active, created_at, updated_at
    """

    unit = await fetch_one(query, unit_id)

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unit with ID {unit_id} not found"
        )

    logger.info(f"Deactivated unit: {unit['unit_name']}")
    return unit


async def delete_unit(unit_id: int) -> Dict:
    """
    Permanently delete a unit.
    Only allowed if unit is not in use by any items.

    Args:
        unit_id: Unit ID to delete

    Returns:
        Success message with deleted unit info
    """
    # Get unit info
    unit = await fetch_one(
        """
        SELECT
            id,
            unit_name,
            (SELECT COUNT(*) FROM item_master WHERE unit = unit_name) as item_count
        FROM unit_of_measurements
        WHERE id = $1
        """,
        unit_id
    )

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unit with ID {unit_id} not found"
        )

    # Check if unit is in use
    if unit["item_count"] > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete unit '{unit['unit_name']}'. It is used by {unit['item_count']} item(s). Please deactivate instead."
        )

    # Delete the unit
    await execute_query(
        "DELETE FROM unit_of_measurements WHERE id = $1",
        unit_id
    )

    logger.info(f"Permanently deleted unit: {unit['unit_name']}")

    return {
        "success": True,
        "message": f"Unit '{unit['unit_name']}' deleted successfully",
        "unit_id": unit_id,
        "unit_name": unit["unit_name"]
    }


async def reactivate_unit(unit_id: int) -> Dict:
    """
    Reactivate a deactivated unit.

    Args:
        unit_id: Unit ID to reactivate

    Returns:
        Reactivated unit dictionary
    """
    query = """
        UPDATE unit_of_measurements
        SET is_active = TRUE
        WHERE id = $1
        RETURNING id, unit_name, abbreviation, category, is_active, created_at, updated_at
    """

    unit = await fetch_one(query, unit_id)

    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unit with ID {unit_id} not found"
        )

    logger.info(f"Reactivated unit: {unit['unit_name']}")
    return unit
